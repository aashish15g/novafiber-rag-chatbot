import json
from pathlib import Path

from app.repositories.database import connect


class DocumentRepository:
    """Store document records in SQLite."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY, filename TEXT NOT NULL,
                storage_path TEXT NOT NULL, file_sha256 TEXT NOT NULL,
                uploaded_at TEXT NOT NULL, status TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0, error TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS documents_hash ON documents(file_sha256)")

    @staticmethod
    def record(row):
        if row is None:
            return None
        record = dict(row)
        record["metadata"] = json.loads(record.pop("metadata_json"))
        return record

    def all(self) -> list[dict]:
        with connect(self.path) as db:
            return [self.record(row) for row in db.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")]

    def get(self, document_id: str) -> dict | None:
        with connect(self.path) as db:
            row = db.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
            return self.record(row)

    def duplicate(self, digest: str) -> dict | None:
        with connect(self.path) as db:
            row = db.execute("SELECT * FROM documents WHERE file_sha256 = ? AND status = 'ready'", (digest,)).fetchone()
            return self.record(row)

    def insert(self, record: dict):
        with connect(self.path) as db:
            db.execute("""INSERT INTO documents
                (document_id, filename, storage_path, file_sha256, uploaded_at, status, metadata_json)
                VALUES (:document_id, :filename, :storage_path, :file_sha256, :uploaded_at, :status, :metadata_json)""",
                       {**record, "metadata_json": json.dumps(record.get("metadata", {}))})

    def update(self, document_id: str, status: str, count: int = 0, error: str | None = None):
        with connect(self.path) as db:
            db.execute("UPDATE documents SET status = ?, chunk_count = ?, error = ? WHERE document_id = ?",
                       (status, count, error, document_id))

    def delete(self, document_id: str):
        with connect(self.path) as db:
            db.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
