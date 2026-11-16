from flask import Flask, redirect, render_template_string, request, url_for
from tracker import get_all_jobs, init_db, update_job_status

app = Flask(__name__)

STATUSES = ["new", "seen", "applied", "contacted", "interviewing", "rejected", "offer"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Job Bot Tracker</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 24px; background: #f4f6f8; color: #222; }
        h1 { margin-bottom: 8px; }
        .filters { margin-bottom: 20px; }
        .filters a { display: inline-block; padding: 6px 12px; margin-right: 6px; background: #fff;
                     border: 1px solid #ccc; border-radius: 4px; text-decoration: none; color: #333; }
        .filters a.active { background: #0066cc; color: #fff; border-color: #0066cc; }
        .job-card { background: #fff; padding: 16px; margin-bottom: 14px; border-radius: 6px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .score { background: #e6f2ff; color: #0055aa; font-weight: bold; padding: 4px 10px; border-radius: 12px; }
        .meta { color: #666; font-size: 0.9em; margin: 6px 0 10px 0; }
        .desc { font-size: 0.92em; line-height: 1.45; color: #444; margin-bottom: 12px; }
        .actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-top: 1px solid #eee; padding-top: 10px; }
        input[type="text"], select { padding: 6px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 6px 14px; background: #28a745; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #218838; }
        .apply-btn { padding: 6px 14px; background: #0066cc; color: #fff; text-decoration: none; border-radius: 4px; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Job Bot Tracker ({{ jobs|length }})</h1>
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
            <button type="submit">Save</button>
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
    jobs = get_all_jobs()
    if current_status != "all":
        jobs = [j for j in jobs if j["status"] == current_status]
    return render_template_string(HTML_TEMPLATE, jobs=jobs, statuses=STATUSES, current_status=current_status)

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
