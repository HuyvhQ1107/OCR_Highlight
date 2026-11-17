from functools import lru_cache
import os
from pathlib import Path
import tempfile
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    if os.getenv("VERCEL"):
        db_path = (Path(tempfile.gettempdir()) / "dau_vet_tri_thuc.db").as_posix()
        return f"sqlite:///{db_path}"
    return "sqlite:///./dau_vet_tri_thuc.db"


def _default_storage_dir() -> str:
    if os.getenv("VERCEL"):
        return str(Path(tempfile.gettempdir()) / "storage")
    return "./storage"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Dấu Vết Tri Thức API"
    API_V1_PREFIX: str = "/api/v1"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-3.5-flash-lite"
    OPENROUTER_EMBEDDING_MODEL: str = "google/gemini-embedding-001"
    OPENROUTER_TIMEOUT_SECONDS: float = 60.0
    OPENROUTER_MAX_RETRIES: int = 2
    OPENROUTER_RETRY_BACKOFF_SECONDS: float = 1.0

    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = Field(default_factory=_default_database_url)
    STORAGE_DIR: str = Field(default_factory=_default_storage_dir)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Quantitative MVP limits (FR-002, SC-006)
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    MAX_PDF_PAGES: int = 100
    MAX_SCAN_PAGES: int = 50
    ALLOWED_EXTENSIONS: tuple[str, ...] = ("pdf", "png", "jpg", "jpeg")

    @property
    def storage_path(self) -> Path:
        return Path(self.STORAGE_DIR)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
