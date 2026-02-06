import os
import json
import requests
import boto3
from datetime import datetime, timedelta

# --- Omgevingsvariabelen ---
BUCKET_NAME = os.environ["BUCKET_NAME"]
LANGUAGE = os.environ.get("LANGUAGE", "Python")
MIN_STARS = int(os.environ.get("MIN_STARS", "500"))
PER_PAGE = int(os.environ.get("PER_PAGE", "30"))
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]  # SQS URL
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
SEARCH_URL = "https://api.github.com/search/repositories"

sqs = boto3.client("sqs")

def fetch_github_repos(language, min_stars=500, per_page=30, max_pages=5):
    """GitHub API’dan repo listesi çek"""
    all_items = []
    for page in range(1, max_pages+1):
        params = {
            "q": f"language:{language} stars:>={min_stars}",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        if response.status_code != 200:
            print(f"GitHub API fout: {response.text}")
            break
        items = response.json().get("items", [])
        if not items:
            break
        all_items.extend(items)
    return all_items

def lambda_handler(event, context):
    repos = fetch_github_repos(LANGUAGE, min_stars=MIN_STARS, per_page=PER_PAGE, max_pages=10)
    if not repos:
        print("Geen repositories gevonden voor de opgegeven criteria.")
        return {"statusCode": 200, "body": "Geen repositories gevonden."}

    for repo in repos:
        message = {
            "repo_full_name": repo["full_name"],
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "license": repo.get("license")["spdx_id"] if repo.get("license") else "NOASSERTION"
        }
        sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(message))

    print(f"{len(repos)} repositories naar SQS gestuurd.")

    return {"statusCode": 200, "body": f"{len(repos)} repositories naar SQS gestuurd."}
