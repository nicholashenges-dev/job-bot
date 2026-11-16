import requests

HEADERS = {
    "Accept": "application/json"
}

def fetch_remoteok():
    jobs = []
    try:
        # RemoteOK works best with default requests headers; avoid rapid back-to-back calls
        response = requests.get("https://remoteok.com/api", timeout=15)
        response.raise_for_status()
        if not response.text.strip():
            print("RemoteOK returned an empty response (likely rate-limited; wait 1-2 mins).")
            return jobs
        data = response.json()
        for raw in data[1:]:
            jobs.append({
                "source": "remoteok",
                "company": raw.get("company", ""),
                "title": raw.get("position", ""),
                "location": raw.get("location", ""),
                "salary_max": raw.get("salary_max", 0),
                "description": raw.get("description", ""),
                "tags": raw.get("tags", []),
                "url": raw.get("url", ""),
                "apply_url": raw.get("apply_url") or raw.get("url", "")
            })
    except Exception as e:
        print(f"Error fetching RemoteOK: {e}")
    return jobs

def fetch_remotive():
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"category": "software-dev", "limit": 50}
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        if not response.text.strip().startswith("{"):
            print(f"Remotive returned non-JSON (status {response.status_code}): {response.text[:120]}")
            return jobs
        data = response.json()
        for raw in data.get("jobs", []):
            jobs.append({
                "source": "remotive",
                "company": raw.get("company_name", ""),
                "title": raw.get("title", ""),
                "location": raw.get("candidate_required_location", ""),
                "salary_max": 0,
                "description": raw.get("description", ""),
                "tags": raw.get("tags", []),
                "url": raw.get("url", ""),
                "apply_url": raw.get("url", "")
            })
    except Exception as e:
        print(f"Error fetching Remotive: {e}")
    return jobs

def fetch_jobicy():
    jobs = []
    try:
        # Updated Jobicy public API endpoint
        url = "https://jobicy.com/api/jobs"
        params = {"count": 50, "industry": "engineering"}
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        if not response.text.strip().startswith("{"):
            print(f"Jobicy returned non-JSON (status {response.status_code}): {response.text[:120]}")
            return jobs
        data = response.json()
        for raw in data.get("jobs", []):
            jobs.append({
                "source": "jobicy",
                "company": raw.get("companyName", ""),
                "title": raw.get("jobTitle", ""),
                "location": raw.get("jobGeo", ""),
                "salary_max": raw.get("annualSalaryMax") or 0,
                "description": raw.get("jobDescription", ""),
                "tags": raw.get("jobIndustry", []) + raw.get("jobType", []),
                "url": raw.get("url", ""),
                "apply_url": raw.get("url", "")
            })
    except Exception as e:
        print(f"Error fetching Jobicy: {e}")
    return jobs

def fetch_all_jobs():
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_jobicy())
    return all_jobs
