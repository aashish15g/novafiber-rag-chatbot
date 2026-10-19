import sqlite3
from contextlib import contextmanager


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()
