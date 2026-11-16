import json
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.highlight_trace import HighlightTrace
from app.services.gemini_client import GeminiClient
from app.services.highlight_detector import (
    PageRenderResult,
    detect_highlight_regions_in_image,
    render_pdf_pages_with_highlights,
)


def sync_trace_to_fts(db: Session, trace: HighlightTrace) -> None:
    """Insert a HighlightTrace into the SQLite FTS5 virtual table."""
    if db.bind and db.bind.dialect.name != "sqlite":
        return
    db.execute(
        text(
            """
            INSERT INTO highlight_traces_fts (trace_id, user_id, document_id, extracted_text, context_snippet)
            VALUES (:trace_id, :user_id, :document_id, :extracted_text, :context_snippet)
            """
        ),
        {
            "trace_id": trace.id,
            "user_id": trace.user_id,
            "document_id": trace.document_id,
            "extracted_text": trace.extracted_text,
            "context_snippet": trace.context_snippet or "",
        },
    )


def delete_document_from_fts(db: Session, document_id: str) -> None:
    """Remove all FTS5 rows belonging to a deleted document."""
    if db.bind and db.bind.dialect.name != "sqlite":
        return
    db.execute(
        text("DELETE FROM highlight_traces_fts WHERE document_id = :document_id"),
        {"document_id": document_id},
    )


def process_document_background(document_id: str) -> None:
    """Background pipeline: render/detect highlights -> Gemini OCR -> Gemini Embedding -> FTS5."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return

        doc.status = "processing"
        doc.processed_pages = 0
        db.commit()

        file_path = Path(doc.storage_path)
        gemini = GeminiClient()

        if doc.file_type == "pdf":
            pages = render_pdf_pages_with_highlights(file_path, dpi=150)
        else:
            img_bytes = file_path.read_bytes()
            regions = detect_highlight_regions_in_image(img_bytes)
            pages = [
                PageRenderResult(
                    page_number=1,
                    image_bytes=img_bytes,
                    page_text_hint="",
                    detected_regions=regions,
                )
            ]

        mime_map = {
            "pdf": "image/png",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
        }
        mime_type = mime_map.get(doc.file_type, "image/png")

        for page in pages:
            # Skip pages with zero detected highlight colors to save latency and API quota
            if page.detected_regions:
                extracted_items = gemini.extract_highlights_from_image(
                    image_bytes=page.image_bytes,
                    mime_type=mime_type,
                    candidate_colors=page.candidate_colors,
                    page_text_hint=page.page_text_hint or None,
                )
                for idx, item in enumerate(extracted_items):
                    extracted_text = str(item.get("extracted_text") or "").strip()
                    if not extracted_text:
                        continue
                    context_snippet = str(item.get("context_snippet") or "").strip() or None
                    color = str(item.get("highlight_color") or "yellow").lower()
                    lang = str(item.get("language") or "mixed").lower()
                    if lang not in ("vi", "en", "mixed"):
                        lang = "mixed"

                    bbox = (
                        page.detected_regions[idx].bbox
                        if idx < len(page.detected_regions)
                        else page.detected_regions[0].bbox
                    )

                    embed_input = f"{extracted_text}\n{context_snippet or ''}".strip()
                    try:
                        embedding = gemini.embed_text(embed_input)
                    except Exception:
                        embedding = []

                    trace = HighlightTrace(
                        document_id=doc.id,
                        user_id=doc.user_id,
                        page_number=page.page_number,
                        highlight_color=color,
                        bbox_json=json.dumps(bbox),
                        extracted_text=extracted_text,
                        context_snippet=context_snippet,
                        language=lang,
                        embedding_json=json.dumps(embedding) if embedding else None,
                    )
                    db.add(trace)
                    db.flush()
                    sync_trace_to_fts(db, trace)

            doc.processed_pages = page.page_number
            db.commit()

        doc.status = "ready"
        db.commit()
    except Exception as exc:
        db.rollback()
        doc = db.get(Document, document_id)
        if doc is not None:
            doc.status = "failed"
            doc.error_message = str(exc)[:500]
            db.commit()
    finally:
        db.close()
