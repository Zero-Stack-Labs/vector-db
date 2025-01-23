from abc import ABC, abstractmethod
from app.models.models import QueryRequest, UpsertRequest


class VectorDBProvider(ABC):
    @abstractmethod
    def create_index(self, config):
        pass

    @abstractmethod
    def upsert_data(self, index_name: str, upsert_request: UpsertRequest):
        pass

    @abstractmethod
    def search(self, index_name: str, query_request: QueryRequest):
        pass
