import requests

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


results = []

for job in jobs[1:]:
    tags = job.get("tags", [])
    title = job.get("position", "").lower()
    location = job.get("location", "").lower()
    description = job.get("description", "").lower()
    full_text = f"{title} {location} {description}"

    # 1. Hard filter: Skip jobs outside US / local area
    if any(region in full_text for region in DISQUALIFIED_REGIONS):
        continue

    # 2. Hard filter: Skip jobs requiring 3+ days in office
    if any(phrase in full_text for phrase in TOO_MANY_OFFICE_DAYS):
        continue

    # 3. Hard filter: Skip if salary is explicitly listed below $85,000
    salary_max = job.get("salary_max") or 0
    if isinstance(salary_max, (int, float)) and 0 < salary_max < MIN_SALARY:
        continue

    # 4. Hard filter: Skip customer-facing & pure support roles
    if any(keyword in title for keyword in bad_title_keywords):
        continue
    if any(phrase in description for phrase in CUSTOMER_FACING_PHRASES):
        continue



    match_found = False
    bad_match = False
    score = 0

    #5 . Check if local (within ~25 mins of Hamburg) or Remote
    is_local = any(city in full_text for city in LOCAL_CITIES)
    is_hybrid = "hybrid" in full_text
    is_remote = "remote" in full_text or location == ""

    if is_hybrid and is_local:
        score += HYBRID_BONUS
    elif is_hybrid and not is_local and location != "" and "remote" not in location:
        # Hybrid tied to a specific non-local city (like Palo Alto or Boston)
        continue
    elif is_remote:
        score += REMOTE_BONUS
    else:
        score += ONSITE_PENALTY

    for keyword in good_title_keywords:
        if keyword in title:
         score += good_title_keywords[keyword]

    for keyword in bad_title_keywords:
        if keyword in title:
         score += bad_title_keywords[keyword]

    for tag in tags:
        if tag.lower() in bad_tags:
            bad_match = True
            score += bad_tags[tag.lower()]

        if tag.lower() in good_tags:
            match_found = True
            score += good_tags[tag.lower()]

    if match_found and not bad_match:
        results.append({
            "score": score,
            "company": job.get("company"),
            "position": job.get("position"),
            "location": job.get("location"),
            "url": job.get("url"),
            "apply_url": job.get("apply_url"),
            "description": job.get("description", ""),
            "tags": tags
        })

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
    print(f"Location: {result['location']}")

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
    print(f"Location: {result['location']}")

    print()
    print(result["description"][:1000])
    print()

    print(f"Tags: {', '.join(result['tags'])}")
    print()