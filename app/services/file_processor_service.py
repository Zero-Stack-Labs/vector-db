import csv
import inspect
import requests
import tempfile
import os
from typing import List, Dict, Any, Generator
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileProcessorService:
    def __init__(self):
        self.supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.html', '.csv', '.jsonl'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.timeout = 30
    
    def process_file_urls_to_records(self, file_urls: List[str], base_record_id: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not file_urls:
            return []
        
        file_records = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {
                executor.submit(self._download_and_process_file, url): url 
                for url in file_urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content, metadata = future.result()
                    if content:
                        file_key = self._generate_file_key(url)
                        file_records.append({
                            "id": f"{base_record_id}_{file_key}",
                            "data": {
                                "text": content,
                                "source_url": url
                            },
                            "metadata": {
                                **base_metadata,
                                "source": "file_url",
                                "source_url": url,
                                "file_type": metadata["file_type"],
                                "original_record_id": base_record_id
                            }
                        })
                except Exception as e:
                    print(f"Error processing {url}: {e}")
        
        return file_records
    
    def _download_and_process_file(self, url: str) -> tuple[str, Dict[str, Any]]:
        try:
            # Convertir enlaces de Google Drive a enlaces de descarga directa
            url = self._convert_google_drive_url(url)
            
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            if int(response.headers.get('content-length', 0)) > self.max_file_size:
                raise ValueError(f"File too large: {url}")
            
            content_type = response.headers.get('content-type', '').lower()
            file_extension = self._get_file_extension(url, content_type)
            
            # Para Google Drive, intentar detectar el tipo por URL si el content-type no es fiable
            if "drive.google.com" in url and file_extension in ['.txt', '.pdf']:
                # Si vemos que el content-type no es útil, intentar forzar CSV
                # (Google Drive a menudo devuelve application/octet-stream para CSVs)
                if 'octet-stream' in content_type or 'pdf' in content_type:
                    file_extension = '.csv'
            
            if file_extension not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                content = self._extract_content(temp_file_path, file_extension)
                
                # Si content es un generador, lo procesamos inmediatamente para evitar
                # que el archivo temporal se elimine antes de poder leerlo
                if inspect.isgenerator(content):
                    content = list(content)  # Convertir generador a lista
                
                metadata = {
                    "url": url,
                    "file_type": file_extension,
                    "content_type": content_type
                }
                
                return content, metadata
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"Failed to process file {url}: {str(e)}")
    
    def _get_file_extension(self, url: str, content_type: str) -> str:
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        if '.' in path:
            return os.path.splitext(path)[1].lower()
        
        content_type_mapping = {
            'text/plain': '.txt',
            'text/markdown': '.md',
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/html': '.html',
            'text/csv': '.csv',
            'application/jsonl': '.jsonl'
        }
        
        return content_type_mapping.get(content_type, '.txt')
    
    def _extract_content(self, file_path: str, file_extension: str) -> str:
        if file_extension in {'.txt', '.md', '.html', '.jsonl'}:
            return self._read_text_in_chunks(file_path)
        
        elif file_extension == '.pdf':
            # PyPDF2 maneja bien la memoria
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
        
        elif file_extension == '.docx':
            # python-docx también maneja bien la memoria
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        elif file_extension == '.csv':
            # Para CSVs grandes, no leemos todo a memoria
            # Devolvemos un generador que procesa el archivo en chunks
            return self._read_csv_in_chunks(file_path)
            
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
            
    def _read_text_in_chunks(self, file_path: str, chunk_size_lines: int = 500):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk = []
            for i, line in enumerate(f):
                chunk.append(line)
                if (i + 1) % chunk_size_lines == 0:
                    yield "".join(chunk)
                    chunk = []
            if chunk:
                yield "".join(chunk)
            
    def _read_csv_in_chunks(self, file_path: str, chunk_size_rows: int = 50, max_chunk_chars: int = 30000):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=';')
            chunk_rows_data = []
            current_chunk_size = 0
            
            # Columnas clave para el texto del embedding (puedes ajustarlas)
            key_columns_for_embedding = ['Status', 'Name', 'Lastname', 'Startup', 'Email', 'Call']

            for row in reader:
                # 1. Crear el texto para el embedding (corto y conciso)
                embedding_values = [str(row.get(col, '')) for col in key_columns_for_embedding if row.get(col)]
                embedding_text = " | ".join(embedding_values)
                row_size = len(embedding_text)

                # 2. Guardar la fila completa como metadatos
                full_metadata = {k: v for k, v in row.items() if v is not None}
                
                # Si agregar esta fila excede los límites, enviar el chunk actual
                if (len(chunk_rows_data) >= chunk_size_rows or 
                    current_chunk_size + row_size > max_chunk_chars) and chunk_rows_data:
                    
                    yield chunk_rows_data
                    chunk_rows_data = []
                    current_chunk_size = 0
                
                chunk_rows_data.append({
                    "text": embedding_text,
                    "metadata": full_metadata
                })
                current_chunk_size += row_size + 1
            
            if chunk_rows_data:
                yield chunk_rows_data
    
    def _generate_file_key(self, url: str) -> str:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "file"
        name_without_ext = os.path.splitext(filename)[0]
        return f"{name_without_ext}_content"
    
    def _convert_google_drive_url(self, url: str) -> str:
        """
        Convierte enlaces de Google Drive a enlaces de descarga directa
        """
        if "drive.google.com" in url and "/file/d/" in url:
            # Extraer el file_id del enlace
            if "/file/d/" in url:
                file_id = url.split("/file/d/")[1].split("/")[0]
                # Convertir a enlace de descarga directa
                converted_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                return converted_url
        
        return url