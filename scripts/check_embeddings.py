"""Download/cache the real model and verify retrieval without any Gemini key."""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import ROOT, Settings
from app.services.embeddings import EmbeddingService
from app.services.generation import GenerationService
from app.services.ingestion import RagService


def main():
    settings = Settings()
    embedding = EmbeddingService(settings.embedding_model, settings.embedding_device, settings.data_dir / "models")
    started = time.perf_counter()
    embedding.load()
    print(f"Loaded {embedding.name} on {embedding.device} in {time.perf_counter() - started:.1f}s", flush=True)
    with tempfile.TemporaryDirectory(prefix="policy-desk-smoke-") as temp:
        local = Settings(_env_file=None, data_dir=Path(temp))
        rag = RagService(local, embedding, GenerationService("", settings.gemini_model))
        rag.ready = True
        try:
            for filename in ("returns-policy.txt", "shipping-policy.txt"):
                content = (ROOT / "tests" / "fixtures" / filename).read_bytes()
                rag.ingest(filename, content)
            results = []
            for question, expected in [("Can I return an unopened product after two weeks?", "returns-policy.txt"),
                                       ("How many days does express shipping take?", "shipping-policy.txt")]:
                started = time.perf_counter()
                matches = rag.retrieve(question)
                assert matches and matches[0]["filename"] == expected, matches
                assert matches[0]["text"] and matches[0]["source_url"]
                results.append({"question": question, "top_source": matches[0]["filename"],
                                "score": matches[0]["score"], "seconds": round(time.perf_counter() - started, 2)})
            print(json.dumps({"dimensions": embedding.dimension, "retrieval_checks": results}, indent=2))
        finally:
            rag.close()


if __name__ == "__main__":
    main()
