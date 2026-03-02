# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-cloud-storage",
#     "openpyxl",
#     "pandas",
#     "pyarrow",
#     "requests",
# ]
# ///

import requests
import pandas as pd
import io
from google.cloud import storage

# Verified Settings
URL = "https://www.fetchseries.com/climate/average-city-temperatures-fsr/average-city-temperatures-fsr.xlsx"
BUCKET_NAME = "de-zoomcamp-project-terra-bucket"
DESTINATION_BLOB = "raw/climate/city_temperatures.parquet"

def main():
    print(f"🚀 Starting cloud ingestion to {BUCKET_NAME}...")
    
    # 1. Fetch
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    
    # 2. Process & Clean
    print("🧹 Cleaning data and fixing types...")
    df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
    
    # Standardize column names
    df.columns = [c.replace(' ', '_').replace('-', '_').lower() for c in df.columns]

    # Fix mixed types (Coerce to float)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop fully empty rows
    df = df.dropna(how='all')

    # 3. Upload
    print(f"⬆️ Uploading Parquet to GCS...")
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(DESTINATION_BLOB)
    
    with io.BytesIO() as buffer:
        df.to_parquet(buffer, index=False, engine='pyarrow')
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type="application/octet-stream")
        
    print("✅ Ingestion complete!")

if __name__ == "__main__":
    main()