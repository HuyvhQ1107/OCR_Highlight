from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Dấu Vết Tri Thức API"
    API_V1_PREFIX: str = "/api/v1"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./dau_vet_tri_thuc.db"
    STORAGE_DIR: str = "./storage"
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
