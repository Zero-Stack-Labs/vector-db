import time

from pinecone import Pinecone, ServerlessSpec
from app.config import PINECONE_API_KEY, MODEL_NAME
from app.models import IndexConfig, DataItem, QueryRequest, UpsertRequest
from app.providers.vector_db_provider import VectorDBProvider


class PineconeDBProvider(VectorDBProvider):
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

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
        embeddings = self.pc.inference.embed(
            model=MODEL_NAME,
            inputs=[
                " ".join(str(value) for value in d.data.values())
                for d in upsert_request.records
            ],
            parameters={"input_type": "passage", "truncate": "END"}
        )

        vectors = []
        for d, embedding in zip(upsert_request.records, embeddings):
            vectors.append({
                "id": d.id,
                "values": embedding['values'],
                "metadata": d.metadata
            })

        index = self.pc.Index(index_name)
        index.upsert(
            vectors=vectors,
            namespace=upsert_request.namespace
        )

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
            embedding = self.pc.inference.embed(
                model=MODEL_NAME,
                inputs=[query_request.query],
                parameters={
                    "input_type": "query"
                }
            )

            query_results = index.query(
                namespace=query_request.namespace,
                vector=embedding[0].values,
                top_k=query_request.top_k,
                include_values=True,
                include_metadata=True,
                filter=query_request.metadata_filter
            )

            for match in query_results['matches']:
                results_to_return.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata'],
                    'vector': match['values']
                })

        return results_to_return
