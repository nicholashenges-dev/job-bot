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

for job in jobs[1:]:
    tags = job.get("tags", [])

    match_found = False
    bad_match = False
    score = 0

    for tag in tags:
        if tag.lower() in bad_tags:
            bad_match = True
            score += bad_tags[tag.lower()]

        if tag.lower() in good_tags:
            match_found = True
            score += good_tags[tag.lower()]

    if match_found and not bad_match:
        print("------------------")
        print(f"Score: {score}")
        print(f"Company: {job.get('company')}")
        print(f"Position: {job.get('position')}")
        print(f"Tags: {', '.join(tags)}")
        print()