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

def fetch_lever():
    jobs = []
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        companies = config.get("lever_companies", [])
    except Exception:
        companies = []

    base_url = "https://" + "api.lever.co/v0/postings/"
    for slug in companies:
        try:
            url = f"{base_url}{slug}"
            response = requests.get(url, params={"mode": "json"}, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                continue
            data = response.json()
            for raw in data:
                categories = raw.get("categories") or {}
                location_name = categories.get("location", "")
                workplace = raw.get("workplaceType", "")
                if workplace == "remote" and "remote" not in location_name.lower():
                    location_name = f"Remote - {location_name}" if location_name else "Remote"

                jobs.append({
                    "source": f"lever ({slug})",
                    "company": slug.capitalize(),
                    "title": raw.get("text", ""),
                    "location": location_name,
                    "salary_max": 0,
                    "description": raw.get("descriptionPlain", "") or raw.get("description", ""),
                    "tags": ["lever", categories.get("team", "")],
                    "url": raw.get("hostedUrl", ""),
                    "apply_url": raw.get("applyUrl") or raw.get("hostedUrl", "")
                })
        except Exception as e:
            print(f"Error fetching Lever ({slug}): {e}")
    return jobs


def fetch_ashby():
    jobs = []
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        companies = config.get("ashby_companies", [])
    except Exception:
        companies = []

    base_url = "https://" + "api.ashbyhq.com" + "/posting-api/job-board/"

    for slug in companies:
        try:
            url = f"{base_url}{slug}"
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                continue
            data = response.json()
            for raw in data.get("jobs", []):
                location_name = raw.get("location", "")
                if raw.get("isRemote") and "remote" not in location_name.lower():
                    location_name = f"Remote - {location_name}" if location_name else "Remote"

                jobs.append({
                    "source": f"ashby ({slug})",
                    "company": slug.capitalize(),
                    "title": raw.get("title", ""),
                    "location": location_name,
                    "salary_max": 0,
                    "description": raw.get("descriptionPlain", "") or raw.get("descriptionHtml", ""),
                    "tags": ["ashby", raw.get("department", "")],
                    "url": raw.get("jobUrl", ""),
                    "apply_url": raw.get("applyUrl") or raw.get("jobUrl", "")
                })
        except Exception as e:
            print(f"Error fetching Ashby ({slug}): {e}")
    return jobs

def fetch_jsearch():
    jobs = []
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        api_key = config.get("rapidapi_key", "")
        queries = config.get("jsearch_queries", [])
    except Exception:
        return jobs

    if not api_key or api_key == "your-rapidapi-key":
        return jobs

    host = "jsearch.p." + "rapidapi.com"
    url = "https://" + host + "/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host
    }

    for query in queries:
        try:
            params = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "date_posted": "week"
            }
            response = requests.get(url, headers=headers, params=params, timeout=20)
            if response.status_code != 200:
                print(f"JSearch error ({query}): status {response.status_code}")
                continue
            data = response.json()
            for raw in data.get("data", []):
                city = raw.get("job_city") or ""
                state = raw.get("job_state") or ""
                country = raw.get("job_country") or ""
                loc_parts = [p for p in [city, state, country] if p]
                location_name = ", ".join(loc_parts)
                if raw.get("job_is_remote") and "remote" not in location_name.lower():
                    location_name = f"Remote - {location_name}" if location_name else "Remote"

                publisher = raw.get("job_publisher") or "jsearch"
                jobs.append({
                    "source": f"jsearch ({publisher})",
                    "company": raw.get("employer_name", ""),
                    "title": raw.get("job_title", ""),
                    "location": location_name,
                    "salary_max": raw.get("job_max_salary") or 0,
                    "description": raw.get("job_description", ""),
                    "tags": ["jsearch", publisher.lower()],
                    "url": raw.get("job_apply_link", ""),
                    "apply_url": raw.get("job_apply_link", "")
                })
        except Exception as e:
            print(f"Error fetching JSearch ({query}): {e}")
    return jobs


def fetch_all_jobs():
    all_jobs = []
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_remotive())
    all_jobs.extend(fetch_jobicy())
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_greenhouse())
    all_jobs.extend(fetch_lever())
    all_jobs.extend(fetch_ashby())
    all_jobs.extend(fetch_jsearch())
    return all_jobs



