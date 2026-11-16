from pathlib import Path
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document
from app.models.highlight_trace import HighlightTrace
from app.models.user import UserAccount
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    HighlightTraceResponse,
)
from app.services.document_processor import delete_document_from_fts, process_document_background
from app.services.highlight_detector import inspect_pdf_metadata
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    settings = get_settings()
    filename = file.filename or "untitled"
    ext = Path(filename).suffix.lstrip(".").lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng tệp không được hỗ trợ. Chỉ chấp nhận: .pdf, .png, .jpg, .jpeg.",
        )

    content = await file.read()
    size_bytes = len(content)
    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tệp tải lên bị rỗng.")
    if size_bytes > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dung lượng tệp vượt quá giới hạn 20 MB.",
        )

    doc_id = str(uuid.uuid4())
    storage = StorageService()
    saved_path = storage.save_document(current_user.id, doc_id, filename, content)

    total_pages = 1
    is_scanned_pdf = False
    if ext == "pdf":
        try:
            total_pages, is_scanned_pdf = inspect_pdf_metadata(saved_path)
        except ValueError as exc:
            storage.delete_document_dir(current_user.id, doc_id)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        if is_scanned_pdf and total_pages > settings.MAX_SCAN_PAGES:
            storage.delete_document_dir(current_user.id, doc_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF scan vượt quá giới hạn {settings.MAX_SCAN_PAGES} trang (tệp có {total_pages} trang).",
            )
        if not is_scanned_pdf and total_pages > settings.MAX_PDF_PAGES:
            storage.delete_document_dir(current_user.id, doc_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF vượt quá giới hạn {settings.MAX_PDF_PAGES} trang (tệp có {total_pages} trang).",
            )

    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        title=filename,
        file_type=ext,
        file_size_bytes=size_bytes,
        is_scanned_pdf=is_scanned_pdf,
        total_pages=total_pages,
        processed_pages=0,
        status="pending",
        storage_path=str(saved_path),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document_background, doc.id)
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    docs = db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    ).all()
    return DocumentListResponse(items=[DocumentResponse.model_validate(d) for d in docs])


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_detail(
    document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    doc = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    traces = db.scalars(
        select(HighlightTrace)
        .where(HighlightTrace.document_id == doc.id, HighlightTrace.user_id == current_user.id)
        .order_by(HighlightTrace.page_number.asc(), HighlightTrace.created_at.asc())
    ).all()

    return DocumentDetailResponse(
        document=DocumentResponse.model_validate(doc),
        highlights=[HighlightTraceResponse.model_validate(t) for t in traces],
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    doc = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    delete_document_from_fts(db, doc.id)
    db.delete(doc)
    db.commit()

    StorageService().delete_document_dir(current_user.id, doc.id)
