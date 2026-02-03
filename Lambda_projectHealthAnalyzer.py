import os
import json
import requests
import boto3
from datetime import datetime, timedelta

# Environment variables van Lambda
BUCKET_NAME = os.environ["BUCKET_NAME"]  # S3 bucket waar JSON bestanden worden opgeslagen
FILE_PREFIX = os.environ["FILE_PREFIX"]  # Voorvoegsel voor bestandsnamen
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]  # GitHub API token

# Headers voor GitHub API authenticatie
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

# Lijst van GitHub repositories om te monitoren
REPOS = [
    "apache/airflow",
    "pallets/flask",
    "numpy/numpy",
    "pandas-dev/pandas"
]

# Functie om Health Score te berekenen
def calculate_health_score(data, repo):
    score = 0
    # Basis score: sterren, forks, watchers, open issues
    score += data.get("stargazers_count", 0) * 1
    score += data.get("forks_count", 0) * 2
    score += data.get("watchers_count", 0) * 0.5
    score -= data.get("open_issues_count", 0) * 1

    # Aantal contributors ophalen
    contrib_url = f"https://api.github.com/repos/{repo}/contributors"
    contrib_resp = requests.get(contrib_url, headers=headers)
    contributors = 0
    if contrib_resp.status_code == 200:
        contributors = len(contrib_resp.json())
        score += contributors * 3

    # Aantal commits in de laatste 30 dagen
    commits_url = f"https://api.github.com/repos/{repo}/commits"
    since_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    commits_resp = requests.get(commits_url, headers=headers, params={"since": since_date})
    recent_commits = 0
    if commits_resp.status_code == 200:
        recent_commits = len(commits_resp.json())
        score += recent_commits * 1

    return max(score, 0), contributors, recent_commits

# Lambda handler functie
def lambda_handler(event, context):
    s3 = boto3.client("s3")  # S3 client om bestanden op te slaan
    
    for repo in REPOS:
        # GitHub API request
        url = f"https://api.github.com/repos/{repo}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            # Foutmelding als ophalen mislukt
            print(f"Fout bij ophalen {repo}: {response.text}")
            continue
        
        data = response.json()  # JSON data van GitHub repository
        # Health score berekenen
        health_score, contributors, recent_commits = calculate_health_score(data, repo)
        
        # Data uitbreiden met nieuwe velden
        data["health_score"] = health_score
        data["contributors_count"] = contributors  # Aantal contributors
        data["recent_commits_30d"] = recent_commits  # Aantal commits laatste 30 dagen
        
        # Bestandsnaam genereren met timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_name = f"{FILE_PREFIX}{repo.replace('/', '_')}_{timestamp}.json"
        
        # Opslaan in S3 bucket
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=json.dumps(data))
        print(f"{repo}: Health Score = {health_score}, Contributors = {contributors}, Aantal commits laatste 30 dagen = {recent_commits}")

    # Lambda resultaat teruggeven
    return {
        "statusCode": 200,
        "body": "Data opgehaald en gedetailleerde Health Scores berekend voor alle repositories."
    }

