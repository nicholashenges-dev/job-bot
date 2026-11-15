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

for job in jobs[1:]:
    tags = job.get("tags", [])

    match_found = False

    for tag in tags:
        if tag.lower() in good_tags:
            match_found = True
            break

    if match_found:
        print("------------------")
        print(f"Company: {job.get('company')}")
        print(f"Position: {job.get('position')}")
        print(f"Tags: {', '.join(tags)}")
        print()