import sqlite3
from contextlib import contextmanager
from pathlib import Path


class DocumentRepository:
    """Short-lived connections; service lock coordinates SQLite and Qdrant."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY, filename TEXT NOT NULL,
                storage_path TEXT NOT NULL, file_sha256 TEXT NOT NULL,
                uploaded_at TEXT NOT NULL, status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0, error TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS documents_hash ON documents(file_sha256)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def all(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")]

    def get(self, document_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
            return dict(row) if row else None

    def duplicate(self, digest: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM documents WHERE file_sha256 = ? AND status = 'ready'", (digest,)).fetchone()
            return dict(row) if row else None

    def insert(self, record: dict):
        with self.connect() as db:
            db.execute("""INSERT INTO documents
                (document_id, filename, storage_path, file_sha256, uploaded_at, status)
                VALUES (:document_id, :filename, :storage_path, :file_sha256, :uploaded_at, :status)""", record)

    def update(self, document_id: str, status: str, count: int = 0, error: str | None = None):
        with self.connect() as db:
            db.execute("UPDATE documents SET status = ?, chunk_count = ?, error = ? WHERE document_id = ?",
                       (status, count, error, document_id))

    def delete(self, document_id: str):
        with self.connect() as db:
            db.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
