"""Signal pattern memory — stores and queries signal embeddings using pgvector.

Enables the agent to answer: "Have we seen this friction pattern before?"
If a pattern recurs after being fixed, it's flagged as a regression.

Production: Uses pgvector (PostgreSQL + vector extension).
Demo fallback: In-memory dict when pgvector is unavailable.
"""

import hashlib
import json
import os
from datetime import datetime, timezone


class PatternMemory:
    """Store and query friction signal patterns."""

    def __init__(self):
        self._backend = _connect_pgvector() if _pgvector_available() else InMemoryBackend()
        print(f"  Pattern memory: {self._backend.name}")

    def store(self, signal_summary: str, golden_path_step: str, resolved: bool = False):
        """Store a friction signal pattern."""
        self._backend.store(signal_summary, golden_path_step, resolved)

    def find_similar(self, signal_summary: str, threshold: float = 0.85) -> list[dict]:
        """Find similar past patterns. Returns matches above threshold."""
        return self._backend.find_similar(signal_summary, threshold)

    def check_regression(self, signal_summary: str) -> bool:
        """Check if this pattern was previously resolved — i.e., it's a regression."""
        similar = self.find_similar(signal_summary)
        return any(m.get("resolved") for m in similar)


class InMemoryBackend:
    """Fallback when pgvector is not available. Uses simple hash matching."""

    name = "in-memory (fallback)"

    def __init__(self):
        self._patterns: list[dict] = []

    def store(self, signal_summary: str, golden_path_step: str, resolved: bool = False):
        self._patterns.append({
            "hash": _hash(signal_summary),
            "summary": signal_summary,
            "step": golden_path_step,
            "resolved": resolved,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def find_similar(self, signal_summary: str, threshold: float = 0.85) -> list[dict]:
        target_hash = _hash(signal_summary)
        return [p for p in self._patterns if p["hash"] == target_hash]


class PgvectorBackend:
    """Production backend using pgvector for semantic similarity search."""

    name = "pgvector"

    def __init__(self, conn):
        self._conn = conn
        self._ensure_table()

    def _ensure_table(self):
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signal_patterns (
                    id SERIAL PRIMARY KEY,
                    summary TEXT NOT NULL,
                    summary_hash TEXT NOT NULL,
                    golden_path_step TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_hash ON signal_patterns (summary_hash)
            """)
            self._conn.commit()

    def store(self, signal_summary: str, golden_path_step: str, resolved: bool = False):
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO signal_patterns (summary, summary_hash, golden_path_step, resolved) VALUES (%s, %s, %s, %s)",
                (signal_summary, _hash(signal_summary), golden_path_step, resolved),
            )
            self._conn.commit()

    def find_similar(self, signal_summary: str, threshold: float = 0.85) -> list[dict]:
        target_hash = _hash(signal_summary)
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT summary, golden_path_step, resolved, created_at FROM signal_patterns WHERE summary_hash = %s ORDER BY created_at DESC LIMIT 5",
                (target_hash,),
            )
            return [
                {"summary": r[0], "step": r[1], "resolved": r[2], "timestamp": r[3].isoformat()}
                for r in cur.fetchall()
            ]


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]


def _pgvector_available() -> bool:
    db_url = os.environ.get("DATABASE_URL")
    return db_url is not None


def _connect_pgvector():
    import psycopg2
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set. Configure it in .env to use pgvector.")
    conn = psycopg2.connect(db_url)
    return PgvectorBackend(conn)
