# Job Bot — Customizable Multi-Source Job Aggregator & Tracker

A lightweight, customizable Python job search aggregator and web dashboard that pulls listings from multiple remote and company career feeds, scores them against your personal skills and filters, deduplicates across boards in SQLite, and sends push alerts to your phone when new matches arrive.

## Features
- **Multi-Source Aggregation:** Pulls live listings from RemoteOK, Remotive, Jobicy, We Work Remotely (RSS), and Greenhouse company career boards.
- **Custom Scoring & Hard Filters:** Ranks jobs using your weighted title keywords, technical skills, and builder keywords while filtering out non-full-time, customer-support, foreign, or on-site roles.
- **Cross-Site Deduplication:** Fingerprints `(company, title)` in a local SQLite database (`jobs.db`) so duplicate postings across boards are skipped automatically.
- **Web Dashboard (`dashboard.py`):** Mobile-friendly Flask UI to browse matches, open application links, update statuses (`new`, `seen`, `applied`, `contacted`, `interviewing`, `rejected`, `offer`, `archived`), and track notes or offers.
- **Phone Push Alerts (`ntfy.sh`):** Sends instant push notifications to your phone whenever new matches are saved.

## Quick Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com
cd job-bot
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Your Preferences
Copy `config.example.json` to `config.json` and customize your settings:
```bash
copy config.example.json config.json
```
Edit `config.json` to set:
- **`ntfy_topic`**: Your private topic name from the free [ntfy](https://ntfy.sh) mobile app (leave blank `""` to disable phone alerts).
- **`min_salary`**: Minimum acceptable annual salary when listed.
- **`local_cities`**: Cities within your commute radius for local/hybrid roles.
- **`greenhouse_companies`**: Company board slugs to pull directly from Greenhouse.
- **`good_title_keywords`**, **`bad_title_keywords`**, **`resume_skills`**, and **`builder_keywords`**: Weighted keywords used to score and filter job descriptions.

### 3. Run the Search & Launch the Dashboard
Run a scan from the terminal:
```bash
python search.py
```

Launch the local web dashboard:
```bash
python dashboard.py
```
Open **`http://127.0.0.1:5000`** in your browser to review matches, trigger new scans with **Fetch New Jobs**, and track your applications.
