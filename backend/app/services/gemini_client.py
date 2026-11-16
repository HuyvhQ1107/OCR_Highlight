import json
from typing import Any
from google import genai
from google.genai import types

from app.core.config import get_settings


class GeminiClient:
    """Wrapper around Google Gemini API for OCR, embeddings, explanations, and study generation."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL
        self._client = genai.Client(api_key=self.api_key) if self.api_key else None

    def _ensure_client(self) -> genai.Client:
        if self._client is None:
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình.")
        return self._client

    def extract_highlights_from_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        candidate_colors: list[str] | None = None,
        page_text_hint: str | None = None,
    ) -> list[dict[str, Any]]:
        """Extract highlighted Vietnamese/English text and context from a page image."""
        client = self._ensure_client()
        color_hint = ", ".join(candidate_colors) if candidate_colors else "yellow, green, blue, pink, orange"
        prompt = (
            "Bạn là hệ thống OCR chuyên trích xuất nội dung đã được tô màu highlight trong tài liệu học tập "
            "(hỗ trợ Tiếng Việt có dấu đầy đủ và Tiếng Anh).\n"
            f"Các màu highlight nghi ngờ phát hiện trên trang: {color_hint}.\n"
            "Hãy tìm TẤT CẢ các đoạn văn bản nằm bên trong vùng tô màu highlight trên ảnh.\n"
            "Với mỗi vùng highlight, trả về một phần tử JSON gồm:\n"
            "- highlight_color: tên màu (yellow, green, blue, pink, orange, other)\n"
            "- extracted_text: chính xác văn bản được highlight (giữ nguyên dấu Tiếng Việt / Tiếng Anh)\n"
            "- context_snippet: 1-3 câu văn xung quanh vùng highlight để hiểu ngữ cảnh\n"
            "- language: 'vi', 'en', hoặc 'mixed'\n"
            "Nếu không có chữ nào được highlight rõ ràng, trả về mảng rỗng []."
        )
        if page_text_hint:
            prompt += f"\n\nGợi ý văn bản trích xuất thô từ trang PDF (tham khảo chính tả):\n{page_text_hint[:3000]}"

        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        raw_text = (response.text or "[]").strip()
        try:
            data = json.loads(raw_text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def embed_text(self, text: str) -> list[float]:
        """Generate a semantic embedding vector using gemini-embedding-001."""
        client = self._ensure_client()
        result = client.models.embed_content(
            model=self.embedding_model,
            contents=text,
        )
        if result.embeddings and len(result.embeddings) > 0:
            return list(result.embeddings[0].values)
        return []

    def explain_highlight(
        self,
        extracted_text: str,
        context_snippet: str | None,
        mode: str,
    ) -> str:
        """Generate a contextual explanation in one of 4 modes: basic, deep, example, summary."""
        client = self._ensure_client()
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
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        return (response.text or "").strip()

    def generate_study_material(
        self,
        traces: list[dict[str, str]],
        material_type: str,
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate structured flashcards or quiz questions from selected highlight traces."""
        client = self._ensure_client()
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
            f"{schema_desc}\n\n"
            f"Danh sách kiến thức nguồn:\n{traces_text}"
        )
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
        raw_text = (response.text or "[]").strip()
        try:
            data = json.loads(raw_text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
