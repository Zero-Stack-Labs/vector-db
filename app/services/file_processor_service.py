import requests
import tempfile
import os
from typing import List, Dict, Any
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileProcessorService:
    def __init__(self):
        self.supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.html'}
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
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            if int(response.headers.get('content-length', 0)) > self.max_file_size:
                raise ValueError(f"File too large: {url}")
            
            content_type = response.headers.get('content-type', '').lower()
            file_extension = self._get_file_extension(url, content_type)
            
            if file_extension not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                content = self._extract_content(temp_file_path, file_extension)
                
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
            'text/html': '.html'
        }
        
        return content_type_mapping.get(content_type, '.txt')
    
    def _extract_content(self, file_path: str, file_extension: str) -> str:
        if file_extension in {'.txt', '.md', '.html'}:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif file_extension == '.pdf':
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
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")
    
    def _generate_file_key(self, url: str) -> str:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "file"
        name_without_ext = os.path.splitext(filename)[0]
        return f"{name_without_ext}_content"