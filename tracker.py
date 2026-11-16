from datetime import datetime
import sqlite3

DB_FILE = "jobs.db"

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

def make_fingerprint(company, position):
    clean_company = (company or "").strip().lower()
    clean_position = (position or "").strip().lower()
    return f"{clean_company}|{clean_position}"

def job_exists(company, position):
    fp = make_fingerprint(company, position)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT 1 FROM jobs WHERE fingerprint = ?", (fp,))
        return cursor.fetchone() is not None

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
