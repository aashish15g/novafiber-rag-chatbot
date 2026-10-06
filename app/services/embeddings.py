import threading

import numpy as np


class EmbeddingService:
    dimension = 1024

    def __init__(self, name: str, device: str, cache_folder=None):
        self.name = name
        self.device = device
        self.cache_folder = str(cache_folder) if cache_folder else None
        self.model = None
        self.lock = threading.RLock()

    def load(self):
        from sentence_transformers import SentenceTransformer

        with self.lock:
            options = {"device": self.device, "cache_folder": self.cache_folder}
            try:
                self.model = SentenceTransformer(self.name, local_files_only=True, **options)
            except OSError:
                self.model = SentenceTransformer(self.name, **options)
            if self.model.get_embedding_dimension() != self.dimension:
                raise ValueError("Embedding model must produce 1024-dimensional vectors.")
            if not self.model.tokenizer.is_fast:
                raise ValueError("Chunking requires a tokenizer supporting character offsets.")

    @property
    def tokenizer(self):
        if self.model is None:
            raise RuntimeError("Embedding model is not ready.")
        return self.model.tokenizer

    def encode(self, texts: list[str], query: bool = False):
        with self.lock:
            if self.model is None:
                raise RuntimeError("Embedding model is not ready.")
            vectors = self.model.encode(texts, batch_size=8, normalize_embeddings=True,
                                        **({"prompt_name": "query"} if query else {}))
            if vectors.shape != (len(texts), self.dimension) or not np.isfinite(vectors).all():
                raise RuntimeError("Embedding model returned invalid vectors.")
            return vectors.tolist()
