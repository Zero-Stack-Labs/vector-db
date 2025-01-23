from abc import ABC, abstractmethod
from app.models.models import IndexConfig, UpsertRequest, QueryRequest


class VectorDBServiceInterface(ABC):
    @abstractmethod
    def create_index(self, provider_name: str, config: IndexConfig):
        pass

    @abstractmethod
    def upsert_data(self, provider_name: str, index_name: str, upsert_request: UpsertRequest):
        pass

    @abstractmethod
    def search(self, provider_name: str, index_name: str, query_request: QueryRequest):
        pass
