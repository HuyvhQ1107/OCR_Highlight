# Quickstart & End-to-End Validation Guide

**Feature**: `001-knowledge-trace-ocr`

## Prerequisites
- Python 3.11+
- Node.js 20+
- Google Gemini API Key (`GEMINI_API_KEY`)

## 1. Environment Setup
1. Configure `backend/.env` with `GEMINI_API_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL=sqlite:///./dau_vet_tri_thuc.db`.
2. Install backend dependencies (`pip install -r backend/requirements.txt`) and start FastAPI (`uvicorn app.main:app --reload` inside `backend/`).
3. Install frontend dependencies (`npm install` inside `frontend/`) and start Vite (`npm run dev`).

## 2. End-to-End Validation Scenarios
1. **Auth & Isolation (US1)**: Register User A and User B via `POST /api/v1/auth/register`. Verify User B cannot access User A's documents (`404`/`403`).
2. **Upload & Async Highlight/OCR (US1, US2)**: Upload a sample bilingual (Vietnamese + English) PDF or image with yellow/green highlights via `POST /api/v1/documents/upload`. Poll `GET /api/v1/documents/{id}` until `status == "ready"`. Verify extracted `highlights` contain Vietnamese diacritics and English text with page numbers.
3. **Edge Case Limits**: Upload a >20 MB file or unsupported `.txt` file and verify `400`/`413` validation error.
4. **Hybrid Search & History (US3)**: Query `POST /api/v1/search` with both exact keywords and paraphrased Vietnamese/English meaning. Verify response returns page number + context in ≤ 1.5s and appears in `GET /api/v1/search/history`.
5. **AI Explanation (US4)**: Call `POST /api/v1/traces/{id}/explain` with `mode: "basic"` and `mode: "example"`. Verify contextual response completes in ≤ 15s.
6. **Related Concepts & Study Mode (US5)**: Call `GET /api/v1/traces/{id}/related` and `POST /api/v1/study/generate` (`flashcard` and `quiz`). Verify valid structured cards/questions are returned and persisted.
7. **Delete Document (FR-005)**: Call `DELETE /api/v1/documents/{id}` and verify document + its traces are removed from search results.

## 3. Automated Test Verification
- Backend suite: `pytest` inside `backend/` (unit tests for PDF/image validation, OpenCV highlight detector, hybrid RRF ranker, and mocked Gemini API integration tests).
- Frontend suite: `npm test` / `npm run build` inside `frontend/`.
