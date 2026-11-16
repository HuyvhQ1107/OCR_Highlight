---

description: "Danh sách tác vụ triển khai chi tiết cho hệ thống Dấu Vết Tri Thức"
---

# Tasks: Dấu Vết Tri Thức (Knowledge Trace AI OCR)

**Input**: Design documents from `/specs/001-knowledge-trace-ocr/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi-summary.md`, `quickstart.md`

**Organization**: Tasks are grouped by user story (`US1`–`US5`) to enable independent implementation and incremental MVP delivery.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps task to User Story (`US1`, `US2`, `US3`, `US4`, `US5`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo cấu trúc dự án `backend/` và `frontend/`, cài đặt thư viện và cấu hình môi trường.

- [X] T001 Create project directory structure (`backend/app/`, `backend/tests/`, `backend/storage/`, `frontend/src/`) per `plan.md`
- [X] T002 Create Python dependency manifest (`fastapi`, `uvicorn`, `sqlalchemy`, `google-genai`, `pymupdf`, `opencv-python-headless`, `numpy`, `pyjwt`, `passlib[argon2]`, `pydantic-settings`, `python-multipart`, `pytest`, `httpx`) in `backend/requirements.txt`
- [X] T003 [P] Initialize React + Vite + TypeScript + Tailwind CSS project (`react-router-dom`, `lucide-react`, `vitest`) in `frontend/package.json` and `frontend/vite.config.ts`
- [X] T004 [P] Create environment template (`GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `GEMINI_EMBEDDING_MODEL=gemini-embedding-001`, `JWT_SECRET_KEY`, `DATABASE_URL=sqlite:///./dau_vet_tri_thuc.db`) in `backend/.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Hạ tầng lõi bắt buộc hoàn thành trước khi triển khai các User Story.

- [X] T005 Implement settings management (`GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`, `JWT_SECRET_KEY`, `MAX_FILE_SIZE_BYTES=20971520`, `MAX_PDF_PAGES=100`, `MAX_SCAN_PAGES=50`) in `backend/app/core/config.py`
- [X] T006 Implement SQLAlchemy 2.0 engine, session dependency, and SQLite FTS5 initialization helper in `backend/app/core/database.py`
- [X] T007 [P] Implement Argon2 password hashing and JWT Bearer token creation/verification (`get_current_user` dependency) in `backend/app/core/security.py`
- [X] T008 [P] Implement local file storage service scoped by `user_id/document_id` (save, read, delete directory) in `backend/app/services/storage_service.py`
- [X] T009 [P] Implement base `GeminiClient` wrapper (`google-genai` SDK) for `gemini-3.5-flash-lite` multimodal/text calls and `gemini-embedding-001` vector generation in `backend/app/services/gemini_client.py`
- [X] T010 Setup FastAPI app entrypoint, CORS middleware, exception handlers, and `GET /api/v1/health` in `backend/app/main.py`
- [X] T011 [P] Create typed API client with JWT Authorization interceptor and error handling in `frontend/src/api/client.ts`
- [X] T012 [P] Implement `AuthContext` (login, register, logout, persisted token state) and protected route wrapper in `frontend/src/context/AuthContext.tsx`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Tài khoản cá nhân & Tải lên tài liệu học tập (Priority: P1) 🎯 MVP Core

**Goal**: Người học đăng ký/đăng nhập tài khoản cá nhân, tải lên file PDF/ảnh (≤ 20 MB, ≤ 100 trang PDF thường / ≤ 50 trang scan), xem danh sách và xóa tài liệu với dữ liệu cô lập theo `user_id`.

**Independent Test**: Đăng ký 2 tài khoản A và B, đăng nhập tài khoản A để upload 1 file PDF hợp lệ, kiểm tra tài khoản B không thấy tài liệu của A, và kiểm tra xóa tài liệu hoạt động.

- [X] T013 [P] [US1] Create `UserAccount` ORM model (`id`, `email` unique, `password_hash`, `full_name`, `created_at`) in `backend/app/models/user.py`
- [X] T014 [P] [US1] Create `Document` ORM model (`id`, `user_id`, `title`, `file_type` enum `pdf|png|jpg|jpeg`, `file_size_bytes <= 20MB`, `is_scanned_pdf`, `total_pages`, `processed_pages`, `status` enum `pending|processing|ready|failed`, `error_message`, `storage_path`, `created_at`) in `backend/app/models/document.py`
- [X] T015 [P] [US1] Create Pydantic auth and document schemas in `backend/app/schemas/auth.py` and `backend/app/schemas/document.py`
- [X] T016 [US1] Implement `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `GET /api/v1/auth/me` endpoints in `backend/app/api/auth.py`
- [X] T017 [US1] Implement file validation (extension, ≤ 20 MB, non-encrypted PDF, page count ≤ 100 text / ≤ 50 scanned via PyMuPDF) and `POST /documents/upload`, `GET /documents`, `GET /documents/{id}`, `DELETE /documents/{id}` scoped by `current_user.id` in `backend/app/api/documents.py`
- [X] T018 [P] [US1] Build login/register page UI in `frontend/src/pages/LoginPage.tsx`
- [X] T019 [P] [US1] Build drag-and-drop upload component with client-side size/type validation in `frontend/src/components/UploadDropzone.tsx`
- [X] T020 [US1] Build user dashboard page listing documents, status badges, and delete action in `frontend/src/pages/DashboardPage.tsx`

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Tự động phát hiện vùng highlight & OCR song ngữ (Priority: P1)

**Goal**: Tự động render trang PDF (≥ 150 DPI), lọc vùng tô màu highlight bằng OpenCV HSV (bỏ qua trang không có highlight), OCR song ngữ Tiếng Việt + Tiếng Anh bằng `gemini-3.5-flash-lite` và lưu `HighlightTrace` theo cơ chế chạy nền bất đồng bộ.

**Independent Test**: Upload 1 ảnh hoặc PDF scan có tô màu highlight Tiếng Việt + Tiếng Anh, poll `GET /api/v1/documents/{id}` đến `status == "ready"` và xác nhận danh sách `highlights` trả về đúng văn bản có dấu, số trang và màu sắc.

- [X] T021 [P] [US2] Create `HighlightTrace` ORM model (`id`, `document_id`, `user_id`, `page_number >= 1`, `highlight_color`, `bbox_json`, `extracted_text`, `context_snippet`, `language` enum `vi|en|mixed`, `embedding_json`, `created_at`) in `backend/app/models/highlight_trace.py`
- [X] T022 [US2] Implement `HighlightDetector` service using PyMuPDF (render ≥ 150 DPI + detect scanned vs text PDF) and OpenCV HSV color-masking (`yellow`, `green`, `blue`, `pink`, `orange`) returning bounding boxes and skipping empty pages in `backend/app/services/highlight_detector.py`
- [X] T023 [US2] Extend `GeminiClient` with structured JSON OCR extraction (`extract_highlights_from_image`) for bilingual Vietnamese + English text and surrounding `context_snippet` using `gemini-3.5-flash-lite` in `backend/app/services/gemini_client.py`
- [X] T024 [US2] Implement async background `DocumentProcessor` pipeline (`pending` → `processing` → `ready`/`failed`, updating `processed_pages` per page and persisting `HighlightTrace` rows) in `backend/app/services/document_processor.py`
- [X] T025 [US2] Wire `BackgroundTasks` trigger on `POST /documents/upload` and return `highlights[]` in `GET /documents/{id}` in `backend/app/api/documents.py`
- [X] T026 [P] [US2] Build `HighlightCard` component displaying page number, color badge, OCR text, and context snippet in `frontend/src/components/HighlightCard.tsx`
- [X] T027 [US2] Build `DocumentDetailPage` with 2-second status polling while `pending`/`processing` and highlight list viewer in `frontend/src/pages/DocumentDetailPage.tsx`

**Checkpoint**: User Stories 1 & 2 work end-to-end (upload → async detect & OCR → view highlights).

---

## Phase 5: User Story 3 - Tìm kiếm & Truy hồi vị trí kiến thức trong tài liệu (Priority: P1)

**Goal**: Tìm kiếm kết hợp từ khóa (SQLite FTS5) và ngữ nghĩa (`gemini-embedding-001` cosine + RRF) trên các vùng highlight của người dùng, trả về vị trí trang/ngữ cảnh trong ≤ 1.5s và lưu `SearchHistory`.

**Independent Test**: Tìm kiếm bằng từ khóa chính xác và cụm từ diễn đạt tương đồng (nhớ mang máng), kiểm tra kết quả trả về đúng tài liệu/số trang/ngữ cảnh và xuất hiện trong `GET /api/v1/search/history`.

- [X] T028 [P] [US3] Create `SearchHistory` ORM model (`id`, `user_id`, `query_text`, `result_count`, `matched_trace_ids_json`, `created_at`) in `backend/app/models/search_history.py`
- [X] T029 [US3] Sync `HighlightTrace` inserts/deletes with SQLite FTS5 virtual table (`highlight_traces_fts`) and generate/store `embedding_json` via `gemini-embedding-001` during document processing in `backend/app/services/document_processor.py`
- [X] T030 [US3] Implement `SearchService` combining FTS5 keyword search + `numpy` cosine similarity on `embedding_json` + Reciprocal Rank Fusion (RRF) scoped to `user_id` in `backend/app/services/search_service.py`
- [X] T031 [US3] Create search schemas in `backend/app/schemas/search.py` and implement `POST /api/v1/search` (logging `SearchHistory` and returning `latency_ms` + ranked results) and `GET /api/v1/search/history` in `backend/app/api/search.py`
- [X] T032 [US3] Build `SearchPage` with hybrid search bar, document filter, result cards (page number + context), and recent search history sidebar in `frontend/src/pages/SearchPage.tsx`

**Checkpoint**: Full MVP search & retrieval loop (US1 + US2 + US3) is complete.

---

## Phase 6: User Story 4 - Giải thích kiến thức theo ngữ cảnh tài liệu (Priority: P2)

**Goal**: Cho phép người học yêu cầu `gemini-3.5-flash-lite` giải thích một `HighlightTrace` dựa trên ngữ cảnh tài liệu theo 4 chế độ (`basic`, `deep`, `example`, `summary`) và lưu cache kết quả.

**Independent Test**: Chọn một `HighlightTrace`, gọi `POST /api/v1/traces/{id}/explain` với từng chế độ `basic`, `deep`, `example`, `summary`, xác minh phản hồi bám sát ngữ cảnh trong ≤ 15s và được lưu lại.

- [X] T033 [P] [US4] Create `KnowledgeExplanation` ORM model (`id`, `trace_id`, `user_id`, `mode` enum `basic|deep|example|summary`, `content`, `created_at`) in `backend/app/models/knowledge_explanation.py`
- [X] T034 [US4] Add `explain_highlight` method to `GeminiClient` supporting 4 modes (`basic`, `deep`, `example`, `summary`) using `extracted_text` + `context_snippet` in `backend/app/services/gemini_client.py`
- [X] T035 [US4] Create AI & study schemas in `backend/app/schemas/ai_study.py` and implement `POST /api/v1/traces/{trace_id}/explain` with ownership check and cache lookup (`trace_id` + `mode`, optional `refresh`) in `backend/app/api/ai_study.py`
- [X] T036 [US4] Build `ExplainDrawer` component with 4 mode tabs, Markdown rendering, and a "Khái niệm liên quan" section calling `GET /api/v1/traces/{trace_id}/related` integrated into `DocumentDetailPage` and `SearchPage` in `frontend/src/components/ExplainDrawer.tsx`

**Checkpoint**: User Story 4 is complete and independently testable.

---

## Phase 7: User Story 5 - Liên kết kiến thức & Hỗ trợ ôn tập (Priority: P3)

**Goal**: Gợi ý các vùng highlight/khái niệm liên quan trong kho tài liệu cá nhân và sinh bộ Flashcard hoặc Quiz trắc nghiệm từ các highlight đã chọn.

**Independent Test**: Gọi `GET /api/v1/traces/{id}/related` để nhận danh sách highlight tương đồng và gọi `POST /api/v1/study/generate` (`flashcard` và `quiz`) để tạo và lưu học liệu ôn tập.

- [X] T037 [P] [US5] Create `StudyMaterial` and `StudyMaterialTrace` ORM models (`id`, `user_id`, `material_type` enum `flashcard|quiz`, `title`, `items_json`, `created_at`) in `backend/app/models/study_material.py`
- [X] T038 [US5] Add `generate_study_material` structured JSON generator (`flashcard` / `quiz`) using `gemini-3.5-flash-lite` in `backend/app/services/gemini_client.py`
- [X] T039 [US5] Implement `GET /api/v1/traces/{trace_id}/related` (cosine similarity over user's traces), `POST /api/v1/study/generate`, and `GET /api/v1/study` in `backend/app/api/ai_study.py`
- [X] T040 [P] [US5] Build interactive `StudyPlayer` component (flip cards for flashcards, answer check + explanation for quiz) in `frontend/src/components/StudyPlayer.tsx`
- [X] T041 [US5] Build `StudyPage` for selecting highlights, generating flashcards/quizzes, and reviewing saved study sets in `frontend/src/pages/StudyPage.tsx`

**Checkpoint**: All 5 user stories (P1–P3) are implemented.

---

## Phase 8: Polish, Testing & Cross-Cutting Concerns

**Purpose**: Kiểm thử tự động, xác minh tiêu chí định lượng, điều hướng tổng thể và hoàn thiện tài liệu chạy dự án.

- [X] T042 [P] Wire main navigation bar and routes (`/login`, `/dashboard`, `/documents/:id`, `/search`, `/study`) in `frontend/src/components/Navbar.tsx` and `frontend/src/App.tsx`
- [X] T043 [P] Add unit tests for upload validation (20 MB / page limits), OpenCV HSV highlight detector, and Hybrid RRF ranker in `backend/tests/unit/test_core_pipeline.py`
- [X] T044 [P] Add API integration tests (auth isolation, upload→status, mocked Gemini OCR/explain/study, delete cascade) in `backend/tests/integration/test_api_flows.py`
- [X] T045 Verify frontend TypeScript compilation (`tsc --noEmit`) and production build (`npm run build`) in `frontend/`
- [X] T046 Execute end-to-end validation scenarios from `specs/001-knowledge-trace-ocr/quickstart.md` with a real `GEMINI_API_KEY` (measuring actual OCR latency ≤ 3s/page per `SC-003` and AI explanation latency ≤ 15s per `SC-005`) and update `README.md` with setup instructions

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)**: Bắt buộc hoàn thành trước mọi User Story.
- **US1 (Phase 3)** → **US2 (Phase 4)** → **US3 (Phase 5)**: Chuỗi MVP cốt lõi (upload/auth → detect/OCR → hybrid search).
- **US4 (Phase 6)** & **US5 (Phase 7)**: Phụ thuộc vào `HighlightTrace` từ US2; có thể phát triển song song sau khi xong Phase 4.
- **Polish (Phase 8)**: Thực hiện sau khi hoàn tất các User Story mong muốn.

### Parallel Opportunities
- Trong **Phase 2**: `T007`, `T008`, `T009`, `T011`, `T012` có thể làm song song.
- Trong **Phase 3 (US1)**: `T013`, `T014`, `T015`, `T018`, `T019` có thể làm song song.
- Trong **Phase 4 (US2)**: `T021` và `T026` có thể làm song song với service backend.
- Trong **Phase 8**: `T042`, `T043`, `T044` có thể làm song song.

### Implementation Strategy (MVP First)
1. Hoàn thành **Phase 1 + Phase 2** (nền tảng).
2. Triển khai **Phase 3 (US1) + Phase 4 (US2) + Phase 5 (US3)** để có ngay **MVP hoàn chỉnh** (đăng nhập → upload PDF/ảnh → phát hiện highlight & OCR Gemini → tìm kiếm vị trí & lưu lịch sử).
3. Bổ sung **Phase 6 (US4)** (AI giải thích) và **Phase 7 (US5)** (liên kết kiến thức & flashcard/quiz).
4. Chạy **Phase 8** để kiểm thử và đóng gói.
