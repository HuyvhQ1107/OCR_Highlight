import json
import re
import time
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.highlight_trace import HighlightTrace
from app.schemas.search import SearchResultItem
from app.services.gemini_client import GeminiClient


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _sanitize_fts_query(query: str) -> str:
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        return ""
    return " OR ".join(f'"{tok}"' for tok in tokens[:12])


def hybrid_search_traces(
    db: Session,
    user_id: str,
    query: str,
    document_id: str | None = None,
    limit: int = 10,
    gemini: GeminiClient | None = None,
) -> tuple[list[SearchResultItem], float]:
    """Run FTS5 keyword search + Gemini embedding semantic search fused via RRF."""
    start = time.perf_counter()

    # 1. Load user's candidate traces (with document title)
    stmt = (
        select(HighlightTrace, Document.title)
        .join(Document, HighlightTrace.document_id == Document.id)
        .where(HighlightTrace.user_id == user_id)
    )
    if document_id:
        stmt = stmt.where(HighlightTrace.document_id == document_id)

    rows = db.execute(stmt).all()
    if not rows:
        return [], round((time.perf_counter() - start) * 1000, 2)

    trace_map: dict[str, tuple[HighlightTrace, str]] = {
        trace.id: (trace, doc_title) for trace, doc_title in rows
    }

    # 2. Keyword ranking via SQLite FTS5
    fts_ranks: dict[str, int] = {}
    fts_query = _sanitize_fts_query(query)
    if fts_query and db.bind and db.bind.dialect.name == "sqlite":
        sql = """
            SELECT trace_id, bm25(highlight_traces_fts) AS rank
            FROM highlight_traces_fts
            WHERE highlight_traces_fts MATCH :q
              AND user_id = :user_id
        """
        params: dict[str, str | int] = {"q": fts_query, "user_id": user_id}
        if document_id:
            sql += " AND document_id = :document_id"
            params["document_id"] = document_id
        sql += " ORDER BY rank LIMIT 50"
        try:
            fts_rows = db.execute(text(sql), params).all()
            for rank_idx, (tid, _) in enumerate(fts_rows, start=1):
                if tid in trace_map:
                    fts_ranks[tid] = rank_idx
        except Exception:
            fts_ranks = {}

    # Fallback substring match if FTS returns nothing
    if not fts_ranks:
        q_lower = query.lower()
        matched_ids = [
            tid
            for tid, (tr, _) in trace_map.items()
            if q_lower in tr.extracted_text.lower()
            or (tr.context_snippet and q_lower in tr.context_snippet.lower())
        ]
        for rank_idx, tid in enumerate(matched_ids, start=1):
            fts_ranks[tid] = rank_idx

    # 3. Semantic ranking via Gemini Embeddings
    sem_ranks: dict[str, int] = {}
    client = gemini or GeminiClient()
    query_vec: np.ndarray | None = None
    if client.api_key:
        try:
            emb = client.embed_text(query)
            if emb:
                query_vec = np.array(emb, dtype=np.float32)
        except Exception:
            query_vec = None

    if query_vec is not None:
        scored_sem: list[tuple[str, float]] = []
        for tid, (tr, _) in trace_map.items():
            if not tr.embedding_json:
                continue
            try:
                vec = np.array(json.loads(tr.embedding_json), dtype=np.float32)
                sim = _cosine_similarity(query_vec, vec)
                if sim > 0.25:
                    scored_sem.append((tid, sim))
            except Exception:
                continue
        scored_sem.sort(key=lambda x: x[1], reverse=True)
        for rank_idx, (tid, _) in enumerate(scored_sem[:50], start=1):
            sem_ranks[tid] = rank_idx

    # 4. Reciprocal Rank Fusion (RRF)
    k = 60.0
    candidate_ids = set(fts_ranks.keys()) | set(sem_ranks.keys())
    fused: list[tuple[str, float]] = []
    for tid in candidate_ids:
        score = 0.0
        if tid in fts_ranks:
            score += 1.0 / (k + fts_ranks[tid])
        if tid in sem_ranks:
            score += 1.0 / (k + sem_ranks[tid])
        fused.append((tid, score))

    fused.sort(key=lambda x: x[1], reverse=True)
    results = []
    for tid, score in fused[:limit]:
        tr, doc_title = trace_map[tid]
        results.append(
            SearchResultItem(
                trace_id=tr.id,
                document_id=tr.document_id,
                document_title=doc_title,
                page_number=tr.page_number,
                highlight_color=tr.highlight_color,
                extracted_text=tr.extracted_text,
                context_snippet=tr.context_snippet,
                score=round(score, 5),
            )
        )

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return results, latency_ms
