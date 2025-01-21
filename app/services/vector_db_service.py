from app.factories.vector_db_provider_factory import VectorDBProviderFactory
from app.models import IndexConfig, UpsertRequest, QueryRequest
from app.services.vector_db_service_interface import VectorDBServiceInterface


class VectorDBService(VectorDBServiceInterface):
    def __init__(self, provider_name: str):
        self.provider = VectorDBProviderFactory.get_provider(provider_name)

    def create_index(self, provider_name: str, config: IndexConfig):
        self.provider.create_index(config)

    def upsert_data(self, provider_name: str, index_name: str, upsert_request: UpsertRequest):
        self.provider.upsert_data(index_name, upsert_request)

    def search(self, provider_name: str, index_name: str, query_request: QueryRequest):
        return self.provider.search(index_name, query_request)
