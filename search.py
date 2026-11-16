import html
import re
import requests

def clean_description(raw_text):
    # 1. Convert HTML entities like &amp; into normal characters (&)
    text = html.unescape(raw_text)
    # 2. Cut off RemoteOK's "Please mention the word..." spam-check footer
    text = re.split(r"Please mention the word", text, flags=re.IGNORECASE)[0]
    # 3. Strip all HTML tags like <p>, <br/>, <strong>
    text = re.sub(r"<.*?>", " ", text)
    # 4. Collapse extra spaces and blank lines into clean single spaces
    return re.sub(r"\s+", " ", text).strip()

def score_job(job):
    tags = job.get("tags", [])
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()
    clean_desc = clean_description(job.get("description", ""))
    description = clean_desc.lower()
    full_text = f"{title} {location} {description}"

    # 1. Hard filter: Skip jobs outside US / local area
    if any(region in full_text for region in DISQUALIFIED_REGIONS):
        return None

    # 2. Hard filter: Skip jobs requiring 3+ days in office
    if any(phrase in full_text for phrase in TOO_MANY_OFFICE_DAYS):
        return None

    # 3. Hard filter: Skip if salary is explicitly listed below $85,000
    salary_max = job.get("salary_max") or 0
    if isinstance(salary_max, (int, float)) and 0 < salary_max < MIN_SALARY:
        return None

    # 4. Hard filter: Skip customer-facing & pure support roles
    if any(keyword in title for keyword in bad_title_keywords):
        return None
    if any(phrase in description for phrase in CUSTOMER_FACING_PHRASES):
        return None

    # 5. Hard filter: Skip non-full-time, freelance, task-based, and commission roles
    if any(phrase in full_text for phrase in NON_FULLTIME_PHRASES):
        return None

    match_found = False
    bad_match = False
    score = 0

    # 6. Check if local (within ~25 mins of Hamburg) or Remote
    is_local = any(city in full_text for city in LOCAL_CITIES)
    is_hybrid = "hybrid" in full_text
    is_remote = "remote" in full_text or location == ""

    if is_hybrid and is_local:
        score += HYBRID_BONUS
    elif is_hybrid and not is_local and location != "" and "remote" not in location:
        return None
    elif is_remote:
        score += REMOTE_BONUS
    else:
        score += ONSITE_PENALTY

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

print("Job Bot Started")

response = requests.get("https://remoteok.com/api")
jobs = response.json()

print(jobs[1].keys())
print()

print(f"Retrieved {len(jobs)} records")
print()

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

good_title_keywords = {
    "backend": 15,
    "platform": 15,
    "infrastructure": 12,
    "devops": 12,
    "software engineer": 10,
    "site reliability": 15,
    "sre": 15
}

bad_title_keywords = {
    "product manager": -15,
    "account manager": -15,
    "account executive": -20,
    "customer success": -20,
    "customer support": -20,
    "support specialist": -20,
    "client support": -20,
    "solutions engineer": -15,
    "field application": -20,
    "application support": -20,
    "production support": -20,
    "technical support": -20,
    "recruiter": -20,
    "business development": -20,
    "sales": -20
}

resume_skills = {
    "sql": 12,
    "sql server": 15,
    "ms sql": 15,
    "postgresql": 10,
    "postilion": 25,
    "iso 8583": 25,
    "payment": 15,
    "payments": 15,
    "clearing": 15,
    "settlement": 15,
    "visa": 12,
    "mainframe": 12,
    "ibm z": 12,
    "cobol": 10,
    "python": 10,
    "api": 8,
    "rest": 8,
    "agile": 5,
    "sdlc": 5
}

builder_keywords = {
    "build": 6,
    "design and implement": 10,
    "new features": 10,
    "greenfield": 12,
    "architecture": 8,
    "mentorship": 10,
    "mentor": 8,
    "learning": 8,
    "professional development": 8,
    "vendor patching": -15,
    "legacy maintenance": -15,
    "tier 1": -15,
    "tier 2": -12,
    "helpdesk": -20,
    "on-call rotation": -5
}



TOP_MATCH_SCORE = 20
MIN_SALARY = 85000

REMOTE_BONUS = 20
HYBRID_BONUS = 10
ONSITE_PENALTY = -25

LOCAL_CITIES = [
    "buffalo", "hamburg", "orchard park", "lackawanna", 
    "west seneca", "cheektowaga", "amherst", "east aurora", "wny"
]

DISQUALIFIED_REGIONS = [
    "emea", "latam", "apac", "europe only", "european time zones",
    "based in the eu", "uk only", "canada only", "philippines",
    "outside the united states", "outside the us", "germany", "mexico",
    "berlin", "london", "warsaw", "estonia", "colombia", "brazil",
    "ireland", "seoul", "southeast asia", "singapore", "india"
]


TOO_MANY_OFFICE_DAYS = [
    "3 days", "three days", "4 days", "four days", "5 days", "five days",
    "100% onsite", "100% on-site", "fully onsite", "fully on-site"
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
    "commission only", "uncapped commission"
]

results = []

for raw_job in jobs[1:]:
    standardized_job = {
        "company": raw_job.get("company"),
        "title": raw_job.get("position", ""),
        "location": raw_job.get("location", ""),
        "salary_max": raw_job.get("salary_max", 0),
        "description": raw_job.get("description", ""),
        "tags": raw_job.get("tags", []),
        "url": raw_job.get("url"),
        "apply_url": raw_job.get("apply_url")
    }
    scored = score_job(standardized_job)
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