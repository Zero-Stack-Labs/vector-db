from typing import List, Optional
from pydantic import BaseModel


class IndexConfig(BaseModel):
    index_name: str
    dimension: int
    metric: str
    cloud: str = "aws"
    region: str = "us-east-1"


class DataItem(BaseModel):
    id: str
    data: dict
    metadata: dict = {}
    file_urls: Optional[List[str]] = []


class UpsertRequest(BaseModel):
    namespace: str
    records: List[DataItem]


class QueryRequest(BaseModel):
    query: str = ""
    ids: Optional[List[str]] = None
    top_k: int = 3
    namespace: str
    metadata_filter: dict = {}
