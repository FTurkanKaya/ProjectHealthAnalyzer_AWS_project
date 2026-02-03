import os
import requests

# Environment variable'dan token okuyoruz
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

headers = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

REPO = "apache/airflow"
url = f"https://api.github.com/repos/{REPO}"

response = requests.get(url, headers=headers)

print(response.json())
