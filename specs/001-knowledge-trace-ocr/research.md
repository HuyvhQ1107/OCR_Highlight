# Research & Technical Decisions: Dấu Vết Tri Thức

**Feature**: `001-knowledge-trace-ocr` | **Date**: 2026-11-16

## 1. Gemini API for Bilingual OCR & Highlight Extraction

- **Decision**: Sử dụng **Google Gemini API** (`google-genai` Python SDK) với model **`gemini-3.5-flash-lite`** (cấu hình qua `GEMINI_MODEL`) cho cả OCR và LLM trả lời, **`gemini-embedding-001`** (cấu hình qua `GEMINI_EMBEDDING_MODEL`) cho tìm kiếm ngữ nghĩa, kết hợp tiền xử lý ảnh bằng **OpenCV** (`opencv-python-headless`) và **PyMuPDF** (`fitz`) để lọc và bỏ qua các trang không có màu highlight trước khi gọi API.
- **Rationale**:
  - Người dùng chỉ định dùng `gemini-3.5-flash-lite` cho OCR/LLM và `gemini-embedding` cho tìm kiếm ngữ nghĩa.
  - Model dòng Flash-Lite tối ưu độ trễ và chi phí, rất phù hợp để đạt mục tiêu `SC-003` (≤ 3s/trang) và `SC-005` (≤ 15s giải thích), đồng thời hỗ trợ đầu ra JSON có cấu trúc (`response_schema`) cho tiếng Việt có dấu và tiếng Anh.
  - Kết hợp PyMuPDF (render trang PDF ra ảnh ≥ 150 DPI + đọc PDF highlight annotations nếu có) và OpenCV (lọc màu highlight theo không gian màu HSV: vàng, xanh lá, xanh dương, hồng, cam để cắt/đánh dấu vùng nghi ngờ) giúp tăng độ chính xác phát hiện vùng highlight (≥ 85%), giảm nhiễu nền và giữ tốc độ xử lý ≤ 3 giây/trang.
- **Alternatives considered**:
  - *Tesseract / PaddleOCR thuần*: Cần cấu hình pipeline riêng cho phát hiện vùng màu + ghép dòng Tiếng Việt; độ chính xác kém hơn trên ảnh chụp nghiêng/nền phức tạp.
  - *Chỉ gửi toàn bộ trang ảnh thô cho Gemini mà không tiền xử lý*: Dễ bỏ sót hoặc nhầm ranh giới vùng highlight khi trang có nhiều chữ nhỏ; kết hợp OpenCV/PyMuPDF giúp định vị bounding box chuẩn hơn.

## 2. Hybrid Search (Keyword + Semantic Search)

- **Decision**: Sử dụng **Hybrid Search** kết hợp **Full-Text Search (SQLite FTS5)** cho khớp từ khóa chính xác và **Semantic Vector Search** sử dụng **Gemini Embeddings** (`gemini-embedding-001` / `text-embedding-004`) với tính toán độ tương đồng cosine lưu cục bộ (SQLite + `numpy` hoặc `sqlite-vec`), hợp nhất điểm bằng Reciprocal Rank Fusion (RRF).
- **Rationale**:
  - Đáp ứng `FR-006` (tìm kiếm kết hợp từ khóa và ngữ nghĩa trên nội dung highlight) và `SC-004` (≤ 1.5s cho 95% truy vấn).
  - Với quy mô MVP (≤ 100 trang/tài liệu, 10–20 người dùng đồng thời), lưu vector embedding theo từng `user_id` trong SQLite + tính cosine bằng `numpy` cho độ trễ < 50ms mà không cần vận hành thêm server Vector DB rời (như Qdrant/Milvus). Kiến trúc được bọc sau `SearchRepository` để dễ nâng cấp lên `pgvector` khi mở rộng.
- **Alternatives considered**:
  - *ChromaDB / Qdrant server*: Tốt cho hàng triệu vector nhưng tăng độ phức tạp triển khai MVP.

## 3. Asynchronous Document Processing Pipeline

- **Decision**: Sử dụng cơ chế xử lý nền bất đồng bộ (**FastAPI `BackgroundTasks`** hoặc worker pool nội bộ) với vòng đời trạng thái `pending` → `processing` → `ready` / `failed`, lưu tiến độ `processed_pages / total_pages`.
- **Rationale**:
  - Đáp ứng `FR-003` (người học không bị treo màn hình khi upload PDF tới 50–100 trang) và giữ API upload phản hồi tức thì (< 500ms).
  - Frontend polling nhẹ `GET /documents/{id}` mỗi 2 giây khi trạng thái là `pending` hoặc `processing`.
- **Alternatives considered**:
  - *Celery + Redis*: Phù hợp quy mô lớn nhưng quá nặng cho MVP; có thể nâng cấp sau nếu tách worker riêng.

## 4. Database, File Storage & Authentication

- **Decision**:
  - **Database**: **SQLite** (qua SQLAlchemy 2.0) cho MVP để chạy không cần cài đặt thêm DB server, thiết kế schema tương thích **PostgreSQL** khi deploy production.
  - **File Storage**: Lưu file gốc và ảnh render trang trên local disk (`backend/storage/{user_id}/{document_id}/`) với giao diện `StorageService` có thể chuyển sang S3/GCS.
  - **Authentication**: Email + Password, băm mật khẩu bằng **Argon2/bcrypt** (`passlib`), xác thực phiên bằng **JWT Bearer Token**.
- **Rationale**: Tối giản thiết lập môi trường cho MVP, đảm bảo cô lập dữ liệu tuyệt đối theo `user_id` (`FR-011`).

## 5. Frontend Web Application

- **Decision**: **React + Vite + TypeScript + Tailwind CSS**.
- **Rationale**: Nhẹ, build nhanh, hệ sinh thái phong phú cho PDF/image preview, highlight overlay, hộp thoại giải thích AI (hỗ trợ streaming/markdown) và giao diện flashcard/quiz.
