# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "openpyxl",
#     "pandas",
#     "pyarrow",
#     "requests",
# ]
# ///

import requests
import pandas as pd
import io
import os

URL = "https://www.fetchseries.com/climate/average-city-temperatures-fsr/average-city-temperatures-fsr.xlsx"

def main():
    # Ensure directory exists for local testing
    os.makedirs("ingestion", exist_ok=True)

    print("Downloading data...")
    r = requests.get(URL)
    r.raise_for_status()
    
    # 1. Load data and drop the empty first column (unnamed: 0)
    df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
    df = df.drop(columns=[df.columns[0]])

    # 2. Identify the date column and standardize
    # The date is the first remaining column (index 0)
    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])

    # 3. Unpivot (Melt) from Wide to Long
    print("Unpivoting data from 1,800+ columns to long format...")
    df = df.melt(id_vars=['date'], var_name='raw_location', value_name='avg_temp')

    # 4. Extract City and Country using Split logic
    print("Cleaning location strings and capitalizing...")
    
    # We split by " - " to get [City part, Country part, FSR, Daily]
    # We use expand=True to get a DataFrame of columns
    location_parts = df['raw_location'].str.split(' - ', expand=True)

    # Extract Country: usually the 2nd part (index 1)
    df['country'] = location_parts[1].str.strip().str.title()

    # Extract City: everything after "in " and before " (" in the 1st part (index 0)
    # Using regex extract with a non-greedy catch
    df['city'] = location_parts[0].str.extract(r'in\s+(.*?)\s+\(')[0].str.strip().str.title()

    # 5. Filter for data from 2020 only
    print("Filtering data for 2020 onwards...")
    df = df[df['date'].dt.year >= 2020]

    # 6. Final Data Cleaning
    # Drop rows where city, country, or temperature is missing
    df = df.dropna(subset=['city', 'country', 'avg_temp'])
    
    # Final column selection and order
    df = df[['date', 'city', 'country', 'avg_temp']]
    
    # Force numeric type for Parquet
    df['avg_temp'] = pd.to_numeric(df['avg_temp'], errors='coerce')

    # 7. Save Outputs
    print(f"Saving {len(df)} rows to ingestion/...")
    
    # Save CSV for visual inspection
    df.to_csv("ingestion/diagnostic_check.csv", index=False)
    
    # Save Parquet for Kestra/BigQuery
    try:
        df.to_parquet("ingestion/test_output.parquet", index=False, engine='pyarrow')
        print("Success! Both CSV and Parquet are correctly formatted.")
    except Exception as e:
        print(f"Parquet failed: {e}")

if __name__ == "__main__":
    main()