import sqlite3
import datetime
import threading
from pathlib import Path

_db_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def init_db(db_path: str | Path = "data/queries.db"):
    """Initialise SQLite database and ensure table exists."""
    global _conn
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(db_path, check_same_thread=False)
    _conn.execute(
        """
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            query TEXT NOT NULL
        )
        """
    )
    _conn.commit()


def log_query(endpoint: str, query: str):
    """Persist a query + endpoint + UTC timestamp."""
    if _conn is None:
        raise RuntimeError("DB not initialised. Call init_db() first.")
    ts = datetime.datetime.utcnow().isoformat()
    with _db_lock:
        _conn.execute("INSERT INTO queries (ts, endpoint, query) VALUES (?, ?, ?)", (ts, endpoint, query))
        _conn.commit() 