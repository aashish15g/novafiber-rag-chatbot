from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.database import connect


class UserRepository:
    """Store accounts and roles in SQLite."""
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with connect(path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                created_at TEXT NOT NULL
            )""")

    def get(self, user_id):
        with connect(self.path) as db:
            row = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def by_email(self, email):
        with connect(self.path) as db:
            row = db.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
            return dict(row) if row else None

    def create(self, email, password_hash, role="user"):
        user = {"user_id": str(uuid4()), "email": email.lower(),
                "password_hash": password_hash, "role": role,
                "created_at": datetime.now(timezone.utc).isoformat()}
        with connect(self.path) as db:
            db.execute("""INSERT INTO users (user_id, email, password_hash, role, created_at)
                VALUES (:user_id, :email, :password_hash, :role, :created_at)""", user)
        return user
