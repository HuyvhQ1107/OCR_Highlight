import json
from fastapi import APIRouter, Depends, HTTPException, status
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.highlight_trace import HighlightTrace
from app.models.knowledge_explanation import KnowledgeExplanation
from app.models.study_material import StudyMaterial, StudyMaterialTrace
from app.models.user import UserAccount
from app.schemas.ai_study import (
    ExplainRequest,
    ExplanationResponse,
    RelatedTraceItem,
    RelatedTracesResponse,
    StudyGenerateRequest,
    StudyMaterialListResponse,
    StudyMaterialResponse,
)
from app.services.gemini_client import GeminiClient
from app.services.search_service import _cosine_similarity

router = APIRouter(tags=["ai-study"])


@router.post("/traces/{trace_id}/explain", response_model=ExplanationResponse)
def explain_trace(
    trace_id: str,
    payload: ExplainRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExplanationResponse:
    trace = db.scalar(
        select(HighlightTrace).where(
            HighlightTrace.id == trace_id, HighlightTrace.user_id == current_user.id
        )
    )
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy vùng highlight."
        )

    if not payload.refresh:
        cached = db.scalar(
            select(KnowledgeExplanation)
            .where(
                KnowledgeExplanation.trace_id == trace.id,
                KnowledgeExplanation.user_id == current_user.id,
                KnowledgeExplanation.mode == payload.mode,
            )
            .order_by(KnowledgeExplanation.created_at.desc())
        )
        if cached is not None:
            return ExplanationResponse.model_validate(cached)

    try:
        content = GeminiClient().explain_highlight(
            extracted_text=trace.extracted_text,
            context_snippet=trace.context_snippet,
            mode=payload.mode,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Không thể tạo giải thích từ Gemini API: {exc}",
        ) from exc

    explanation = KnowledgeExplanation(
        trace_id=trace.id,
        user_id=current_user.id,
        mode=payload.mode,
        content=content,
    )
    db.add(explanation)
    db.commit()
    db.refresh(explanation)
    return ExplanationResponse.model_validate(explanation)


@router.get("/traces/{trace_id}/related", response_model=RelatedTracesResponse)
def get_related_traces(
    trace_id: str,
    limit: int = 5,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RelatedTracesResponse:
    target = db.scalar(
        select(HighlightTrace).where(
            HighlightTrace.id == trace_id, HighlightTrace.user_id == current_user.id
        )
    )
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy vùng highlight."
        )

    if not target.embedding_json:
        return RelatedTracesResponse(trace_id=trace_id, related_traces=[])

    target_vec = np.array(json.loads(target.embedding_json), dtype=np.float32)

    rows = db.execute(
        select(HighlightTrace, Document.title)
        .join(Document, HighlightTrace.document_id == Document.id)
        .where(
            HighlightTrace.user_id == current_user.id,
            HighlightTrace.id != target.id,
        )
    ).all()

    scored: list[RelatedTraceItem] = []
    for tr, doc_title in rows:
        if not tr.embedding_json:
            continue
        try:
            vec = np.array(json.loads(tr.embedding_json), dtype=np.float32)
            sim = _cosine_similarity(target_vec, vec)
            if sim > 0.35:
                scored.append(
                    RelatedTraceItem(
                        trace_id=tr.id,
                        document_id=tr.document_id,
                        document_title=doc_title,
                        page_number=tr.page_number,
                        extracted_text=tr.extracted_text,
                        similarity_score=round(sim, 4),
                    )
                )
        except Exception:
            continue

    scored.sort(key=lambda item: item.similarity_score, reverse=True)
    return RelatedTracesResponse(trace_id=trace_id, related_traces=scored[:limit])


@router.post("/study/generate", response_model=StudyMaterialResponse, status_code=status.HTTP_201_CREATED)
def generate_study(
    payload: StudyGenerateRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyMaterialResponse:
    traces = db.scalars(
        select(HighlightTrace).where(
            HighlightTrace.id.in_(payload.trace_ids),
            HighlightTrace.user_id == current_user.id,
        )
    ).all()
    if not traces:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy vùng highlight hợp lệ để tạo học liệu.",
        )

    trace_dicts = [
        {
            "id": t.id,
            "extracted_text": t.extracted_text,
            "context_snippet": t.context_snippet or "",
        }
        for t in traces
    ]

    try:
        items = GeminiClient().generate_study_material(
            traces=trace_dicts,
            material_type=payload.material_type,
            count=payload.count,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Không thể tạo học liệu ôn tập từ Gemini API: {exc}",
        ) from exc

    title = payload.title or (
        f"Flashcards ({len(items)} thẻ)" if payload.material_type == "flashcard" else f"Quiz ({len(items)} câu)"
    )
    material = StudyMaterial(
        user_id=current_user.id,
        material_type=payload.material_type,
        title=title,
        items_json=json.dumps(items, ensure_ascii=False),
    )
    db.add(material)
    db.flush()

    for t in traces:
        db.add(StudyMaterialTrace(study_material_id=material.id, trace_id=t.id))

    db.commit()
    db.refresh(material)

    return StudyMaterialResponse(
        id=material.id,
        material_type=material.material_type,
        title=material.title,
        items=items,
        created_at=material.created_at,
    )


@router.get("/study", response_model=StudyMaterialListResponse)
def list_study_materials(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyMaterialListResponse:
    materials = db.scalars(
        select(StudyMaterial)
        .where(StudyMaterial.user_id == current_user.id)
        .order_by(StudyMaterial.created_at.desc())
    ).all()

    return StudyMaterialListResponse(
        items=[
            StudyMaterialResponse(
                id=m.id,
                material_type=m.material_type,
                title=m.title,
                items=json.loads(m.items_json),
                created_at=m.created_at,
            )
            for m in materials
        ]
    )
