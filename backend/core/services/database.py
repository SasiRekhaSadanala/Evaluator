"""
PostgreSQL database management for the Evaluator system.

Provides connection pooling, schema initialization, and a context-managed
connection interface used by all persistent services (review queue, student
tracker, submission index).
"""

import os
import uuid
from contextlib import contextmanager
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
    student_id      TEXT,
    display_name    TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);

-- Submission index for plagiarism detection
CREATE TABLE IF NOT EXISTS submission_index (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id   TEXT NOT NULL,
    student_id      TEXT NOT NULL,
    fingerprint     TEXT NOT NULL,
    normalized_code TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sub_assignment ON submission_index(assignment_id);
CREATE INDEX IF NOT EXISTS idx_sub_fingerprint ON submission_index(fingerprint);

-- Human review queue
CREATE TABLE IF NOT EXISTS review_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id   TEXT NOT NULL,
    student_id      TEXT NOT NULL,
    assignment_id   TEXT NOT NULL,
    trigger         TEXT,
    auto_score      FLOAT,
    flag_reasons    JSONB,
    status          TEXT DEFAULT 'pending',
    teacher_score   FLOAT,
    teacher_notes   TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_review_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_review_assignment ON review_queue(assignment_id);

-- Student score history
CREATE TABLE IF NOT EXISTS student_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      TEXT NOT NULL,
    assignment_id   TEXT NOT NULL,
    topic_tag       TEXT,
    score           FLOAT NOT NULL,
    submitted_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_scores_student ON student_scores(student_id);
CREATE INDEX IF NOT EXISTS idx_scores_topic ON student_scores(student_id, topic_tag);

-- Persistent evaluation results
CREATE TABLE IF NOT EXISTS evaluation_results (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id          TEXT NOT NULL,
    submission_id     TEXT NOT NULL,
    assignment_type   TEXT NOT NULL,
    file              TEXT,
    final_score       FLOAT NOT NULL,
    max_score         FLOAT DEFAULT 100,
    percentage        FLOAT NOT NULL,
    feedback          JSONB,
    flag_score        FLOAT,
    flag_reasons      JSONB,
    percentile        INT,
    improvement_delta FLOAT,
    trend             TEXT,
    evaluated_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_eval_batch ON evaluation_results(batch_id);
CREATE INDEX IF NOT EXISTS idx_eval_time ON evaluation_results(evaluated_at DESC);

-- Evaluation batch summary
CREATE TABLE IF NOT EXISTS evaluation_batches (
    batch_id                 TEXT PRIMARY KEY,
    assignment_type          TEXT,
    total_submissions        INT,
    average_score            FLOAT,
    average_percentage       FLOAT,
    highest_score            FLOAT,
    lowest_score             FLOAT,
    csv_output_path          TEXT,
    csv_detailed_output_path TEXT,
    evaluated_at             TIMESTAMPTZ DEFAULT now()
);
"""


# ---------------------------------------------------------------------------
# Database singleton
# ---------------------------------------------------------------------------

class Database:
    """PostgreSQL connection manager with lazy initialization."""

    _instance: Optional["Database"] = None

    def __init__(self):
        self._connection_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "dbname": os.getenv("DB_NAME", "evaluator"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "sslmode": os.getenv("DB_SSLMODE", "prefer"),  # Render/Neon: set to "require"
            "connect_timeout": 10,
        }
        self._conn = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "Database":
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    @property
    def available(self) -> bool:
        """Check if PostgreSQL is reachable."""
        if not PSYCOPG2_AVAILABLE:
            return False
        try:
            self._ensure_connection()
            return True
        except Exception:
            return False

    # -- connection helpers ---------------------------------------------------

    def _ensure_connection(self):
        """Create or re-establish the connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._connection_params)
            self._conn.autocommit = True

    def _ensure_schema(self):
        """Run schema creation (idempotent)."""
        if self._initialized:
            return
        self._ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        self._initialized = True

    # -- public API -----------------------------------------------------------

    @contextmanager
    def get_cursor(self):
        """
        Context-managed cursor.  Usage::

            db = Database.get_instance()
            with db.get_cursor() as cur:
                cur.execute("SELECT ...")
                rows = cur.fetchall()
        """
        self._ensure_connection()
        self._ensure_schema()
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def execute(self, query: str, params=None):
        """Execute a query and return all rows (or None for writes)."""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return None

    def execute_one(self, query: str, params=None):
        """Execute a query and return a single row."""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchone()
            return None

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


def get_db() -> Database:
    """Convenience accessor."""
    return Database.get_instance()


def init_db():
    """Initialize database schema. Safe to call multiple times."""
    db = get_db()
    if db.available:
        db._ensure_schema()
        print("✓ Database schema initialized.")
    else:
        print("⚠ PostgreSQL not available. Database features disabled.")
