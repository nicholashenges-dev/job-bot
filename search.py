import json
import requests

print("Job Bot Started")

response = requests.get("https://remoteok.com/api")
jobs = response.json()

print(f"Retrieved {len(jobs)} records")

with open("jobs.json", "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=4)

print("Saved jobs.json")