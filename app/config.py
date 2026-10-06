from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    app_env: str = "development"
    data_dir: Path = ROOT / "data"
    qdrant_path: Path | None = None
    qdrant_collection: str = "customer_policies_qwen3_1024_v1"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_device: str = "cpu"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = ""
    chunk_size_tokens: int = Field(default=400, ge=20, le=4096)
    chunk_overlap_tokens: int = Field(default=60, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    max_upload_mb: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def validate_paths_and_overlap(self):
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("Chunk overlap must be smaller than chunk size.")
        if not self.data_dir.is_absolute():
            self.data_dir = ROOT / self.data_dir
        if self.qdrant_path is None:
            self.qdrant_path = self.data_dir / "qdrant"
        elif not self.qdrant_path.is_absolute():
            self.qdrant_path = ROOT / self.qdrant_path
        return self
