# Python 3.9-compatible type hints
from __future__ import annotations

import sqlite3
import datetime
import threading
from pathlib import Path
from typing import Optional, Union


_db_lock = threading.Lock()
# Use Optional for pre-3.10 compatibility
_conn: Optional[sqlite3.Connection] = None


def init_db(db_path: Union[str, Path] = "data/queries.db"):
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


# No change needed here – Python 3.9 supports plain str annotations
def log_query(endpoint: str, query: str):
    """Persist a query + endpoint + UTC timestamp."""
    if _conn is None:
        raise RuntimeError("DB not initialised. Call init_db() first.")
    ts = datetime.datetime.utcnow().isoformat()
    with _db_lock:
        _conn.execute("INSERT INTO queries (ts, endpoint, query) VALUES (?, ?, ?)", (ts, endpoint, query))
        _conn.commit() 