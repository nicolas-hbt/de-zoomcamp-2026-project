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
    print("🧹 Cleaning data and unpivoting...")
    df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
    
    # Drop the empty first column (unnamed: 0)
    df = df.drop(columns=[df.columns[0]])

    # Standardize the Date column
    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])

    # Unpivot from Wide to Long
    df = df.melt(id_vars=['date'], var_name='raw_location', value_name='avg_temp')

    # Extract City and Country using the reliable "Split" logic
    location_parts = df['raw_location'].str.split(' - ', expand=True)
    df['country'] = location_parts[1].str.strip().str.title()
    df['city'] = location_parts[0].str.extract(r'in\s+(.*?)\s+\(')[0].str.strip().str.title()

    # Apply 2020 Filter
    df = df[df['date'].dt.year >= 2020]

    # Final cleanup
    df = df.dropna(subset=['city', 'country', 'avg_temp'])
    df['avg_temp'] = pd.to_numeric(df['avg_temp'], errors='coerce')
    df = df[['date', 'city', 'country', 'avg_temp']]

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