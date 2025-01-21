from app.providers.pinecone_db_provider import PineconeDBProvider
from app.providers.vector_db_provider import VectorDBProvider


class VectorDBProviderFactory:
    _providers = {}

    @staticmethod
    def get_provider(provider_name: str) -> VectorDBProvider:
        if provider_name not in VectorDBProviderFactory._providers:
            if provider_name == "pinecone":
                VectorDBProviderFactory._providers[provider_name] = PineconeDBProvider()
            else:
                raise NotImplementedError(f"Proveedor {provider_name} no implementado")
        return VectorDBProviderFactory._providers[provider_name]
