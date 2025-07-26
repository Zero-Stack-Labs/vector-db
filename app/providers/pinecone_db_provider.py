import time

from pinecone import Pinecone, ServerlessSpec
from app.configurations.config import PINECONE_API_KEY, CHUNK_THRESHOLD
from app.models.models import IndexConfig, QueryRequest, UpsertRequest
from app.providers.vector_db_provider import VectorDBProvider
from app.services.text_splitter_service import TextSplitterService
from app.services.embedding_service import EmbeddingService


class PineconeDBProvider(VectorDBProvider):
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.text_splitter = TextSplitterService()
        self.embedding_service = EmbeddingService()

    def create_index(self, config: IndexConfig):
        self.pc.create_index(
            name=config.index_name,
            dimension=config.dimension,
            metric=config.metric,
            spec=ServerlessSpec(
                cloud=config.cloud,
                region=config.region
            )
        )

        while not self.pc.describe_index(config.index_name).status['ready']:
            time.sleep(1)

    def upsert_data(self, index_name: str, upsert_request: UpsertRequest):
        index = self.pc.Index(index_name)
        
        self._delete_existing_document_chunks(index, upsert_request)
        
        chunks = self._process_records_to_chunks(upsert_request.records)
        embeddings = self._create_embeddings_for_chunks(chunks)
        vectors = self._build_vectors_from_chunks_and_embeddings(chunks, embeddings)
        
        index.upsert(vectors=vectors, namespace=upsert_request.namespace)
    
    def _process_records_to_chunks(self, records):
        all_chunks = []
        timestamp = int(time.time() * 1000)
        
        for record in records:
            combined_text = self.text_splitter.combine_data_values(record.data)
            
            if len(combined_text) > CHUNK_THRESHOLD:
                chunks = self.text_splitter.split_text_with_metadata(
                    text=combined_text,
                    original_id=record.id,
                    metadata=record.metadata
                )
                all_chunks.extend(chunks)
            else:
                enhanced_metadata = {
                    **record.metadata,
                    "original_id": record.id,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "chunk_size": len(combined_text),
                    "created_at": timestamp
                }
                all_chunks.append({
                    "id": record.id,
                    "text": combined_text,
                    "metadata": enhanced_metadata
                })
        
        return all_chunks
    
    def _create_embeddings_for_chunks(self, chunks):
        texts = [chunk["text"] for chunk in chunks]
        return self.embedding_service.create_embeddings(texts)
    
    def _build_vectors_from_chunks_and_embeddings(self, chunks, embeddings):
        return [
            {
                "id": chunk["id"],
                "values": embedding,
                "metadata": chunk["metadata"]
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]
    
    def _delete_existing_document_chunks(self, index, upsert_request):
        original_ids = [record.id for record in upsert_request.records]
        
        if not original_ids:
            return
            
        try:
            index.delete(
                filter={"original_id": {"$in": original_ids}},
                namespace=upsert_request.namespace
            )
        except Exception:
            pass

    def search(self, index_name: str, query_request: QueryRequest):
        index = self.pc.Index(index_name)

        results_to_return = []
        if query_request.ids:
            query_results = index.fetch(query_request.ids, query_request.namespace)
            for vector_id, vector_data in query_results['vectors'].items():
                results_to_return.append({
                    'id': vector_data['id'],
                    'score': None,
                    'metadata': vector_data['metadata'],
                    'vector': vector_data['values']
                })
        else:
            query_embedding = self.embedding_service.create_single_embedding(query_request.query)

            query_results = index.query(
                namespace=query_request.namespace,
                vector=query_embedding,
                top_k=query_request.top_k,
                include_values=True,
                include_metadata=True,
                filter=query_request.metadata_filter
            )

            for match in query_results['matches']:
                results_to_return.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {}),
                    'vector': match['values']
                })

        return results_to_return
    
    def ensure_namespace_exists(self, index_name: str, namespace: str):
        try:
            index = self.pc.Index(index_name)
            
            index.query(
                namespace=namespace,
                vector=[0.0] * 1536,
                top_k=1,
                include_metadata=False
            )
            
            return {"message": f"Namespace '{namespace}' está listo en índice '{index_name}'", "exists": True}
        except Exception as e:
            if "dimension" in str(e).lower():
                return {"message": f"Namespace '{namespace}' se creará automáticamente en el primer upsert", "exists": False}
            else:
                raise Exception(f"Error con namespace: {str(e)}")
