from datetime import datetime
import re
import sqlite3

DB_FILE = "jobs.db"
ACTIVE_APPLICATION_STATUSES = ("applied", "contacted", "interviewing", "offer")

def init_db():
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT 1 FROM jobs WHERE fingerprint = ?", (fp,))
        return cursor.fetchone() is not None

def get_active_companies():
    with sqlite3.connect(DB_FILE) as conn:
        placeholders = ",".join("?" for _ in ACTIVE_APPLICATION_STATUSES)
        cursor = conn.execute(
            f"SELECT DISTINCT company FROM jobs WHERE status IN ({placeholders})",
            ACTIVE_APPLICATION_STATUSES
        )
        return {normalize_company(row[0]) for row in cursor.fetchall() if normalize_company(row[0])}

def save_job(job, source="remoteok"):
    fp = make_fingerprint(job.get("company"), job.get("position"))
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (
                fingerprint, source, company, position, location,
                score, apply_url, description, status, date_found
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
        """, (
            fp,
            source,
            job.get("company"),
            job.get("position"),
            job.get("location") or "Remote",
            job.get("score"),
            job.get("apply_url") or job.get("url"),
            job.get("description", ""),
            today
        ))

def get_all_jobs():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM jobs ORDER BY score DESC, date_found DESC")
        return [dict(row) for row in cursor.fetchall()]

def update_job_status(job_id, status, notes="", offer_amount=""):
    date_applied = datetime.now().strftime("%Y-%m-%d") if status == "applied" else None
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
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("UPDATE jobs SET status = 'seen' WHERE status = 'new'")
        return cursor.rowcount
