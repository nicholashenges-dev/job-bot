import requests

print("Job Bot Started")

response = requests.get("https://remoteok.com/api")
jobs = response.json()

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
    "customer success": -15,
    "recruiter": -20,
    "business development": -20,
    "sales": -15
}

TOP_MATCH_SCORE = 20

results = []

for job in jobs[1:]:
    tags = job.get("tags", [])
    title = job.get("position", "").lower()

    match_found = False
    bad_match = False
    score = 0

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
    print(f"Tags: {', '.join(result['tags'])}")
    print()