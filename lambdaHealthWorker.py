import os
import json
import boto3
import requests
import time
from datetime import datetime, timedelta

# -------- Environment --------
BUCKET_NAME = os.environ["BUCKET_NAME"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

s3 = boto3.client("s3")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# -------- Helper: Safe Request --------
def safe_get(url, params=None):
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        # Rate limit handling
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                print("Rate limit hit. Sleeping 5 seconds...")
                time.sleep(5)
                return safe_get(url, params)

        if response.status_code != 200:
            print(f"GitHub error {response.status_code}: {response.text}")
            return None

        return response

    except Exception as e:
        print("Request failed:", str(e))
        return None


# -------- Contributors Count (Pagination Safe) --------
def get_contributors_count(base_url):
    url = f"{base_url}/contributors"
    params = {"per_page": 1, "anon": "true"}

    response = safe_get(url, params)
    if not response:
        return 0

    if "Link" in response.headers:
        link = response.headers["Link"]
        if 'rel="last"' in link:
            last_page = link.split('rel="last"')[0].split("page=")[-1].split(">")[0]
            return int(last_page)
    return len(response.json())


# -------- Commits Last 7 Days --------
def get_last_7_days_commits(base_url):
    since_date = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    url = f"{base_url}/commits"
    params = {"since": since_date, "per_page": 1}

    response = safe_get(url, params)
    if not response:
        return 0

    if "Link" in response.headers:
        link = response.headers["Link"]
        if 'rel="last"' in link:
            last_page = link.split('rel="last"')[0].split("page=")[-1].split(">")[0]
            return int(last_page)
    return len(response.json())


# -------- Main Repo Detail Fetch --------
def get_repo_details(full_name):
    base_url = f"https://api.github.com/repos/{full_name}"

    repo_response = safe_get(base_url)
    if not repo_response:
        return None

    repo_data = repo_response.json()

    contributors_count = get_contributors_count(base_url)
    commits_count = get_last_7_days_commits(base_url)

    return {
        "repo": full_name,
        "language": repo_data.get("language"),
        "stars": repo_data.get("stargazers_count"),
        "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
        "contributors": contributors_count,
        "last_7_days_commits": commits_count,
        "html_url": repo_data.get("html_url")
    }


# -------- Lambda Handler --------
def lambda_handler(event, context):
    print(f"Processing {len(event.get('Records', []))} SQS messages")

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            repo = body["repo"]
            snapshot_date = body["snapshot_date"]

            print(f"Processing repo: {repo}")

            data = get_repo_details(repo)

            if not data:
                print(f"Skipping repo due to fetch error: {repo}")
                continue

            data["snapshot_date"] = snapshot_date

            key = f"health/{snapshot_date}/raw/{repo.replace('/', '_')}.json"

            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=json.dumps(data)
            )

            print(f"Saved: {key}")

            # Small delay to avoid GitHub secondary rate limit
            time.sleep(0.3)

        except Exception as e:
            print("Record processing failed:", str(e))
            continue

    return {"statusCode": 200}
