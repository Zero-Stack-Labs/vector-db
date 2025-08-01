from openai import OpenAI
from typing import List
import time
from app.configurations.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_EMBEDDING_MODEL
        self.max_texts_per_batch = 2048
        self.max_chars_per_batch = 750000

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        all_embeddings = []
        current_batch = []
        current_char_count = 0

        for text in texts:
            char_count = len(text)
            
            if (current_char_count + char_count > self.max_chars_per_batch or 
                len(current_batch) >= self.max_texts_per_batch) and current_batch:
                
                batch_embeddings = self._get_embeddings_with_retry(current_batch)
                all_embeddings.extend(batch_embeddings)
                
                current_batch = [text]
                current_char_count = char_count
            else:
                current_batch.append(text)
                current_char_count += char_count

        if current_batch:
            batch_embeddings = self._get_embeddings_with_retry(current_batch)
            all_embeddings.extend(batch_embeddings)
            
        return all_embeddings

    def _get_embeddings_with_retry(self, texts: List[str]) -> List[List[float]]:
        try:
            return self._create_embeddings_batch(texts)
        except Exception as e:
            if "rate limit" in str(e).lower():
                time.sleep(60)
                return self._create_embeddings_batch(texts)
            else:
                raise e
    
    def _create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [embedding.embedding for embedding in response.data]
    
    def create_single_embedding(self, text: str) -> List[float]:
        return self.create_embeddings([text])[0] 