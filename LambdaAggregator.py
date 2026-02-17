import os
import json
import boto3
import csv
from io import StringIO
from datetime import datetime, timedelta

# --- Environment Variables ---
BUCKET_NAME = os.environ["BUCKET_NAME"]
DAILY_PREFIX = os.environ.get("DAILY_PREFIX", "health/")
WEEKLY_PREFIX = os.environ.get("WEEKLY_PREFIX", "health/weekly/")

s3 = boto3.client("s3")


# --- Yardımcı Fonksiyonlar ---
def get_last_7_days_folders():
    """Son 7 günü hesapla ve S3 pathlerini oluştur"""
    today = datetime.utcnow().date()
    folders = []
    for i in range(7):
        day = today - timedelta(days=i)
        folder_name = day.strftime("%Y-%m-%d")
        folders.append(f"{DAILY_PREFIX}{folder_name}/raw/")
    folders.reverse()  # eski -> yeni sıralı
    return folders


def list_json_files(prefix):
    """Verilen prefix altındaki JSON dosyalarını listele"""
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                files.append(obj["Key"])
    return files


def read_json_from_s3(key):
    """S3’den JSON oku"""
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return json.loads(obj["Body"].read())


def save_weekly_data(all_data, snapshot_date):
    """Haftalık CSV ve JSON dosyalarını S3’e kaydet"""
    weekly_folder = f"{WEEKLY_PREFIX}{snapshot_date}/"

    # JSON
    json_key = f"{weekly_folder}summary.json"
    s3.put_object(Bucket=BUCKET_NAME, Key=json_key, Body=json.dumps(all_data))

    # CSV
    if all_data:
        output = StringIO()
        fieldnames = list(all_data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for item in all_data:
            writer.writerow(item)
        csv_key = f"{weekly_folder}summary.csv"
        s3.put_object(Bucket=BUCKET_NAME, Key=csv_key, Body=output.getvalue())

    return json_key, csv_key


# --- Lambda Handler ---
def lambda_handler(event, context):
    snapshot_date = datetime.utcnow().strftime("%G-W%V")  # Örn: 2026-W07
    print(f"Weekly snapshot: {snapshot_date}")

    all_data = []

    folders = get_last_7_days_folders()
    print("Checking daily folders:", folders)

    for folder in folders:
        json_files = list_json_files(folder)
        print(f"Found {len(json_files)} files in {folder}")
        for key in json_files:
            data = read_json_from_s3(key)
            all_data.append(data)

    if not all_data:
        print("No data found for the week.")
        return {"statusCode": 200, "body": "No data for weekly aggregation"}

    json_key, csv_key = save_weekly_data(all_data, snapshot_date)

    print(f"Weekly data saved: {json_key}, {csv_key}")

    return {
        "statusCode": 200,
        "body": f"Weekly aggregation completed. Total records: {len(all_data)}"
    }
