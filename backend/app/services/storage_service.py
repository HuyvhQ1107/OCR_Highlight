from pathlib import Path
import shutil

from app.core.config import get_settings


class StorageService:
    """Local file storage scoped by user_id and document_id."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or get_settings().storage_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def document_dir(self, user_id: str, document_id: str) -> Path:
        path = self.base_dir / user_id / document_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_document(self, user_id: str, document_id: str, filename: str, content: bytes) -> Path:
        safe_name = Path(filename).name or "document"
        target = self.document_dir(user_id, document_id) / safe_name
        target.write_bytes(content)
        return target

    def delete_document_dir(self, user_id: str, document_id: str) -> None:
        target = self.base_dir / user_id / document_id
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
