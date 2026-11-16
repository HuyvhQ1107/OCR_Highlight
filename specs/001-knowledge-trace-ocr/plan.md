# Implementation Plan: Dấu Vết Tri Thức (Knowledge Trace AI OCR)

**Branch**: `001-knowledge-trace-ocr` | **Date**: 2026-11-16 | **Spec**: [spec.md](file:///D:/OCR_Education/OCR_Education/specs/001-knowledge-trace-ocr/spec.md)

**Input**: Feature specification from `/specs/001-knowledge-trace-ocr/spec.md`

## Summary

Xây dựng ứng dụng web **Dấu Vết Tri Thức** hỗ trợ người học tải lên tài liệu PDF hoặc ảnh (`.png`, `.jpg`, `.jpeg`) đã tô màu highlight sẵn, tự động phát hiện vùng highlight và OCR song ngữ Tiếng Việt + Tiếng Anh bằng **Google Gemini API** (kết hợp tiền xử lý PyMuPDF & OpenCV), tìm kiếm truy hồi vị trí kết hợp từ khóa (FTS5) + ngữ nghĩa (Gemini Embeddings), giải thích kiến thức theo ngữ cảnh tài liệu (4 chế độ), gợi ý khái niệm liên quan và sinh flashcard/quiz ôn tập.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5+ / React 18+ (Frontend)

**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, SQLAlchemy 2.0, `google-genai` (Gemini API: `gemini-3.5-flash-lite` cho OCR/LLM & `gemini-embedding-001` cho semantic search, cấu hình qua biến môi trường), `PyMuPDF` (`fitz`), `opencv-python-headless` (tiền xử lý lọc màu highlight, bỏ qua trang không có highlight), `numpy`, `PyJWT`, `passlib[argon2]`, `pydantic-settings`
- Frontend: React, Vite, Tailwind CSS, Lucide Icons, React Router

**Storage**: SQLite (với FTS5 cho full-text search và lưu vector embeddings cục bộ; không cần cài đặt DB ngoài, thiết kế ORM tương thích PostgreSQL) + Local filesystem (`backend/storage/`) cho file PDF/ảnh tải lên

**Testing**: `pytest` + `httpx` (Backend unit, API contract & mocked Gemini integration tests); `vitest` + `tsc` (Frontend type-check & component tests)

**Target Platform**: Web application (trình duyệt desktop/mobile hiện đại) + Python API server (Windows/Linux)

**Project Type**: Web application (`backend/` + `frontend/`)

**Performance Goals**:
- Highlight detection + OCR: ≤ 3 giây/trang (`SC-003`)
- Hybrid Search (Keyword + Semantic): ≤ 1.5 giây ở p95 (`SC-004`)
- AI Contextual Explanation: ≤ 15 giây (`SC-005`)
- Độ chính xác: phát hiện highlight ≥ 85% (`SC-001`), OCR ≥ 90% (`SC-002`)

**Constraints**:
- File upload ≤ 20 MB; tối đa 100 trang PDF thường hoặc 50 trang PDF scan (`FR-002`, `SC-006`)
- Xử lý nền bất đồng bộ với trạng thái `pending` → `processing` → `ready` / `failed` (`FR-003`)
- Cô lập dữ liệu tuyệt đối theo `user_id` (`FR-011`)
- Chỉ xóa ở cấp tài liệu, không sửa/xóa từng vùng highlight trong MVP (`FR-005`)

**Scale/Scope**: MVP phục vụ 10–20 người dùng đồng thời, 6 core entities, 12 API endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `.specify/memory/constitution.md` hiện là template mẫu chưa điền nguyên tắc riêng của dự án; không có ràng buộc xung đột.
- Thiết kế tuân thủ các thực hành chuẩn: tách lớp rõ ràng (`api` → `services` → `models`), có `pytest` kiểm thử tự động cho các luồng nghiệp vụ và validation biên, không rò rỉ dữ liệu giữa các user.
- **Gate Status**: PASS (cả trước Phase 0 và sau Phase 1).

## Project Structure

### Documentation (this feature)

```text
specs/001-knowledge-trace-ocr/
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 technical decisions (Gemini OCR/LLM, Hybrid Search, Async)
├── data-model.md        # Phase 1 entities, relationships, state transitions
├── quickstart.md        # Phase 1 end-to-end validation guide
├── contracts/
│   └── openapi-summary.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                  # FastAPI app entrypoint, CORS, lifespan
│   ├── core/
│   │   ├── config.py            # Settings (GEMINI_API_KEY, JWT, upload limits)
│   │   ├── database.py          # SQLAlchemy engine, session, SQLite FTS5 init
│   │   └── security.py          # Password hashing & JWT auth dependencies
│   ├── models/                  # SQLAlchemy ORM models (User, Document, HighlightTrace, etc.)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/
│   │   ├── gemini_client.py     # Gemini API wrapper (OCR/vision, LLM explain/quiz, embeddings)
│   │   ├── highlight_detector.py# PyMuPDF page render + OpenCV HSV highlight region detection
│   │   ├── document_processor.py# Async background pipeline (pending -> processing -> ready/failed)
│   │   ├── search_service.py    # Hybrid search (SQLite FTS5 + cosine semantic + RRF)
│   │   └── storage_service.py   # Local file storage scoped by user_id
│   └── api/
│       ├── auth.py              # /auth/register, /auth/login, /auth/me
│       ├── documents.py         # /documents/upload, list, detail, delete
│       ├── search.py            # /search, /search/history
│       └── ai_study.py          # /traces/{id}/explain, /traces/{id}/related, /study/generate
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt

frontend/
├── src/
│   ├── api/                     # Typed API client with JWT interceptor
│   ├── context/                 # AuthContext
│   ├── components/              # Navbar, UploadDropzone, HighlightCard, ExplainDrawer, StudyPlayer
│   ├── pages/                   # LoginPage, DashboardPage, DocumentDetailPage, SearchPage, StudyPage
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Structure Decision**: Chọn cấu trúc **Web application (`backend/` + `frontend/`)** khớp với định hướng công nghệ trong `De_tai_Dau_Vet_Tri_Thuc_AI_OCR.docx` (FastAPI/Python + Web application) và hỗ trợ phát triển, kiểm thử độc lập giữa API và giao diện người dùng.

## Complexity Tracking

> Không có vi phạm Constitution Check.
