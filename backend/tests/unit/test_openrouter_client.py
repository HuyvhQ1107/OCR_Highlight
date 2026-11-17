import httpx
import pytest

from app.core.config import get_settings
from app.services.gemini_client import GeminiClient


class _FakeResponse:
    def __init__(self, status_code: int, json_data: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text

    def json(self) -> dict:
        return self._json_data


def test_openrouter_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    get_settings.cache_clear()
    client = GeminiClient()
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        client.embed_text("hello")
    get_settings.cache_clear()


def test_openrouter_ocr_and_embeddings_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemini-3.5-flash-lite")
    monkeypatch.setenv("OPENROUTER_EMBEDDING_MODEL", "google/gemini-embedding-001")
    get_settings.cache_clear()

    recorded_calls: list[tuple[str, dict]] = []

    def fake_post(self, url: str, headers: dict, json: dict):  # noqa: A002
        recorded_calls.append((url, json))
        if url.endswith("/chat/completions"):
            return _FakeResponse(
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": '```json\n[{"highlight_color": "yellow", "extracted_text": "Xin chào", "context_snippet": "Ngữ cảnh", "language": "vi"}]\n```'
                            }
                        }
                    ]
                },
            )
        return _FakeResponse(200, {"data": [{"embedding": [0.1, 0.2, 0.3]}]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = GeminiClient()
    ocr_result = client.extract_highlights_from_image(b"png-bytes", mime_type="image/png")
    assert len(ocr_result) == 1
    assert ocr_result[0]["extracted_text"] == "Xin chào"

    vec = client.embed_text("Xin chào")
    assert vec == [0.1, 0.2, 0.3]

    assert recorded_calls[0][0].endswith("/chat/completions")
    assert recorded_calls[0][1]["model"] == "google/gemini-3.5-flash-lite"
    assert recorded_calls[1][0].endswith("/embeddings")
    assert recorded_calls[1][1]["model"] == "google/gemini-embedding-001"
    get_settings.cache_clear()


def test_openrouter_retries_on_429_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("OPENROUTER_RETRY_BACKOFF_SECONDS", "0.0")
    get_settings.cache_clear()

    attempts = {"count": 0}

    def fake_post(self, url: str, headers: dict, json: dict):  # noqa: A002
        attempts["count"] += 1
        if attempts["count"] == 1:
            return _FakeResponse(429, text="rate limited")
        return _FakeResponse(200, {"choices": [{"message": {"content": "Giải thích thành công"}}]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = GeminiClient()
    result = client.explain_highlight("Định lý", "Ngữ cảnh", "basic")
    assert result == "Giải thích thành công"
    assert attempts["count"] == 2
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("status_code", "expected_msg"),
    [
        (401, "không hợp lệ"),
        (402, "hết hạn mức"),
    ],
)
def test_openrouter_fails_fast_on_auth_or_quota(
    monkeypatch: pytest.MonkeyPatch, status_code: int, expected_msg: str
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    get_settings.cache_clear()

    attempts = {"count": 0}

    def fake_post(self, url: str, headers: dict, json: dict):  # noqa: A002
        attempts["count"] += 1
        return _FakeResponse(status_code, text="error")

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = GeminiClient()
    with pytest.raises(RuntimeError, match=expected_msg):
        client.embed_text("test")
    assert attempts["count"] == 1
    get_settings.cache_clear()
