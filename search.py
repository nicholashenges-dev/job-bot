import html
import json
import os
import re
import requests

from tracker import (
    get_active_companies,
    get_existing_fingerprints,
    init_db,
    make_fingerprint,
    normalize_company,
    save_job,
)
from sources import fetch_all_jobs

if os.environ.get("CONFIG_JSON", "").strip():
    CONFIG = json.loads(os.environ["CONFIG_JSON"])
else:
    with open("config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)



def clean_description(raw_text):
    text = html.unescape(raw_text)
    text = re.split(r"Please mention the word", text, flags=re.IGNORECASE)[0]
    text = re.sub(r"<.*?>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

NTFY_TOPIC = CONFIG.get("ntfy_topic", "")

def send_phone_alert(new_count, top_matches):
    if new_count <= 0:
        return
    top_lines = "\n".join(
        f"• {job['position']} @ {job['company']} (Score: {job['score']})"
        for job in top_matches[:3]
    )
    message = f"Found {new_count} new job match(es)!\n\nTop picks:\n{top_lines}"
    try:
        requests.post(
            "".join(["https://", "ntfy.sh/", NTFY_TOPIC]),
            data=message.encode("utf-8"),
            headers={"Title": "Job Bot Alert", "Tags": "briefcase"},
            timeout=10
        )
    except Exception as e:
        print(f"Phone alert failed: {e}")


def exceeds_max_office_days(full_text):
    if MAX_OFFICE_DAYS is None:
        return False

    office_day_matches = re.findall(
        r"\b([1-5])\s*(?:-\s*[1-5]\s*)?(?:days?|x|times)\s*(?:a\s+|per\s+|/\s*)?(?:week|wk|in[\s-]office|on[\s-]?site|onsite)?",
        full_text
    )
    for num_str in office_day_matches:
        if int(num_str) > MAX_OFFICE_DAYS:
            return True

    word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    for word, count in word_map.items():
        if count > MAX_OFFICE_DAYS and re.search(rf"\b{word}\s+days?\b", full_text):
            return True

    if MAX_OFFICE_DAYS <= 2:
        if re.search(r"\b(?:1|one)\s+days?\s*(?:a\s+|per\s+|/\s*)?(?:week\s+)?(?:remote|from home|wfh)\b", full_text):
            return True

    return any(phrase in full_text for phrase in TOO_MANY_OFFICE_DAYS)


def has_confirmed_allowed_hybrid_days(full_text):
    if MAX_OFFICE_DAYS is None:
        return True
    allowed_nums = [str(n) for n in range(1, MAX_OFFICE_DAYS + 1)]
    word_map = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
    allowed_words = [word_map[n] for n in range(1, MAX_OFFICE_DAYS + 1) if n in word_map]

    num_pattern = r"\b(?:" + "|".join(allowed_nums) + r")\s*(?:days?|x|times)\s*(?:a\s+|per\s+|/\s*)?(?:week|wk|in[\s-]office|on[\s-]?site|onsite)"
    word_pattern = r"\b(?:" + "|".join(allowed_words) + r")\s+days?\s*(?:a\s+|per\s+|/\s*)?(?:week|wk|in[\s-]office|on[\s-]?site|onsite)"
    return bool(re.search(num_pattern, full_text) or re.search(word_pattern, full_text))


def evaluate_experience_penalty(description_lower):
    if not MAX_REQUIRED_YEARS or MAX_REQUIRED_YEARS <= 0:
        return False, 0

    pattern = re.compile(
        r"(?:minimum of |at least |requires? |with )?(\d{1,2})\s*(?:\+|to\s*\d{1,2}|-\s*\d{1,2})?\s*years?\s+(?:of\s+)?(?:[\w/+-]+\s+){0,4}?(?:experience|developing|development|engineering|working)",
        re.IGNORECASE
    )

    preferred_markers = ("preferred", "nice to have", "bonus", "plus", "ideally", "desired")
    company_history_markers = ("in business", "history", "founded", "serving clients", "industry leader")

    penalty = 0
    for match in pattern.finditer(description_lower):
        years = int(match.group(1))
        if years <= MAX_REQUIRED_YEARS or years > 25:
            continue

        start = max(0, match.start() - 80)
        end = min(len(description_lower), match.end() + 80)
        context = description_lower[start:end]

        if any(marker in context for marker in company_history_markers):
            continue

        over_by = years - MAX_REQUIRED_YEARS
        if any(marker in context for marker in preferred_markers):
            if over_by > MAX_PREFERRED_YEARS_OVER:
                return True, 0
            penalty = max(penalty, over_by)
        else:
            return True, 0

    return False, penalty

def score_job(job):
    company_norm = normalize_company(job.get("company", ""))
    if company_norm and any(ex in company_norm for ex in EXCLUDED_COMPANIES_NORM):
        return None

    tags = job.get("tags", [])
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()
    clean_desc = clean_description(job.get("description", ""))
    description = clean_desc.lower()
    full_text = f"{title} {location} {description}"

    if any(region in full_text for region in DISQUALIFIED_REGIONS):
        return None
    if any(loc in location for loc in DISQUALIFIED_LOCATIONS):
        return None
    allowed_locations = ["remote", "anywhere", "worldwide", "usa", "united states", "buffalo", "hamburg"]
    if location and not any(allowed in location for allowed in allowed_locations):
        return None

    if exceeds_max_office_days(full_text):
        return None

    salary_max = job.get("salary_max") or 0
    if isinstance(salary_max, (int, float)) and 0 < salary_max < MIN_SALARY:
        return None

    if any(keyword in title for keyword in bad_title_keywords):
        return None
    if any(phrase in description for phrase in CUSTOMER_FACING_PHRASES):
        return None

    if any(phrase in full_text for phrase in NON_FULLTIME_PHRASES):
        return None

    should_block_exp, exp_penalty = evaluate_experience_penalty(description)
    if should_block_exp:
        return None

    match_found = False
    bad_match = False
    score = -exp_penalty

    is_local = any(city in full_text for city in LOCAL_CITIES)
    is_hybrid = "hybrid" in full_text
    is_remote = "remote" in full_text or location == ""

    if is_hybrid:
        if not is_local and not is_remote:
            return None
        if REQUIRE_CONFIRMED_HYBRID_DAYS and not is_remote and not has_confirmed_allowed_hybrid_days(full_text):
            return None
        score += HYBRID_BONUS
    elif is_remote:
        score += REMOTE_BONUS
    else:
        return None

    for keyword in good_title_keywords:
        if keyword in title:
            match_found = True
            score += good_title_keywords[keyword]

    for skill, points in resume_skills.items():
        if skill in description:
            score += points

    for phrase, points in builder_keywords.items():
        if phrase in description:
            score += points

    for tag in tags:
        if tag.lower() in bad_tags:
            bad_match = True
            score += bad_tags[tag.lower()]

        if tag.lower() in good_tags:
            match_found = True
            score += good_tags[tag.lower()]

    if match_found and not bad_match:
        return {
            "source": job.get("source", "unknown"),
            "score": score,
            "company": job.get("company"),
            "position": job.get("title"),
            "location": job.get("location"),
            "url": job.get("url"),
            "apply_url": job.get("apply_url"),
            "description": clean_desc,
            "tags": tags
        }

    return None

good_tags = {
    "backend": 10,
    "python": 8,
    "engineer": 5,
    "cloud": 4,
    "sys admin": 3,
    "ops": 2
}

bad_tags = {
    "marketing": -10,
    "recruiter": -10,
    "sales": -8,
    "customer support": -5,
    "customer service": -5,
    "accounting": -10
}

good_title_keywords = CONFIG.get("good_title_keywords", {})
bad_title_keywords = CONFIG.get("bad_title_keywords", {})
resume_skills = CONFIG.get("resume_skills", {})
builder_keywords = CONFIG.get("builder_keywords", {})

TOP_MATCH_SCORE = CONFIG.get("top_match_score", 20)
MIN_SAVE_SCORE = CONFIG.get("min_save_score", 15)
MIN_SALARY = CONFIG.get("min_salary", 85000)
MAX_OFFICE_DAYS = CONFIG.get("max_office_days", 2)
REQUIRE_CONFIRMED_HYBRID_DAYS = CONFIG.get("require_confirmed_hybrid_days", True)
MAX_REQUIRED_YEARS = CONFIG.get("max_required_years_experience", 6)
MAX_PREFERRED_YEARS_OVER = CONFIG.get("max_preferred_years_over", 3)
HIDE_ACTIVE_COMPANIES = CONFIG.get("hide_companies_with_active_applications", True)
EXCLUDED_COMPANIES_NORM = [
    normalize_company(c) for c in CONFIG.get("excluded_companies", []) if normalize_company(c)
]

REMOTE_BONUS = 20
HYBRID_BONUS = 10
ONSITE_PENALTY = -25

LOCAL_CITIES = CONFIG.get("local_cities", [])

DISQUALIFIED_REGIONS = [
    "emea", "latam", "apac", "europe only", "european time zones",
    "based in the eu", "uk only", "canada only", "philippines",
    "outside the united states", "outside the us", "germany", "mexico",
    "berlin", "london", "warsaw", "estonia", "colombia", "brazil",
    "ireland", "seoul", "southeast asia", "singapore", "india"
]

DISQUALIFIED_LOCATIONS = [
    "canada", "toronto", "vancouver", "montreal", "china", "europe",
    "uk", "united kingdom", "london", "dublin", "berlin", "australia",
    "sydney", "new zealand", "france", "spain", "poland", "netherlands",
    "sweden", "japan", "tokyo", "taiwan", "singapore", "india",
    "bengaluru", "argentina", "chile", "mexico", "brazil"
]

TOO_MANY_OFFICE_DAYS = [
    "3 days", "three days", "4 days", "four days", "5 days", "five days",
    "100% onsite", "100% on-site", "fully onsite", "fully on-site",
    "in-office 4", "in office 4", "in-office 3", "in office 3",
    "majority in office", "majority in-office"
]

CUSTOMER_FACING_PHRASES = [
    "customer-facing", "customer facing", "client-facing", "client facing",
    "outbound calls", "inbound calls", "cold calling", "customer calls",
    "manage client relationships", "own the commercial relationship",
    "frontline customer support", "handle customer inquiries"
]

NON_FULLTIME_PHRASES = [
    "task based", "task-based", "paid per task",
    "1099", "independent contractor", "contractor only",
    "freelance", "part-time", "part time",
    "commission only", "uncapped commission", "per task", "10 hours"
]

def run_search():
    jobs = fetch_all_jobs()
    print(f"Retrieved {len(jobs)} total records across all sources\n")

    init_db()
    existing_fps = get_existing_fingerprints()
    active_companies = get_active_companies() if HIDE_ACTIVE_COMPANIES else set()
    results = []

    for job in jobs:
        fp = make_fingerprint(job.get("company"), job.get("title"))
        if fp in existing_fps:
            continue
        existing_fps.add(fp)

        scored = score_job(job)
        if scored:
            results.append(scored)

    results.sort(key=lambda x: x["score"], reverse=True)

    top_matches = []
    strong_matches = []

    strong_matches_count = len(results)

    for result in results:
        if result["score"] >= TOP_MATCH_SCORE:
            top_matches.append(result)
        else:
            strong_matches.append(result)

    print()
    print(f"Strong matches found: {strong_matches_count}")
    print()

    print("TOP MATCHES")
    print("-----------")
    print()

    for result in top_matches:
        print("------------------")
        print(f"Score: {result['score']}")
        print(f"Company: {result['company']}")
        print(f"Position: {result['position']}")
        print(f"Location: {result['location'] or 'Remote'}")
        print(f"Apply URL: {result['apply_url']}")
        print()
        print(result["description"][:1000])
        print()
        print(f"Tags: {', '.join(result['tags'])}")
        print()

    print("OTHER STRONG MATCHES")
    print("--------------------")
    print()

    for result in strong_matches:
        if result["score"] < 15:
            continue

        print("------------------")
        print(f"Score: {result['score']}")
        print(f"Company: {result['company']}")
        print(f"Position: {result['position']}")
        print(f"Location: {result['location'] or 'Remote'}")
        print(f"Apply URL: {result['apply_url']}")
        print()
        print(result["description"][:1000])
        print()
        print(f"Tags: {', '.join(result['tags'])}")
        print()

    new_saved = 0
    alertable_jobs = []
    for result in results:
        if result["score"] >= MIN_SAVE_SCORE:
            save_job(result, source=result.get("source", "unknown"))
            new_saved += 1
            if normalize_company(result.get("company", "")) not in active_companies:
                alertable_jobs.append(result)

    print(f"Saved {new_saved} new matches to jobs.db.")
    send_phone_alert(len(alertable_jobs), alertable_jobs)
    return len(alertable_jobs)


if __name__ == "__main__":
    print("Job Bot Started")
    run_search()
