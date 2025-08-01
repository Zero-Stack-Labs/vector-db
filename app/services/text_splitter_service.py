from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import time
import re
from app.configurations.config import CHUNK_SIZE, CHUNK_OVERLAP


class TextSplitterService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
        
        self.smart_separators = [
            r'\n\n\n+',  # Multiple line breaks (new sections)
            r'\n\n',     # Double line breaks (paragraphs)
            r'\. ',      # End of sentences
            r'\.\n',     # End of sentences with newline
            r'; ',       # Semicolons
            r', ',       # Commas (last resort)
            r' '         # Spaces (final fallback)
        ]
    
    def split_text_with_metadata(self, text: str, original_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_type = metadata.get("file_type", "")
        
        if file_type == ".pdf":
            cleaned_text = self._clean_pdf_text(text)
            chunks = self._smart_split_text(cleaned_text)
        else:
            chunks = self.text_splitter.split_text(text)
        
        timestamp = int(time.time() * 1000)
        
        results = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{original_id}_chunk_{i}_{timestamp}"
            
            prev_chunk_id = f"{original_id}_chunk_{i-1}_{timestamp}" if i > 0 else None
            next_chunk_id = f"{original_id}_chunk_{i+1}_{timestamp}" if i < len(chunks) - 1 else None
            
            chunk_metadata = {
                **metadata,
                "original_id": original_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "created_at": timestamp,
                "chunk_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
            }
            
            # Solo agregar IDs de chunks vecinos si existen
            if prev_chunk_id:
                chunk_metadata["prev_chunk_id"] = prev_chunk_id
            if next_chunk_id:
                chunk_metadata["next_chunk_id"] = next_chunk_id
            
            results.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return results
    
    def combine_data_values(self, data: Dict[str, Any]) -> str:
        
        text_content = data.get("text", "")
        other_values = [str(value) for key, value in data.items() if key != "text"]
        
        return " ".join([text_content] + other_values).strip()
    
    def _clean_pdf_text(self, text: str) -> str:
        cleaned_text = text
        
        # Eliminar saltos de línea en medio de palabras/oraciones
        cleaned_text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', cleaned_text)
        
        # Eliminar saltos de línea múltiples excesivos
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Unir líneas que terminan sin puntuación con la siguiente
        cleaned_text = re.sub(r'([a-zA-Z0-9,])\n([a-z])', r'\1 \2', cleaned_text)
        
        # Limpiar espacios múltiples
        cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
        
        # Eliminar caracteres extraños comunes en PDFs
        cleaned_text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\n]', '', cleaned_text)
        
        # Limpiar líneas que solo tienen números (posibles números de página)
        cleaned_text = re.sub(r'\n\d+\n', '\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def _smart_split_text(self, text: str) -> List[str]:
        chunks = []
        current_chunk = ""
        target_size = CHUNK_SIZE
        overlap_size = CHUNK_OVERLAP
        
        # Dividir por párrafos primero
        paragraphs = re.split(r'\n\n+', text)
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Si el párrafo es muy largo, dividirlo por oraciones
            if len(paragraph) > target_size:
                sentences = self._split_into_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > target_size and current_chunk:
                        # Agregar overlap del chunk anterior si existe
                        if chunks:
                            overlap_text = self._get_overlap_text(current_chunk, overlap_size)
                            chunks.append(current_chunk)
                            current_chunk = overlap_text + " " + sentence
                        else:
                            chunks.append(current_chunk)
                            current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                # El párrafo completo cabe
                if len(current_chunk) + len(paragraph) > target_size and current_chunk:
                    if chunks:
                        overlap_text = self._get_overlap_text(current_chunk, overlap_size)
                        chunks.append(current_chunk)
                        current_chunk = overlap_text + " " + paragraph
                    else:
                        chunks.append(current_chunk)
                        current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        if len(text) <= overlap_size:
            return text
        
        # Intentar cortar en una oración completa
        overlap_text = text[-overlap_size:]
        sentence_start = overlap_text.find('. ')
        if sentence_start != -1:
            return overlap_text[sentence_start + 2:]
        
        return overlap_text