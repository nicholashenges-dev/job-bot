import requests

print("Job Bot Started")

response = requests.get("https://remoteok.com/api")

print(f"Status Code: {response.status_code}")