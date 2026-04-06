from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    asset_id: Optional[str] = Field(default=None, description="Limit search to a specific asset")


class SearchHitResponse(BaseModel):
    asset_id: str
    chunk_index: int
    text: str
    score: float


class QueryResponse(BaseModel):
    query: str
    hits: List[SearchHitResponse]
