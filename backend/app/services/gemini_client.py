import base64
import json
import time
from typing import Any

import httpx

from app.core.config import get_settings

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class GeminiClient:
    """OpenRouter API client for Gemini 3.5 Flash-Lite (OCR/LLM) and Gemini Embedding 001."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.model = settings.OPENROUTER_MODEL
        self.embedding_model = settings.OPENROUTER_EMBEDDING_MODEL
        self.timeout = settings.OPENROUTER_TIMEOUT_SECONDS
        self.max_retries = settings.OPENROUTER_MAX_RETRIES
        self.retry_backoff = settings.OPENROUTER_RETRY_BACKOFF_SECONDS

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY chưa được cấu hình.")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "Dau Vet Tri Thuc",
        }

    def _post_with_retry(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to OpenRouter with exponential backoff on transient failures."""
        self._ensure_configured()
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=self._headers(), json=payload)

                if response.status_code in (401, 403):
                    raise RuntimeError("OPENROUTER_API_KEY không hợp lệ hoặc không có quyền truy cập.")
                if response.status_code == 402:
                    raise RuntimeError("Tài khoản OpenRouter đã hết hạn mức (quota/credit).")

                if response.status_code in _RETRYABLE_STATUS_CODES:
                    last_error = RuntimeError(
                        f"OpenRouter tạm thời quá tải hoặc lỗi máy chủ (HTTP {response.status_code})."
                    )
                    if attempt < self.max_retries:
                        time.sleep(self.retry_backoff * (2**attempt))
                        continue
                    raise last_error

                if response.status_code >= 400:
                    raise RuntimeError(f"OpenRouter trả về lỗi HTTP {response.status_code}: {response.text[:300]}")

                return response.json()
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = RuntimeError(f"Lỗi kết nối tới OpenRouter: {exc}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (2**attempt))
                    continue
                raise last_error from exc

        raise last_error or RuntimeError("Không thể kết nối tới OpenRouter.")

    @staticmethod
    def _extract_message_content(data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        return content.strip() if isinstance(content, str) else ""

    @staticmethod
    def _parse_json_list(raw_text: str) -> list[dict[str, Any]]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        try:
            data = json.loads(cleaned or "[]")
        except json.JSONDecodeError:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return value
        return []

    def extract_highlights_from_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        candidate_colors: list[str] | None = None,
        page_text_hint: str | None = None,
    ) -> list[dict[str, Any]]:
        """Extract highlighted Vietnamese/English text and context from a page image."""
        color_hint = ", ".join(candidate_colors) if candidate_colors else "yellow, green, blue, pink, orange"
        prompt = (
            "Bạn là hệ thống OCR chuyên trích xuất nội dung đã được tô màu highlight trong tài liệu học tập "
            "(hỗ trợ Tiếng Việt có dấu đầy đủ và Tiếng Anh).\n"
            f"Các màu highlight nghi ngờ phát hiện trên trang: {color_hint}.\n"
            "Hãy tìm TẤT CẢ các đoạn văn bản nằm bên trong vùng tô màu highlight trên ảnh.\n"
            "Với mỗi vùng highlight, trả về một phần tử JSON trong mảng JSON gồm:\n"
            "- highlight_color: tên màu (yellow, green, blue, pink, orange, other)\n"
            "- extracted_text: chính xác văn bản được highlight (giữ nguyên dấu Tiếng Việt / Tiếng Anh)\n"
            "- context_snippet: 1-3 câu văn xung quanh vùng highlight để hiểu ngữ cảnh\n"
            "- language: 'vi', 'en', hoặc 'mixed'\n"
            "Chỉ trả về JSON array hợp lệ (không thêm giải thích ngoài JSON). "
            "Nếu không có chữ nào được highlight rõ ràng, trả về []."
        )
        if page_text_hint:
            prompt += f"\n\nGợi ý văn bản trích xuất thô từ trang PDF (tham khảo chính tả):\n{page_text_hint[:3000]}"

        b64_image = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64_image}"
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        data = self._post_with_retry("/chat/completions", payload)
        return self._parse_json_list(self._extract_message_content(data))

    def embed_text(self, text: str) -> list[float]:
        """Generate a semantic embedding vector via OpenRouter."""
        payload = {
            "model": self.embedding_model,
            "input": text,
        }
        data = self._post_with_retry("/embeddings", payload)
        items = data.get("data") or []
        if items and isinstance(items[0], dict) and "embedding" in items[0]:
            return [float(x) for x in items[0]["embedding"]]
        return []

    def explain_highlight(
        self,
        extracted_text: str,
        context_snippet: str | None,
        mode: str,
    ) -> str:
        """Generate a contextual explanation in one of 4 modes: basic, deep, example, summary."""
        mode_instructions = {
            "basic": "Giải thích dễ hiểu, súc tích cho người mới học, giải nghĩa thuật ngữ chính.",
            "deep": "Phân tích chuyên sâu, bản chất lý thuyết, cơ chế và các lưu ý học thuật quan trọng.",
            "example": "Đưa ra 1-2 ví dụ minh họa thực tế, trực quan gắn với nội dung kiến thức.",
            "summary": "Tóm tắt ngắn gọn thành 3-5 gạch đầu dòng cốt lõi dễ nhớ.",
        }
        instruction = mode_instructions.get(mode, mode_instructions["basic"])
        prompt = (
            "Bạn là trợ lý gia sư AI cho hệ thống Dấu Vết Tri Thức.\n"
            f"Yêu cầu: {instruction}\n"
            "Trả lời bằng Markdown rõ ràng, cùng ngôn ngữ với kiến thức (ưu tiên Tiếng Việt nếu nội dung là Tiếng Việt hoặc giải thích song ngữ nếu thuật ngữ Tiếng Anh).\n\n"
            f"Nội dung được đánh dấu:\n\"{extracted_text}\"\n\n"
            f"Ngữ cảnh trong tài liệu:\n\"{context_snippet or 'Không có ngữ cảnh bổ sung'}\""
        )
        payload = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = self._post_with_retry("/chat/completions", payload)
        return self._extract_message_content(data)

    def generate_study_material(
        self,
        traces: list[dict[str, str]],
        material_type: str,
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate structured flashcards or quiz questions from selected highlight traces."""
        traces_text = "\n".join(
            f"- [ID: {t['id']}] {t['extracted_text']} (Ngữ cảnh: {t.get('context_snippet') or ''})"
            for t in traces
        )
        if material_type == "flashcard":
            schema_desc = (
                f"Tạo đúng {count} flashcard dạng JSON array. Mỗi phần tử gồm: "
                '{"front": "câu hỏi/khái niệm mặt trước", "back": "đáp án/giải thích ngắn mặt sau", "source_trace_id": "ID trích dẫn"}.'
            )
        else:
            schema_desc = (
                f"Tạo đúng {count} câu hỏi trắc nghiệm 4 lựa chọn dạng JSON array. Mỗi phần tử gồm: "
                '{"question": "câu hỏi", "options": ["A...", "B...", "C...", "D..."], '
                '"correct_answer": "chuỗi khớp chính xác 1 option", "explanation": "giải thích ngắn", "source_trace_id": "ID trích dẫn"}.'
            )

        prompt = (
            "Bạn là trợ lý tạo học liệu ôn tập chủ động từ các nội dung người học đã highlight.\n"
            f"{schema_desc}\n"
            "Chỉ trả về JSON array hợp lệ (không thêm giải thích ngoài JSON).\n\n"
            f"Danh sách kiến thức nguồn:\n{traces_text}"
        )
        payload = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = self._post_with_retry("/chat/completions", payload)
        return self._parse_json_list(self._extract_message_content(data))
