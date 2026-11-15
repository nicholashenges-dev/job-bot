import requests

print("Job Bot Started")

response = requests.get("https://remoteok.com/api")
jobs = response.json()

print(f"Retrieved {len(jobs)} records")
print()

good_tags = [
    "backend",
    "python",
    "engineer",
    "cloud",
    "sys admin",
    "ops"
]

bad_tags = [
    "marketing",
    "recruiter",
    "sales",
    "customer support",
    "accounting"
]

for job in jobs[1:]:
    tags = job.get("tags", [])

    match_found = False
    bad_match = False

    for tag in tags:
        if tag.lower() in bad_tags:
            bad_match = True

        if tag.lower() in good_tags:
            match_found = True

    if match_found and not bad_match:
        print("------------------")
        print(f"Company: {job.get('company')}")
        print(f"Position: {job.get('position')}")
        print(f"Tags: {', '.join(tags)}")
        print()