from openai import OpenAI
from typing import List
from app.configurations.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_EMBEDDING_MODEL
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        return [embedding.embedding for embedding in response.data]
    
    def create_single_embedding(self, text: str) -> List[float]:
        return self.create_embeddings([text])[0] 