from abc import ABC, abstractmethod
from app.models import IndexConfig, UpsertRequest, QueryRequest


class VectorDBServiceInterface(ABC):
    @abstractmethod
    def create_index(self, provider_name: str, config: IndexConfig):
        """
        Método para crear un índice en el proveedor de base de datos vectorial.
        """
        pass

    @abstractmethod
    def upsert_data(self, provider_name: str, index_name: str, upsert_request: UpsertRequest):
        """
        Método para insertar o actualizar datos en el índice de la base de datos vectorial.
        """
        pass

    @abstractmethod
    def search(self, provider_name: str, index_name: str, query_request: QueryRequest):
        """
        Método para realizar una búsqueda en el índice de la base de datos vectorial.
        """
        pass
