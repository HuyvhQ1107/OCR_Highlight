# Data Model: Dấu Vết Tri Thức

**Feature**: `001-knowledge-trace-ocr` | **Date**: 2026-11-16

## Entity Relationship Overview

```text
UserAccount (1) ────< (N) Document (1) ────< (N) HighlightTrace
     │                                               │
     ├────< (N) SearchHistory                        ├────< (N) KnowledgeExplanation
     │                                               │
     └────< (N) StudyMaterial >──────────────────────┘ (N:M via StudyMaterialTrace)
```

## Entities & Validation Rules

### 1. UserAccount (`users`)
- `id`: UUID (PK)
- `email`: String(255), unique, not null, valid email format
- `password_hash`: String(255), not null
- `full_name`: String(120), optional
- `created_at`: DateTime (UTC)

### 2. Document (`documents`)
- `id`: UUID (PK)
- `user_id`: UUID (FK → `users.id`, indexed, not null)
- `title`: String(255), not null (original filename)
- `file_type`: Enum(`pdf`, `png`, `jpg`, `jpeg`), not null
- `file_size_bytes`: Integer, not null (`<= 20 * 1024 * 1024`)
- `is_scanned_pdf`: Boolean, default `false`
- `total_pages`: Integer, not null (`<= 100` for PDF with text layer, `<= 50` for scanned PDF, `1` for image)
- `processed_pages`: Integer, default `0`
- `status`: Enum(`pending`, `processing`, `ready`, `failed`), default `pending`
- `error_message`: Text, nullable
- `storage_path`: String(512), not null
- `created_at`: DateTime (UTC)

**State Transitions**:
- `pending` → `processing` (worker starts page rendering & highlight/OCR)
- `processing` → `ready` (all pages processed)
- `processing` → `failed` (corrupted/encrypted file, API error, or unrecoverable failure)

### 3. HighlightTrace (`highlight_traces`)
- `id`: UUID (PK)
- `document_id`: UUID (FK → `documents.id`, cascade delete, indexed)
- `user_id`: UUID (FK → `users.id`, indexed, not null)
- `page_number`: Integer, not null (`>= 1`)
- `highlight_color`: String(32), nullable (e.g., `yellow`, `green`, `blue`, `pink`, `orange`)
- `bbox_json`: JSON, nullable (`{x, y, width, height}` normalized 0..1 on page)
- `extracted_text`: Text, not null (OCR output in Vietnamese/English)
- `context_snippet`: Text, nullable (surrounding paragraph/context on the same page)
- `language`: Enum(`vi`, `en`, `mixed`), default `mixed`
- `embedding_json`: JSON / Blob, nullable (float vector from Gemini Embeddings for semantic search)
- `created_at`: DateTime (UTC)

*Note*: Read-only in MVP (`FR-005`); deleted only when parent `Document` is deleted.

### 4. SearchHistory (`search_histories`)
- `id`: UUID (PK)
- `user_id`: UUID (FK → `users.id`, indexed, not null)
- `query_text`: String(500), not null
- `result_count`: Integer, not null, default `0`
- `matched_trace_ids_json`: JSON, nullable (ordered list of top matched `HighlightTrace.id`)
- `created_at`: DateTime (UTC)

### 5. KnowledgeExplanation (`knowledge_explanations`)
- `id`: UUID (PK)
- `trace_id`: UUID (FK → `highlight_traces.id`, cascade delete, indexed)
- `user_id`: UUID (FK → `users.id`, indexed, not null)
- `mode`: Enum(`basic`, `deep`, `example`, `summary`), not null
- `content`: Text, not null (Markdown formatted explanation)
- `created_at`: DateTime (UTC)

### 6. StudyMaterial (`study_materials` & `study_material_traces`)
- `id`: UUID (PK)
- `user_id`: UUID (FK → `users.id`, indexed, not null)
- `material_type`: Enum(`flashcard`, `quiz`), not null
- `title`: String(255), not null
- `items_json`: JSON, not null
  - For `flashcard`: `[{front, back, source_trace_id}]`
  - For `quiz`: `[{question, options, correct_answer, explanation, source_trace_id}]`
- `created_at`: DateTime (UTC)
- Join table `study_material_traces`: `(study_material_id, trace_id)`
