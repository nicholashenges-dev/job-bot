import json
import requests
import xml.etree.ElementTree as ET



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

def fetch_weworkremotely():
    jobs = []
    base = "https://" + "weworkremotely.com" + "/categories/"
    feeds = [
        base + "remote-back-end-programming-jobs.rss",
        base + "remote-full-stack-programming-jobs.rss"
    ]
    rss_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9,*/*;q=0.8"
    }
    for feed_url in feeds:
        try:
            response = requests.get(feed_url, headers=rss_headers, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for item in root.findall("./channel/item"):
                raw_title = item.findtext("title", "")
                if ":" in raw_title:
                    company, title = [part.strip() for part in raw_title.split(":", 1)]
                else:
                    company, title = "Unknown", raw_title.strip()

                region = item.findtext("region", "") or "Remote"
                link = item.findtext("link", "")
                description = item.findtext("description", "")

                jobs.append({
                    "source": "weworkremotely",
                    "company": company,
                    "title": title,
                    "location": region,
                    "salary_max": 0,
                    "description": description,
                    "tags": ["remote"],
                    "url": link,
                    "apply_url": link
                })
        except Exception as e:
            print(f"Error fetching We Work Remotely ({feed_url}): {e}")
    return jobs

def fetch_greenhouse():
    jobs = []
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        companies = config.get("greenhouse_companies", [])
    except Exception:
        companies = ["stripe", "plaid", "cloudflare", "gitlab"]
    base_url = "https://" + "boards-api.greenhouse.io/v1/boards/"
    for slug in companies:
        try:
            url = f"{base_url}{slug}/jobs"
            response = requests.get(url, params={"content": "true"}, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                continue
            data = response.json()
            for raw in data.get("jobs", []):
                location_obj = raw.get("location") or {}
                location_name = location_obj.get("name", "")
                jobs.append({
                    "source": f"greenhouse ({slug})",
                    "company": slug.capitalize(),
                    "title": raw.get("title", ""),
                    "location": location_name,
                    "salary_max": 0,
                    "description": raw.get("content", ""),
                    "tags": ["greenhouse"],
                    "url": raw.get("absolute_url", ""),
                    "apply_url": raw.get("absolute_url", "")
                })
        except Exception as e:
            print(f"Error fetching Greenhouse ({slug}): {e}")
    return jobs

def fetch_all_jobs():
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_greenhouse())
    return all_jobs


