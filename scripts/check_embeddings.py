"""Download and cache the local embedding model."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.services.embeddings import EmbeddingService

if __name__ == "__main__":
    settings = Settings()
    embeddings = EmbeddingService(
        settings.embedding_model, settings.embedding_device, settings.data_dir / "models")
    embeddings.load()
    print(f"Loaded {embeddings.name} on {embeddings.device}.")
