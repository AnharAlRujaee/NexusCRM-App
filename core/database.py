"""Small OOP PostgreSQL access layer for NEXUS CRM."""
from __future__ import annotations

import os
from pathlib import Path
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # gives a clear message if requirements have not been installed
    psycopg2 = None
    RealDictCursor = None


def _load_env_file():
    """Load simple KEY=VALUE settings from the project-root .env, without a dependency."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


class DatabaseError(RuntimeError):
    """A user-presentable database access error."""


class Database:
    """Owns PostgreSQL connections and provides parameterized query helpers."""

    def __init__(self, dbname=None, user=None, password=None, host=None, port=None):
        _load_env_file()
        self.config = {
            "dbname": dbname or os.getenv("DB_NAME", "nexus_crm"),
            "user": user or os.getenv("DB_USER", "postgres"),
            "password": password if password is not None else os.getenv("DB_PASSWORD", ""),
            "host": host or os.getenv("DB_HOST", "localhost"),
            "port": port or os.getenv("DB_PORT", "5432"),
        }

    @contextmanager
    def connection(self):
        if psycopg2 is None:
            raise DatabaseError("psycopg2 is missing. Run: python -m pip install psycopg2-binary")
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            if isinstance(exc, DatabaseError):
                raise
            # Avoid showing credentials or connection strings in the UI.
            raise DatabaseError(f"Database operation failed ({exc.__class__.__name__}). Check .env and PostgreSQL.") from exc
        finally:
            if conn is not None:
                conn.close()

    def fetch_all(self, query, params=()):
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def fetch_one(self, query, params=()):
        with self.connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                return dict(row) if row else None

    def execute(self, query, params=()):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount


db = Database()
