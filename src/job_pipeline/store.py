import sqlite3
from datetime import UTC, datetime

from job_pipeline.config import DATA_DIR
from job_pipeline.models import JobCard

DB_PATH = DATA_DIR / "jobs_seen.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs_seen (
    job_id      TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    company     TEXT NOT NULL,
    location    TEXT,
    source      TEXT,
    alert_name  TEXT,
    email_id    TEXT,
    first_seen  TEXT NOT NULL,
    status      TEXT NOT NULL,   -- new | dropped | scored
    reason      TEXT             -- why it was dropped, if it was
);
"""
POSTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS postings (
    job_id      TEXT PRIMARY KEY REFERENCES jobs_seen(job_id),
    raw_text    TEXT,
    apply_state TEXT,          -- None | applied | closed
    fetched_at  TEXT NOT NULL
);
"""

def connect() -> sqlite3.Connection:
    """
    connect to the SQLite database and ensure the schema is created.
    Returns:
        sqlite3.Connection: A connection object to the SQLite database.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    conn.execute(POSTINGS_SCHEMA)
    return conn

def seen_jobs(conn: sqlite3.Connection)-> set[str]:
    """
    Retrieve the set of job IDs that have been seen in the database.
    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.
    Returns:
        set[str]: A set of job IDs that have been seen.
    """
    
    conn.execute("SELECT job_id FROM jobs_seen")
    return {row[0] for row in conn.execute("SELECT job_id FROM jobs_seen")}

def add_jobs(
        conn: sqlite3.Connection,
        cards: list[JobCard],
        status: str,
        reason: list[str] | None = None,
) -> None:
    """
    Add new job cards to the database with the specified status and reason.
    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.
        cards (list[JobCard]): A list of JobCard objects to be added.
        status (str): The status of the job cards (e.g., "new", "dropped", "scored").
        reason (list[str] | None): Optional list of reasons for dropping the job cards.
    """
    now = datetime.now(UTC).isoformat(timespec="seconds")
    reasons = reason if reason is not None else [None] * len(cards)

    rows = [
        (c.job_id, c.title, c.company, c.location, 
         c.source, c.alert_name, c.email_id, now, status, r)
         for c,r in zip(cards, reasons)
    ]

    with conn: # Commits on success but rools back on error
        conn.executemany(
            "INSERT OR REPLACE INTO jobs_seen "
            "(job_id, title, company, location, source, alert_name, email_id, first_seen, status, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows
        )

def pending_ids(conn: sqlite3.Connection, limit: int) -> list[str]:
    """Kept jobs that don't have a posting yet, newest first."""
    rows = conn.execute(
        """SELECT j.job_id FROM jobs_seen j
           LEFT JOIN postings p ON p.job_id = j.job_id
           WHERE j.status = 'new' AND p.job_id IS NULL
           ORDER BY j.first_seen DESC LIMIT ?""",
        (limit,),
    )
    return [r[0] for r in rows]


def save_posting(conn: sqlite3.Connection, job_id: str, raw_text: str,
                 apply_state: str | None) -> None:
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO postings VALUES (?, ?, ?, ?)",
            (job_id, raw_text, apply_state, now),
        )