from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "test.db"
    storage_dir = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-fake-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest-123456")

    from app.core.config import get_settings
    get_settings.cache_clear()

    import app.core.database as db_mod
    import app.services.document_processor as proc_mod
    from app.main import app
    from app.services.gemini_client import GeminiClient

    test_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )

    @event.listens_for(test_engine, "connect")
    def _fk(dbapi_conn, _rec):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.close()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)

    monkeypatch.setattr(db_mod, "engine", test_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(proc_mod, "SessionLocal", TestSessionLocal)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_mod.get_db] = override_get_db

    db_mod.Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS highlight_traces_fts
                USING fts5(
                    trace_id UNINDEXED,
                    user_id UNINDEXED,
                    document_id UNINDEXED,
                    extracted_text,
                    context_snippet,
                    tokenize='unicode61'
                );
                """
            )
        )

    # Mock GeminiClient methods so tests run offline & deterministically
    monkeypatch.setattr(
        GeminiClient,
        "extract_highlights_from_image",
        lambda self, **kwargs: [
            {
                "highlight_color": "yellow",
                "extracted_text": "Định lý Pytago trong tam giác vuông",
                "context_snippet": "Trong hình học phẳng, định lý Pytago liên hệ độ dài ba cạnh.",
                "language": "vi",
            }
        ],
    )
    monkeypatch.setattr(GeminiClient, "embed_text", lambda self, text: [0.8, 0.2, 0.1])
    monkeypatch.setattr(
        GeminiClient,
        "explain_highlight",
        lambda self, extracted_text, context_snippet, mode: f"[{mode}] Giải thích: {extracted_text}",
    )
    monkeypatch.setattr(
        GeminiClient,
        "generate_study_material",
        lambda self, traces, material_type, count=5: (
            [{"front": "Định lý Pytago?", "back": "a^2 + b^2 = c^2", "source_trace_id": traces[0]["id"]}]
            if material_type == "flashcard"
            else [
                {
                    "question": "Định lý Pytago áp dụng cho tam giác nào?",
                    "options": ["Tam giác vuông", "Tam giác đều", "Tam giác cân", "Tam giác tù"],
                    "correct_answer": "Tam giác vuông",
                    "explanation": "Áp dụng cho tam giác có một góc 90 độ.",
                    "source_trace_id": traces[0]["id"],
                }
            ]
        ),
    )

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()
    test_engine.dispose()
    get_settings.cache_clear()


def _sample_highlighted_png() -> bytes:
    img = np.full((400, 600, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (50, 100), (450, 160), (0, 255, 255), -1)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def test_full_mvp_user_flow_and_isolation(client: TestClient):
    # 1. Register User A and User B
    res_a = client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "password123", "full_name": "User A"},
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]

    res_b = client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "password123", "full_name": "User B"},
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Reject invalid file extension
    bad_upload = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert bad_upload.status_code == 400

    # 3. Upload valid highlighted PNG
    upload = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("lesson1.png", _sample_highlighted_png(), "image/png")},
    )
    assert upload.status_code == 202
    doc_id = upload.json()["id"]

    # 4. User B cannot access User A's document (FR-011)
    assert client.get(f"/api/v1/documents/{doc_id}", headers=headers_b).status_code == 404

    # 5. Fetch document detail & verify OCR highlight extracted
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert detail.status_code == 200
    body = detail.json()
    assert body["document"]["status"] == "ready"
    assert len(body["highlights"]) == 1
    trace_id = body["highlights"][0]["id"]
    assert "Pytago" in body["highlights"][0]["extracted_text"]

    # 6. Hybrid search + search history
    search_res = client.post(
        "/api/v1/search",
        headers=headers_a,
        json={"query": "Pytago"},
    )
    assert search_res.status_code == 200
    assert len(search_res.json()["results"]) == 1

    history_res = client.get("/api/v1/search/history", headers=headers_a)
    assert history_res.status_code == 200
    assert len(history_res.json()["items"]) == 1

    # 7. AI explanation + related traces
    exp_res = client.post(
        f"/api/v1/traces/{trace_id}/explain",
        headers=headers_a,
        json={"mode": "basic"},
    )
    assert exp_res.status_code == 200
    assert "[basic]" in exp_res.json()["content"]

    rel_res = client.get(f"/api/v1/traces/{trace_id}/related", headers=headers_a)
    assert rel_res.status_code == 200

    # 8. Generate flashcard & quiz
    fc_res = client.post(
        "/api/v1/study/generate",
        headers=headers_a,
        json={"trace_ids": [trace_id], "material_type": "flashcard", "count": 1},
    )
    assert fc_res.status_code == 201
    assert fc_res.json()["material_type"] == "flashcard"

    # 9. Delete document cascades cleanly
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers_a)
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/documents/{doc_id}", headers=headers_a).status_code == 404
