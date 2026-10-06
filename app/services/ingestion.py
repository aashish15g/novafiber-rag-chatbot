import hashlib
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from qdrant_client import models

from app.repositories.documents import DocumentRepository
from app.services.chunking import chunk_pages
from app.services.extraction import DocumentError, extract
from app.services.generation import GenerationError
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RagService:
    def __init__(self, settings, embeddings, generator):
        self.settings, self.embeddings, self.generator = settings, embeddings, generator
        self.lock = threading.RLock()
        self.upload_dir = settings.data_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.repo = DocumentRepository(settings.data_dir / "app.sqlite3")
        self.store = VectorStore(settings.qdrant_path, settings.qdrant_collection, embeddings.dimension)
        self.ready = False
        self.startup_error = None
        self.reconcile()

    @staticmethod
    def public(record):
        return {k: v for k, v in record.items() if k != "storage_path"} | {
            "source_url": f"/api/documents/{record['document_id']}/source"}

    def reconcile(self):
        with self.lock:
            for record in self.repo.all():
                if record["status"] in {"processing", "deleting"}:
                    self.store.delete(record["document_id"])
                    if record["status"] == "deleting":
                        self.original_path(record).unlink(missing_ok=True)
                        self.repo.delete(record["document_id"])
                    else:
                        self.repo.update(record["document_id"], "failed", error="Ingestion was interrupted. Delete this record and upload again.")

    def load(self):
        try:
            self.embeddings.load()
            # Smoke-check both encoding paths before exposing readiness.
            self.embeddings.encode(["Customer policy readiness check."])
            self.embeddings.encode(["What is the policy?"], query=True)
            self.ready = True
        except Exception:
            logger.exception("Embedding startup failed")
            self.startup_error = "Embedding model could not be loaded. Check the server log, internet access, and available memory; then restart."

    def require_ready(self):
        if not self.ready:
            raise GenerationError(self.startup_error or "The embedding model is loading. Please try again shortly.", 503)

    def original_path(self, record):
        path = (self.upload_dir / record["storage_path"]).resolve()
        if path.parent != self.upload_dir.resolve():
            raise RuntimeError("Invalid document storage path.")
        return path

    def documents(self):
        with self.lock:
            return [self.public(r) for r in self.repo.all()]

    def ingest(self, filename: str, content: bytes):
        self.require_ready()
        filename = filename.replace("\\", "/").split("/")[-1].strip()
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".txt"}:
            raise DocumentError("Only text-based PDF and UTF-8 TXT files are supported.")
        if not content:
            raise DocumentError("The uploaded file is empty.")
        if len(content) > self.settings.max_upload_mb * 1024 * 1024:
            raise DocumentError("The file exceeds the upload size limit.")
        digest = hashlib.sha256(content).hexdigest()
        with self.lock:
            if existing := self.repo.duplicate(digest):
                return {"document": self.public(existing), "duplicate": True}
            document_id = str(uuid4())
            record = {"document_id": document_id, "filename": filename[:255], "storage_path": document_id + suffix,
                      "file_sha256": digest, "uploaded_at": datetime.now(timezone.utc).isoformat(), "status": "processing"}
            self.repo.insert(record)
            try:
                self.original_path(record).write_bytes(content)
                pages = extract(self.original_path(record))
                chunks = chunk_pages(pages, self.embeddings.tokenizer,
                                     self.settings.chunk_size_tokens, self.settings.chunk_overlap_tokens)
                if not chunks:
                    raise DocumentError("The document contains no usable chunks.")
                for start in range(0, len(chunks), 8):
                    batch = chunks[start:start + 8]
                    vectors = self.embeddings.encode([c.text for c in batch])
                    points = [models.PointStruct(id=str(uuid4()), vector=v, payload={
                        "document_id": document_id, "filename": record["filename"],
                        "file_sha256": digest, "uploaded_at": record["uploaded_at"],
                        "text": c.text, "page_number": c.page_number, "chunk_index": c.chunk_index,
                        "token_count": c.token_count, "embedding_model": self.settings.embedding_model,
                        "chunking_version": "v1", "status": "indexing"}) for c, v in zip(batch, vectors, strict=True)]
                    self.store.add(points)
                self.store.publish(document_id)
                self.repo.update(document_id, "ready", len(chunks))
            except Exception as exc:
                self.store.delete(document_id)
                message = str(exc) if isinstance(exc, DocumentError) else "Ingestion failed. Check the server log and retry."
                self.repo.update(document_id, "failed", error=message)
                if not isinstance(exc, DocumentError):
                    logger.exception("Ingestion failed for %s", document_id)
                raise DocumentError(message) from exc
            return {"document": self.public(self.repo.get(document_id)), "duplicate": False}

    def delete(self, document_id):
        with self.lock:
            record = self.repo.get(document_id)
            if record is None:
                return
            self.repo.update(document_id, "deleting")
            self.store.delete(document_id)
            self.original_path(record).unlink(missing_ok=True)
            self.repo.delete(document_id)

    def source(self, document_id):
        with self.lock:
            record = self.repo.get(document_id)
            if not record or record["status"] != "ready":
                return None
            path = self.original_path(record)
            return (record, path) if path.is_file() else None

    def retrieve(self, question):
        self.require_ready()
        with self.lock:
            ready_ids = {r["document_id"] for r in self.repo.all() if r["status"] == "ready"}
            if not ready_ids:
                return []
            vector = self.embeddings.encode([question], query=True)[0]
            results = self.store.search(vector, self.settings.retrieval_top_k)
            passages = []
            for point in results:
                p = point.payload
                if p["document_id"] not in ready_ids:
                    continue
                label = f"S{len(passages) + 1}"
                url = f"/api/documents/{p['document_id']}/source"
                if p["page_number"]:
                    url += f"#page={p['page_number']}"
                passages.append({"source_id": label, "document_id": p["document_id"],
                    "filename": p["filename"], "page_number": p["page_number"],
                    "chunk_index": p["chunk_index"], "excerpt": p["text"], "text": p["text"],
                    "score": float(point.score), "source_url": url})
            return passages

    def chat(self, question):
        passages = self.retrieve(question)
        if not passages:
            return {"answer": "No policy documents are available yet. Ask the administrator to upload a policy first.",
                    "sources": [], "status": "no_documents"}
        answer, ids = self.generator.generate(question, passages)
        return {"answer": answer, "sources": [{k: v for k, v in p.items() if k not in {"text", "score"}}
                for p in passages if p["source_id"] in ids], "status": "answered" if ids else "insufficient_evidence"}

    def close(self):
        self.generator.close()
        self.store.close()
