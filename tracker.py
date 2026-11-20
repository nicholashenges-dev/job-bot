from datetime import datetime
import json
import os
import re
import sqlite3

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

DB_FILE = "jobs.db"
ACTIVE_APPLICATION_STATUSES = ("applied", "contacted", "interviewing", "offer")


def get_database_url():
    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url:
        return env_url
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return (config.get("database_url") or "").strip()
    except Exception:
        return ""


def _pg_connect(db_url):
    if psycopg2 is None:
        raise RuntimeError("psycopg2-binary is not installed. Run: pip install psycopg2-binary")
    return psycopg2.connect(db_url)


def init_db():
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        fingerprint TEXT UNIQUE,
                        source TEXT,
                        company TEXT,
                        position TEXT,
                        location TEXT,
                        score INTEGER,
                        apply_url TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'new',
                        date_found TEXT,
                        date_applied TEXT,
                        offer_amount TEXT DEFAULT '',
                        notes TEXT DEFAULT ''
                    )
                """)
        return

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE,
                source TEXT,
                company TEXT,
                position TEXT,
                location TEXT,
                score INTEGER,
                apply_url TEXT,
                description TEXT,
                status TEXT DEFAULT 'new',
                date_found TEXT,
                date_applied TEXT,
                offer_amount TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            )
        """)


def normalize_company(company):
    clean = (company or "").strip().lower()
    clean = re.sub(r"\b(inc|llc|corp|corporation|ltd|co|company)\b\.?", "", clean)
    clean = re.sub(r"[^a-z0-9]+", " ", clean)
    return clean.strip()


def make_fingerprint(company, position):
    clean_company = (company or "").strip().lower()
    clean_position = (position or "").strip().lower()
    return f"{clean_company}|{clean_position}"


def job_exists(company, position):
    fp = make_fingerprint(company, position)
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM jobs WHERE fingerprint = %s", (fp,))
                return cur.fetchone() is not None

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT 1 FROM jobs WHERE fingerprint = ?", (fp,))
        return cursor.fetchone() is not None

def get_existing_fingerprints():
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT fingerprint FROM jobs")
                return {row[0] for row in cur.fetchall() if row[0]}

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT fingerprint FROM jobs")
        return {row[0] for row in cursor.fetchall() if row[0]}   

def get_active_companies():
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                placeholders = ",".join("%s" for _ in ACTIVE_APPLICATION_STATUSES)
                cur.execute(
                    f"SELECT DISTINCT company FROM jobs WHERE status IN ({placeholders})",
                    ACTIVE_APPLICATION_STATUSES
                )
                return {normalize_company(row) for row in cur.fetchall() if normalize_company(row)}

    with sqlite3.connect(DB_FILE) as conn:
        placeholders = ",".join("?" for _ in ACTIVE_APPLICATION_STATUSES)
        cursor = conn.execute(
            f"SELECT DISTINCT company FROM jobs WHERE status IN ({placeholders})",
            ACTIVE_APPLICATION_STATUSES
        )
        return {normalize_company(row) for row in cursor.fetchall() if normalize_company(row)}


def save_job(job, source="remoteok"):
    fp = make_fingerprint(job.get("company"), job.get("position"))
    today = datetime.now().strftime("%Y-%m-%d")
    values = (
        fp,
        source,
        job.get("company"),
        job.get("position"),
        job.get("location") or "Remote",
        job.get("score"),
        job.get("apply_url") or job.get("url"),
        job.get("description", ""),
        today
    )

    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jobs (
                        fingerprint, source, company, position, location,
                        score, apply_url, description, status, date_found
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'new', %s)
                    ON CONFLICT (fingerprint) DO NOTHING
                """, values)
        return

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (
                fingerprint, source, company, position, location,
                score, apply_url, description, status, date_found
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
        """, values)


def get_all_jobs():
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM jobs ORDER BY score DESC, date_found DESC")
                return [dict(row) for row in cur.fetchall()]

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM jobs ORDER BY score DESC, date_found DESC")
        return [dict(row) for row in cursor.fetchall()]


def update_job_status(job_id, status, notes="", offer_amount=""):
    date_applied = datetime.now().strftime("%Y-%m-%d") if status == "applied" else None
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                if date_applied:
                    cur.execute("""
                        UPDATE jobs
                        SET status = %s, notes = %s, offer_amount = %s, date_applied = COALESCE(date_applied, %s)
                        WHERE id = %s
                    """, (status, notes, offer_amount, date_applied, job_id))
                else:
                    cur.execute("""
                        UPDATE jobs
                        SET status = %s, notes = %s, offer_amount = %s
                        WHERE id = %s
                    """, (status, notes, offer_amount, job_id))
        return

    with sqlite3.connect(DB_FILE) as conn:
        if date_applied:
            conn.execute("""
                UPDATE jobs
                SET status = ?, notes = ?, offer_amount = ?, date_applied = COALESCE(date_applied, ?)
                WHERE id = ?
            """, (status, notes, offer_amount, date_applied, job_id))
        else:
            conn.execute("""
                UPDATE jobs
                SET status = ?, notes = ?, offer_amount = ?
                WHERE id = ?
            """, (status, notes, offer_amount, job_id))


def mark_all_new_as_seen():
    db_url = get_database_url()
    if db_url:
        with _pg_connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE jobs SET status = 'seen' WHERE status = 'new'")
                return cur.rowcount

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("UPDATE jobs SET status = 'seen' WHERE status = 'new'")
        return cursor.rowcount
