from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    document_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    trace_id: str
    document_id: str
    document_title: str
    page_number: int
    highlight_color: str | None
    extracted_text: str
    context_snippet: str | None
    score: float


class SearchResponse(BaseModel):
    query: str
    latency_ms: float
    results: list[SearchResultItem]


class SearchHistoryItem(BaseModel):
    id: str
    query_text: str
    result_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchHistoryListResponse(BaseModel):
    items: list[SearchHistoryItem]
