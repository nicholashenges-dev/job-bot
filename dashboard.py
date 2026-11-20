import json
from flask import Flask, redirect, render_template_string, request, url_for
from search import run_search
from tracker import (
    get_active_companies,
    get_all_jobs,
    init_db,
    mark_all_new_as_seen,
    normalize_company,
    update_job_status,
)

app = Flask(__name__)

STATUSES = ["new", "seen", "applied", "contacted", "interviewing", "rejected", "offer", "archived"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Bot Tracker</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f4f6f8; color: #222; }
        .top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 14px; }
        h1 { margin: 0; }
        .top-actions { display: flex; flex-wrap: wrap; gap: 8px; }
        .btn-fetch { padding: 8px 16px; background: #0066cc; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        .btn-fetch:hover { background: #0052a3; }
        .btn-seen { padding: 8px 16px; background: #6c757d; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
        .btn-seen:hover { background: #5a6268; }
        .banner { background: #d4edda; color: #155724; padding: 10px 14px; border-radius: 4px; margin-bottom: 14px; border: 1px solid #c3e6cb; }
        .filters { margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 6px; }
        .filters a { display: inline-block; padding: 6px 12px; background: #fff;
                     border: 1px solid #ccc; border-radius: 4px; text-decoration: none; color: #333; }
        .filters a.active { background: #0066cc; color: #fff; border-color: #0066cc; }
        .job-card { background: #fff; padding: 16px; margin-bottom: 14px; border-radius: 6px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
        .score { background: #e6f2ff; color: #0055aa; font-weight: bold; padding: 4px 10px; border-radius: 12px; white-space: nowrap; }
        .meta { color: #666; font-size: 0.9em; margin: 6px 0 10px 0; }
        .desc { font-size: 0.92em; line-height: 1.45; color: #444; margin-bottom: 12px; }
        .actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-top: 1px solid #eee; padding-top: 10px; }
        input[type="text"], select { padding: 6px; border: 1px solid #ccc; border-radius: 4px; }
        button.save-btn { padding: 6px 14px; background: #28a745; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
        button.save-btn:hover { background: #218838; }
        .apply-btn { padding: 6px 14px; background: #0066cc; color: #fff; text-decoration: none; border-radius: 4px; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Job Bot Tracker ({{ jobs|length }})</h1>
        <div class="top-actions">
            <form method="POST" action="{{ url_for('fetch') }}">
                <button type="submit" class="btn-fetch">Fetch New Jobs</button>
            </form>
            <form method="POST" action="{{ url_for('mark_seen') }}">
                <button type="submit" class="btn-seen">Mark All New as Seen</button>
            </form>
        </div>
    </div>

    {% if message %}
        <div class="banner">{{ message }}</div>
    {% endif %}

    <div class="filters">
        <a href="{{ url_for('index', status='all') }}" class="{{ 'active' if current_status == 'all' else '' }}">All</a>
        {% for s in statuses %}
            <a href="{{ url_for('index', status=s) }}" class="{{ 'active' if current_status == s else '' }}">{{ s|capitalize }}</a>
        {% endfor %}
    </div>

    {% for job in jobs %}
    <div class="job-card">
        <div class="header">
            <div><strong>{{ job.position }}</strong> — {{ job.company }}</div>
            <span class="score">Score: {{ job.score }}</span>
        </div>
        <div class="meta">
            Source: {{ job.source }} | Location: {{ job.location }} | Found: {{ job.date_found }}
            {% if job.date_applied %} | Applied: <strong>{{ job.date_applied }}</strong>{% endif %}
        </div>
        <div class="desc">{{ job.description[:450] }}...</div>
        <form class="actions" method="POST" action="{{ url_for('update', job_id=job.id) }}">
            <input type="hidden" name="filter_status" value="{{ current_status }}">
            <a class="apply-btn" href="{{ job.apply_url }}" target="_blank">Open Job Post</a>
            <label>Status:
                <select name="status">
                    {% for s in statuses %}
                        <option value="{{ s }}" {{ 'selected' if job.status == s else '' }}>{{ s|capitalize }}</option>
                    {% endfor %}
                </select>
            </label>
            <input type="text" name="offer_amount" placeholder="Offer ($)" value="{{ job.offer_amount or '' }}" size="12">
            <input type="text" name="notes" placeholder="Notes (e.g. recruiter name, tech stack)..." value="{{ job.notes or '' }}" size="35">
            <button type="submit" class="save-btn">Save</button>
        </form>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route("/")
def index():
    init_db()
    current_status = request.args.get("status", "all")
    message = request.args.get("message", "")

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        hide_active_companies = config.get("hide_companies_with_active_applications", True)
    except Exception:
        hide_active_companies = True

    jobs = get_all_jobs()

    if hide_active_companies:
        active_companies = get_active_companies()
        jobs = [
            j for j in jobs
            if not (j["status"] in ("new", "seen") and normalize_company(j["company"]) in active_companies)
        ]

    if current_status != "all":
        jobs = [j for j in jobs if j["status"] == current_status]
    else:
        jobs = [j for j in jobs if j["status"] != "archived"]
    return render_template_string(HTML_TEMPLATE, jobs=jobs, statuses=STATUSES, current_status=current_status, message=message)

@app.route("/fetch", methods=["POST"])
def fetch():
    new_count = run_search()
    return redirect(url_for("index", status="new", message=f"Scan complete! Found {new_count} new job(s)."))

@app.route("/mark-seen", methods=["POST"])
def mark_seen():
    updated_count = mark_all_new_as_seen()
    return redirect(url_for("index", status="all", message=f"Marked {updated_count} job(s) as seen."))

@app.route("/update/<int:job_id>", methods=["POST"])
def update(job_id):
    status = request.form.get("status", "seen")
    notes = request.form.get("notes", "")
    offer_amount = request.form.get("offer_amount", "")
    filter_status = request.form.get("filter_status", "all")
    update_job_status(job_id, status, notes=notes, offer_amount=offer_amount)
    return redirect(url_for("index", status=filter_status))

if __name__ == "__main__":
    print("Starting Job Bot Dashboard at http://127.0.0.1:5000")
    app.run(debug=True)
