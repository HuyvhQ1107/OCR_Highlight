from datetime import datetime
from pydantic import BaseModel


class HighlightTraceResponse(BaseModel):
    id: str
    document_id: str
    page_number: int
    highlight_color: str | None
    bbox_json: str | None
    extracted_text: str
    context_snippet: str | None
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    title: str
    file_type: str
    file_size_bytes: int
    is_scanned_pdf: bool
    total_pages: int
    processed_pages: int
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]


class DocumentDetailResponse(BaseModel):
    document: DocumentResponse
    highlights: list[HighlightTraceResponse]
