import hashlib
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from qdrant_client import models

from app.repositories.documents import DocumentRepository
from app.services.chunking import chunk_pages
from app.services.extraction import DocumentError, extract
from app.services.generation import GenerationError
from app.services.knowledge_registry import KnowledgeRegistry
from app.services.vector_store import VectorStore


class RagService:
    """Coordinate document ingestion and question answering."""
    def __init__(self, settings, embeddings, generator):
        self.settings = settings
        self.embeddings = embeddings
        self.generator = generator
        # One lock keeps this single-process local database workflow simple.
        self.lock = threading.RLock()
        self.upload_dir = settings.data_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.repo = DocumentRepository(settings.data_dir / "app.sqlite3")
        self.store = VectorStore(settings.qdrant_path, settings.qdrant_collection, embeddings.dimension)
        self.registry = KnowledgeRegistry()
        self.ready = False
        self.startup_error = None

    def load(self):
        try:
            self.embeddings.load()
            self.ready = True
        except Exception as exc:
            logging.exception("Embedding model could not load")
            self.startup_error = (
                "Windows ran out of virtual memory while loading Qwen (1455). Close memory-heavy apps, then restart the server."
                if "1455" in str(exc)
                else "Could not load the embedding model. Check the server log and restart.")

    def require_ready(self):
        if not self.ready:
            raise GenerationError(self.startup_error or "The embedding model is loading.", 503)

    @staticmethod
    def source_url(document_id, page=None):
        url = f"/api/documents/{document_id}/source"
        return f"{url}#page={page}" if page else url

    def original_path(self, record):
        return self.upload_dir / record["storage_path"]

    def searchable_document_ids(self, records):
        return {r["document_id"] for r in records
                if r["status"] == "ready" and r["metadata"].get("company") == "NovaFiber"
                and r["metadata"].get("customer_chatbot_allowed", True)}

    def public(self, record, searchable_ids=None):
        if searchable_ids is None:
            searchable_ids = self.searchable_document_ids(self.repo.all())
        return {key: value for key, value in record.items() if key != "storage_path"} | {
            "source_url": self.source_url(record["document_id"]),
            "searchable": record["document_id"] in searchable_ids}

    def documents(self):
        with self.lock:
            records = self.repo.all()
            searchable_ids = self.searchable_document_ids(records)
            return [self.public(record, searchable_ids) for record in records]

    def ingest(self, filename, content):
        """Extract, chunk, embed, and store an uploaded document."""
        self.require_ready()
        filename = filename.replace("\\", "/").split("/")[-1]
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".txt"} or not content:
            raise DocumentError("Upload a nonempty PDF or TXT file.")
        digest = hashlib.sha256(content).hexdigest()
        metadata = self.registry.metadata(filename, digest)
        with self.lock:
            existing = self.repo.duplicate(digest)
            if existing:
                return {"document": self.public(existing), "duplicate": True}
            document_id = str(uuid4())
            record = {
                "document_id": document_id, "filename": filename,
                "storage_path": document_id + suffix, "file_sha256": digest,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "status": "processing", "metadata": metadata}
            self.repo.insert(record)
            try:
                path = self.original_path(record)
                path.write_bytes(content)
                chunks = chunk_pages(extract(path), self.embeddings.tokenizer,
                                     self.settings.chunk_size_tokens, self.settings.chunk_overlap_tokens)
                vectors = self.embeddings.encode([chunk.text for chunk in chunks])
                points = [models.PointStruct(id=str(uuid4()), vector=vector, payload={
                    "document_id": document_id, "filename": filename, "metadata": metadata,
                    "text": chunk.text, "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index, "token_count": chunk.token_count,
                    "char_start": chunk.char_start, "char_end": chunk.char_end,
                    "status": "ready", "embedding_model": self.settings.embedding_model
                }) for chunk, vector in zip(chunks, vectors)]
                self.store.add(points)
                self.repo.update(document_id, "ready", len(chunks))
            except Exception as exc:
                self.store.delete(document_id)
                self.repo.update(document_id, "failed", error="Upload failed. Delete and try again.")
                raise DocumentError("Could not ingest the document.") from exc
            return {"document": self.public(self.repo.get(document_id)), "duplicate": False}

    def delete(self, document_id):
        with self.lock:
            record = self.repo.get(document_id)
            if record:
                self.store.delete(document_id)
                self.original_path(record).unlink(missing_ok=True)
                self.repo.delete(document_id)

    def source(self, document_id):
        with self.lock:
            record = self.repo.get(document_id)
            if not record or record["status"] != "ready" or not record["metadata"].get("customer_chatbot_allowed", True):
                return None
            path = self.original_path(record)
            return (record, path) if path.exists() else None

    def retrieve(self, question):
        """Find policy passages relevant to a question."""
        self.require_ready()
        with self.lock:
            document_ids = self.searchable_document_ids(self.repo.all())
            if not document_ids:
                return []
            vector = self.embeddings.encode([question], query=True)[0]
            points = self.store.search(vector, self.settings.retrieval_top_k, document_ids)
            passages = []
            for index, point in enumerate(points):
                p = point.payload
                passages.append({
                    "source_id": f"S{index + 1}", "document_id": p["document_id"],
                    "filename": p["filename"], "page_number": p["page_number"],
                    "chunk_index": p["chunk_index"], "chunk_id": str(point.id),
                    "excerpt": p["text"], "text": p["text"], "metadata": p.get("metadata", {}),
                    "char_start": p.get("char_start"), "char_end": p.get("char_end"),
                    "score": float(point.score),
                    "source_url": self.source_url(p["document_id"], p["page_number"]),
                    "passage_url": f"/sources/{p['document_id']}/{point.id}#passage"})
            return passages

    def passage(self, document_id, chunk_id):
        """Locate a stored passage in its original page text."""
        with self.lock:
            source = self.source(document_id)
            point = self.store.chunk(chunk_id)
            if source is None or point is None or point.payload["document_id"] != document_id:
                return None
            record, path = source
            p = point.payload
            text = dict(extract(path)).get(p["page_number"])
            if text is None:
                return None
            start = p.get("char_start")
            if start is None:
                start = text.find(p["text"])
            end = p.get("char_end", start + len(p["text"]))
            if start < 0 or text[start:end] != p["text"]:
                raise DocumentError("This source no longer matches its citation. Reupload the document.")
            return {
                "document_id": document_id, "chunk_id": chunk_id, "filename": record["filename"],
                "metadata": p.get("metadata", {}), "page_number": p["page_number"],
                "chunk_index": p["chunk_index"], "page_text": text,
                "char_start": start, "char_end": end, "excerpt": p["text"],
                "source_url": self.source_url(document_id, p["page_number"])}

    def chat(self, question):
        started = perf_counter()
        passages = self.retrieve(question)
        logging.info("Chat retrieval completed: passages=%d, elapsed_seconds=%.2f",
                     len(passages), perf_counter() - started)
        if not passages:
            return {"answer": "No policy documents are available yet.", "sources": [], "status": "no_documents"}
        answer, ids = self.generator.generate(question, passages)
        sources = [{key: value for key, value in passage.items() if key not in {"text", "score"}}
                   for passage in passages if passage["source_id"] in ids]
        return {"answer": answer, "sources": sources,
                "status": "answered" if ids else "insufficient_evidence"}

    def close(self):
        self.generator.close()
        self.store.close()
