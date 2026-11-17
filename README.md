# Dấu Vết Tri Thức — AI OCR Hỗ Trợ Học Tập

Hệ thống hỗ trợ người học tải lên tài liệu PDF hoặc ảnh (`.png`, `.jpg`, `.jpeg`) đã tô màu highlight sẵn, tự động phát hiện vùng highlight (OpenCV HSV + PyMuPDF), trích xuất văn bản song ngữ Tiếng Việt + Tiếng Anh thông qua **OpenRouter (`google/gemini-3.5-flash-lite`)**, tìm kiếm kết hợp từ khóa (SQLite FTS5) + ngữ nghĩa (`google/gemini-embedding-001`), giải thích theo ngữ cảnh và tạo Flashcard/Quiz ôn tập.

## Yêu cầu môi trường
- Python 3.11+
- Node.js 20+
- OpenRouter API Key (`OPENROUTER_API_KEY`)

## 1. Chạy Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Mở backend/.env và điền OPENROUTER_API_KEY của bạn
uvicorn app.main:app --reload
```

API chạy tại: `http://127.0.0.1:8000` (Swagger docs: `http://127.0.0.1:8000/docs`).

## 2. Chạy Frontend (React + Vite)

```powershell
cd frontend
npm install
npm run dev
```

Giao diện web chạy tại: `http://localhost:5173`.

## 3. Chạy kiểm thử tự động

```powershell
# Backend unit & integration tests
cd backend
pytest -v

# Frontend TypeScript check & production build
cd frontend
npm run build
```
