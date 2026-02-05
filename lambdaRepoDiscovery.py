import os
import json
import requests
import csv
from datetime import datetime
import boto3

# 🌐 Environment Variables
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]        # GitHub access token
BUCKET_NAME = os.environ["BUCKET_NAME"]          # S3 bucket
LANGUAGES = json.loads(os.environ["LANGUAGES"])  # ["Python","JavaScript","Go","C#"]
MIN_STARS = int(os.environ.get("MIN_STARS", 500)) # minimum stars filter

# 🔑 GitHub headers
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# 🗂️ S3 client
s3 = boto3.client("s3")

def lambda_handler(event, context):
    discovered_repos = []

    # 📌 Elke taal afzonderlijk verwerken
    for lang in LANGUAGES:
        print(f"Zoeken naar repos voor taal: {lang}")

        # GitHub Search API endpoint
        url = f"https://api.github.com/search/repositories?q=stars:>{MIN_STARS}+language:{lang}&sort=stars&order=desc&per_page=100"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Fout bij ophalen van {lang}: {response.text}")
            continue

        items = response.json().get("items", [])
        for repo in items:
            discovered_repos.append({
                "repo": repo["full_name"],
                "language": lang,
                "stars": repo["stargazers_count"],
                "license": repo["license"]["spdx_id"] if repo["license"] else "None",
                "snapshot_date": datetime.utcnow().strftime("%Y-%m-%d")
            })

    # 📝 CSV maken
    csv_file_name = f"discovered_repos_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    csv_content = "repo,language,stars,license,snapshot_date\n"
    for r in discovered_repos:
        csv_content += f"{r['repo']},{r['language']},{r['stars']},{r['license']},{r['snapshot_date']}\n"

    # ☁️ CSV opslaan naar S3
    s3.put_object(Bucket=BUCKET_NAME, Key=csv_file_name, Body=csv_content)
    print(f"{csv_file_name} succesvol opgeslagen in S3")

    return {
        "statusCode": 200,
        "body": f"{len(discovered_repos)} repositories ontdekt en opgeslagen."
    }
