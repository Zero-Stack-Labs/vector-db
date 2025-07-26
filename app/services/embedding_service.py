from openai import OpenAI
from typing import List
import time
from app.configurations.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_EMBEDDING_MODEL
        self.max_batch_size = 2048
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        if len(texts) <= self.max_batch_size:
            return self._create_embeddings_batch(texts)
        
        all_embeddings = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch_texts = texts[i:i + self.max_batch_size]
            
            try:
                batch_embeddings = self._create_embeddings_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                if "rate limit" in str(e).lower():
                    time.sleep(60)
                    batch_embeddings = self._create_embeddings_batch(batch_texts)
                    all_embeddings.extend(batch_embeddings)
                else:
                    raise e
        
        return all_embeddings
    
    def _create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        return [embedding.embedding for embedding in response.data]
    
    def create_single_embedding(self, text: str) -> List[float]:
        return self.create_embeddings([text])[0] 