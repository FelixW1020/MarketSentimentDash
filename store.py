import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).parent / "dashboard.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                fetched_at REAL NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS mention_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                ts REAL NOT NULL,
                mention_count INTEGER NOT NULL
            )
            """
        )


def cache_get(key: str, ttl: int) -> Optional[Any]:
    with _conn() as con:
        row = con.execute(
            "SELECT payload, fetched_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
    if row is None:
        return None
    if time.time() - row["fetched_at"] > ttl:
        return None
    return json.loads(row["payload"])


def cache_set(key: str, value: Any) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO cache (key, payload, fetched_at) VALUES (?, ?, ?)",
            (key, json.dumps(value, default=str), time.time()),
        )


def append_mention_history(ticker: str, mention_count: int) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO mention_history (ticker, ts, mention_count) VALUES (?, ?, ?)",
            (ticker, time.time(), mention_count),
        )


def get_mention_history(ticker: Optional[str] = None) -> list[dict]:
    with _conn() as con:
        if ticker:
            rows = con.execute(
                "SELECT ticker, ts, mention_count FROM mention_history WHERE ticker = ? ORDER BY ts",
                (ticker,),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT ticker, ts, mention_count FROM mention_history ORDER BY ts"
            ).fetchall()
    return [dict(r) for r in rows]
