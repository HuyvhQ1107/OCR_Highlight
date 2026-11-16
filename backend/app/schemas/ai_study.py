from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    mode: Literal["basic", "deep", "example", "summary"] = "basic"
    refresh: bool = False


class ExplanationResponse(BaseModel):
    id: str
    trace_id: str
    mode: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RelatedTraceItem(BaseModel):
    trace_id: str
    document_id: str
    document_title: str
    page_number: int
    extracted_text: str
    similarity_score: float


class RelatedTracesResponse(BaseModel):
    trace_id: str
    related_traces: list[RelatedTraceItem]


class StudyGenerateRequest(BaseModel):
    trace_ids: list[str] = Field(min_length=1, max_length=30)
    material_type: Literal["flashcard", "quiz"] = "flashcard"
    count: int = Field(default=5, ge=1, le=20)
    title: str | None = Field(default=None, max_length=255)


class StudyMaterialResponse(BaseModel):
    id: str
    material_type: str
    title: str
    items: list[dict[str, Any]]
    created_at: datetime


class StudyMaterialListResponse(BaseModel):
    items: list[StudyMaterialResponse]
