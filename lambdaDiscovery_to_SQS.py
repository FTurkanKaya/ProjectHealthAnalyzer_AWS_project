import os
import json
import boto3
import requests
from datetime import datetime

BUCKET_NAME = os.environ["BUCKET_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
LANGUAGE = os.environ.get("LANGUAGE", "Python")
MIN_STARS = int(os.environ.get("MIN_STARS", "100"))
MAX_REPOS = int(os.environ.get("MAX_REPOS", "250"))

SEARCH_URL = "https://api.github.com/search/repositories"

sqs = boto3.client("sqs")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def fetch_repositories():
    repos = []
    page = 1
    per_page = 100

    while len(repos) < MAX_REPOS:
        params = {
            "q": f"language:{LANGUAGE} stars:>={MIN_STARS}",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }

        r = requests.get(SEARCH_URL, headers=headers, params=params)
        if r.status_code != 200:
            break

        items = r.json().get("items", [])
        if not items:
            break

        repos.extend(items)
        page += 1

    return repos[:MAX_REPOS]

def lambda_handler(event, context):
    snapshot_date = datetime.utcnow().strftime("%Y-%m-%d")
    repos = fetch_repositories()

    for repo in repos:
        message = {
            "repo": repo["full_name"],
            "snapshot_date": snapshot_date
        }

        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )

    return {
        "statusCode": 200,
        "body": f"{len(repos)} repos sent to SQS"
    }
