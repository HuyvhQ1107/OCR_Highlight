import json
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.search_history import SearchHistory
from app.models.user import UserAccount
from app.schemas.search import (
    SearchHistoryItem,
    SearchHistoryListResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.search_service import hybrid_search_traces

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_highlights(
    payload: SearchRequest,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    results, latency_ms = hybrid_search_traces(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        document_id=payload.document_id,
        limit=payload.limit,
    )

    history = SearchHistory(
        user_id=current_user.id,
        query_text=payload.query,
        result_count=len(results),
        matched_trace_ids_json=json.dumps([r.trace_id for r in results]),
    )
    db.add(history)
    db.commit()

    return SearchResponse(query=payload.query, latency_ms=latency_ms, results=results)


@router.get("/history", response_model=SearchHistoryListResponse)
def get_search_history(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchHistoryListResponse:
    items = db.scalars(
        select(SearchHistory)
        .where(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.created_at.desc())
        .limit(50)
    ).all()
    return SearchHistoryListResponse(
        items=[SearchHistoryItem.model_validate(item) for item in items]
    )
