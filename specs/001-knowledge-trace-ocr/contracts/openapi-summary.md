# API Contracts: Dấu Vết Tri Thức

**Base URL**: `/api/v1` | **Auth**: `Authorization: Bearer <JWT>` (tất cả endpoint trừ `/auth/register`, `/auth/login`, `/health`)

## 1. Authentication (`/auth`)
- `POST /auth/register`: `{ email, password, full_name? }` → `201 { user, access_token }`
- `POST /auth/login`: `{ email, password }` → `200 { user, access_token }`
- `GET /auth/me`: → `200 { id, email, full_name, created_at }`

## 2. Documents & Highlights (`/documents`)
- `POST /documents/upload`: `multipart/form-data` (`file`: `.pdf/.png/.jpg/.jpeg`, ≤ 20 MB)
  - Validates format, size ≤ 20 MB, PDF page count (≤ 100 text PDF / ≤ 50 scanned PDF) and encryption.
  - Enqueues background OCR + highlight detection task.
  - → `202 { id, title, status: "pending", total_pages, processed_pages: 0 }`
- `GET /documents`: List current user's documents (paginated, ordered by `created_at DESC`) → `200 { items: [...] }`
- `GET /documents/{document_id}`: Get document detail + processing progress + extracted `highlights[]` → `200 { document, highlights }`
- `DELETE /documents/{document_id}`: Delete document, stored file, and all associated highlights/explanations → `204 No Content`

## 3. Hybrid Search & History (`/search`)
- `POST /search`: `{ query: string, document_id?: UUID, limit?: int (default 10) }`
  - Runs keyword (FTS5) + semantic (Gemini embedding cosine) hybrid search scoped to `current_user.id`.
  - Records entry in `SearchHistory`.
  - → `200 { query, latency_ms, results: [{ trace_id, document_id, document_title, page_number, highlight_color, extracted_text, context_snippet, score }] }`
- `GET /search/history`: List user's search history → `200 { items: [{ id, query_text, result_count, created_at }] }`

## 4. AI Explanation, Related Concepts & Study Materials (`/ai`, `/study`)
- `POST /traces/{trace_id}/explain`: `{ mode: "basic" | "deep" | "example" | "summary" }`
  - Uses Gemini LLM with `extracted_text` + `context_snippet` to generate contextual explanation (returns cached if same `trace_id` + `mode` unless `refresh: true`).
  - → `200 { id, trace_id, mode, content, created_at }`
- `GET /traces/{trace_id}/related`:
  - Finds top-K semantically related `HighlightTrace` items across the user's documents (excluding `trace_id`).
  - → `200 { trace_id, related_traces: [{ trace_id, document_id, document_title, page_number, extracted_text, similarity_score }] }`
- `POST /study/generate`: `{ trace_ids: UUID[], material_type: "flashcard" | "quiz", count?: int (default 5) }`
  - Generates flashcards or quiz questions via Gemini LLM from selected traces and persists `StudyMaterial`.
  - → `201 { id, material_type, title, items, created_at }`
- `GET /study`: List user's generated study materials → `200 { items: [...] }`

## 5. Health Check
- `GET /health`: → `200 { status: "ok" }`
