from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import time
from app.configurations.config import CHUNK_SIZE, CHUNK_OVERLAP


class TextSplitterService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )
    
    def split_text_with_metadata(self, text: str, original_id: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = self.text_splitter.split_text(text)
        timestamp = int(time.time() * 1000)
        
        results = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{original_id}_chunk_{i}_{timestamp}"
            chunk_metadata = {
                **metadata,
                "original_id": original_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "created_at": timestamp
            }
            
            results.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return results
    
    def combine_data_values(self, data: Dict[str, Any]) -> str:
        return " ".join(str(value) for value in data.values()) 