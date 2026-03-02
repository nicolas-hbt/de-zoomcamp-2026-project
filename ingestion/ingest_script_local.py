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

URL = "https://www.fetchseries.com/climate/average-city-temperatures-fsr/average-city-temperatures-fsr.xlsx"

def main():
    print("Downloading data...")
    r = requests.get(URL)
    df = pd.read_excel(io.BytesIO(r.content), engine='openpyxl')
    
    # Clean column names
    df.columns = [c.replace(' ', '_').replace('-', '_').lower() for c in df.columns]

    # DIAGNOSTIC: Save as CSV first
    print("Saving to CSV for inspection...")
    df.to_csv("ingestion/diagnostic_check.csv", index=False)
    
    # FIX: Force everything to float to satisfy Parquet's strictness
    print("Attempting to fix types for Parquet...")
    for col in df.columns:
        # We try to convert to numeric; if it fails, it becomes NaN (a float)
        # This prevents the "Expected bytes, got float" error
        df[col] = pd.to_numeric(df[col], errors='coerce')

    try:
        print("Saving to Parquet...")
        df.to_parquet("ingestion/test_output.parquet", index=False, engine='pyarrow')
        print("Success! Parquet created.")
    except Exception as e:
        print(f"Parquet still failing: {e}")

if __name__ == "__main__":
    main()