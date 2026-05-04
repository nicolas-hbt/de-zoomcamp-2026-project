# 🌦️ City Weather Pipeline — DE Zoomcamp 2026 Project
A production-grade, end-to-end data engineering pipeline that ingests real-time and historical weather data for multiple cities, stores it in Google Cloud Storage (GCS) and BigQuery, transforms it with dbt, and makes it available for analytics — all orchestrated with Kestra, provisioned with Terraform, and containerized with Docker.

---

## Table of Contents

1. [Problem Description](#1-problem-description)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Prerequisites](#5-prerequisites)
6. [Setup Instructions](#6-setup-instructions)
7. [Running the Pipeline](#7-running-the-pipeline)
8. [Pipeline Execution Details](#8-pipeline-execution-details)
9. [dbt Transformation Layers](#9-dbt-transformation-layers)
10. [Running Tests & Validation](#10-running-tests--validation)
11. [Data Visualization](#11-data-visualization)

---

## 1. Problem Description

### The Challenge

Real-world weather data is often scattered across the internet in various formats and requires significant preprocessing before it can be analyzed. Organizations need a reliable, automated way to:

1. **Source data** from external APIs and file repositories
2. **Extract and clean** messy data with inconsistent formatting
3. **Store it efficiently** with partitioning and clustering for query optimization
4. **Transform it systematically** following data engineering best practices (Bronze → Silver → Gold layers)
5. **Run data quality checks** to ensure reliability and trust in the data
6. **Orchestrate the entire workflow** on a schedule with monitoring and alerting capabilities

This project demonstrates a production-ready solution for weather data ingestion and transformation, showcasing best practices in the modern data stack (dbt, Kestra, BigQuery, Google Cloud Storage, and Terraform).

### What This Project Solves

- **Automated Data Ingestion**: Downloads city temperature data daily from an external XLSX source
- **Cloud-Native Storage**: Stores raw data in Google Cloud Storage with proper partitioning and formats
- **Data Transformation**: Implements a medallion architecture (Raw → Silver → Gold) for data quality and analytics
- **Orchestration**: Uses Kestra to schedule and monitor the pipeline with automatic retries
- **Infrastructure as Code**: Automates GCP resource provisioning with Terraform
- **Data Quality**: Uses dbt tests to validate data at each transformation layer

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│         (External XLSX - fetchseries.com)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Kestra Orchestration                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 1. Ingest Task (Python Script)                       │  │
│  │    - Downloads XLSX data                              │  │
│  │    - Cleans & unpivots data                           │  │
│  │    - Uploads Parquet to GCS (raw/climate/)           │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 2. BigQuery Update Task (SQL)                        │  │
│  │    - Creates external table from GCS                  │  │
│  │    - Merges into partitioned/clustered table         │  │
│  └───────────────────────────────────────────────────────┘  │
│  Scheduled: Daily at 7:00 AM UTC                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Google Cloud Storage (Raw Layer)                    │
│  gs://bucket/raw/climate/*.parquet                          │
│  ├─ Partitioned by: date                                   │
│  └─ Format: Parquet (columnar, compressed)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│      BigQuery Warehouse (Optimized Raw Table)              │
│  PROJECT.DATASET.city_weather_optimized                    │
│  ├─ Partitioned by: DATE(date)                             │
│  ├─ Clustered by: country, city                            │
│  └─ Strategy: MERGE for efficient incremental updates      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           dbt Transformation (Silver & Gold)                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ SILVER LAYER: stg_weather                          │  │
│  │ - Source: city_weather_optimized                   │  │
│  │ - Cleaning: Remove nulls, deduplication            │  │
│  │ - Conversions: Celsius → Fahrenheit                │  │
│  │ - Tests: not_null, duplicate detection             │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ GOLD LAYER: fct_monthly_city_stats                 │  │
│  │ - Aggregation: Monthly statistics per city          │  │
│  │ - Partitioning: By month_start_date                │  │
│  │ - Clustering: By country, city                      │  │
│  │ - Tests: not_null, accepted_range validations      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

# 3. Tech Stack

| Layer | Tool                        |
|---|-----------------------------|
| Infrastructure as Code | Terraform                   |
| Cloud Provider | Google Cloud Platform (GCP) |
| Data Lake | Google Cloud Storage (GCS)  |
| Data Warehouse | BigQuery                    |
| Orchestration | Kestra                      |
| Containerization | Docker + Docker Compose     |
| Ingestion | Python                      |
| Transformation | dbt (dbt Core)              |
| Visualization | Looker Studio                         |

---

## 4. Project Structure

```
de-zoomcamp-2026-project/
├── README.md                          # This file
├── docker-compose.yml                 # Kestra container setup
├── .env_encoded                       # GCP credentials
│
├── terraform/                         # Infrastructure as Code
│   ├── main.tf                        # Resource definitions (GCS, BigQuery, IAM)
│   ├── variables.tf                   # Configuration variables
│   └── keys/                          # GCP service account credentials
│
├── kestra/                            
│   └── flows/                         # Kestra YAML flow definition
│       └── ingest_city_weather.yaml   # Main pipeline (ingestion + BigQuery)
│
├── city_weather_dbt/                  # dbt transformation project
│   ├── dbt_project.yml                # dbt project configuration
│   ├── models/
│   │   ├── stg_weather.sql           # Silver layer
│   │   ├── fct_monthly_city_stats.sql # Gold layer
│   │   ├── schema.yml                 # Data quality tests
│   │   └── sources.yml                # Source table definitions
│   ├── packages.yml                   # dbt dependencies (dbt-utils)
│
├── ingestion/                         # Legacy ingestion scripts
│   └── ingest_script.py               # Python ingestion logic (referenced by Kestra)
```

---

## 5. Prerequisites

### System Requirements
- Docker & Docker Compose (for Kestra local development)
- Python 3.11+ (for local development)
- Git (for version control)
- curl or similar HTTP client (for testing)

### Cloud Requirements
- Google Cloud Project (with billing enabled)
- Service Account with appropriate IAM roles (created automatically by Terraform)
- GCP credentials file (JSON key)

### Software Versions
- Kestra: latest-full
- dbt-core: 1.x
- Python: 3.11+
- Terraform: 5.6.0+ (Google provider)

---

## 6. Setup Instructions

### 1. Clone and Prepare the Repository

### 2. GCP Setup with Terraform

#### Step 2a: Create GCP Service Account & Credentials

#### Step 2b: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan the deployment (review resources)
terraform plan

# Apply the configuration (creates GCS bucket, BigQuery dataset, service accounts)
terraform apply
```

**Resources Created:**
- **Google Cloud Storage Bucket**: `de-zoomcamp-project-terra-bucket`
  - Storage Class: STANDARD (regional, cost-optimized)
  - Location: europe-west1
  - Auto-cleanup: Aborts incomplete multipart uploads after 1 day

- **BigQuery Dataset**: `city_weather_dataset`
  - Location: europe-west1
  - Contains raw and transformed tables

- **Service Account**: `weather-data-ingest@PROJECT_ID.iam.gserviceaccount.com`
  - Permissions: `roles/storage.objectAdmin` on GCS bucket only
  - Used by Kestra for secure data ingestion

### 3. Environment Configuration

#### Step 3a: Create `.env_encoded` for Kestra Secrets

The `.env_encoded` file is already committed with GCP credentials.

#### Step 3b: Configure Kestra Key-Value Pairs

SCREENSHOT HERE # TODO

When you start Kestra (see Step 4), add these Key-Value pairs in the UI at http://localhost:8080:

1. **GCP_PROJECT_ID**: `de-zoomcamp-project-488915`
2. **GCP_BUCKET_NAME**: `de-zoomcamp-project-terra-bucket`
3. **GCP_DATASET**: `city_weather_dataset`
4. **GCP_LOCATION**: `europe-west1`

### 4. Start Kestra Locally

```bash
docker-compose up -d

# Access Kestra UI
open http://localhost:8080
```

**First-time setup in Kestra UI:**
1. Navigate to **Namespace** → Click into `company.data.weather`
2. Go to **KV Store** (Key-Value store)
3. Add the four keys from Step 3b above
4. Go to **Secrets** tab
5. Verify `GCP_SERVICE_ACCOUNT` is populated from `.env_encoded`

### 5. Deploy dbt Project

```bash
cd city_weather_dbt

# Install dbt and dependencies
pip install dbt-bigquery

# Create profiles.yml for BigQuery connection
cat > ~/.dbt/profiles.yml << EOF
city_weather_dbt:
  target: prod
  outputs:
    prod:
      type: bigquery
      project: de-zoomcamp-project-488915
      dataset: city_weather_dataset
      method: service-account-json
      keyfile: /path/to/keys/my-gcp-key.json
      threads: 4
      timeout_seconds: 300
      location: europe-west1
      priority: interactive
      retries: 1
EOF

# Test the connection
dbt debug

# Install dbt packages (dbt-utils for custom tests)
dbt deps

# Run dbt models (creates views and tables)
dbt run

# Run data quality tests
dbt test

# View test results
dbt docs generate
dbt docs serve --port 8001 # if 8080 is used by Kestra. 
# Then you can check docs at http://localhost:8001
```

---

## 7. Running the Pipeline

1. Go to http://localhost:8080
2. Navigate to Flows → Click "+ New Flow"
3. Copy and paste the content of `kestra/flows/ingest_city_weather.yaml` into the editor
4. Click **Execute** button
5. Monitor execution in real-time
6. Check logs for each task
7. Go into BigQuery console to verify data is ingested and tables are updated

```yaml
triggers:
  - id: daily_7am
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 7 * * *"
```

To modify the schedule, edit the cron expression in the Kestra flow.

---

## 8. Pipeline Execution Details

### Task 1: Ingest Data to GCS

**What it does:**
1. Downloads XLSX file from https://www.fetchseries.com/climate/average-city-temperatures-fsr/average-city-temperatures-fsr.xlsx
2. Parses the Excel file using pandas and openpyxl
3. Unpivots data from wide to long format
4. Extracts city and country from concatenated location strings
5. Filters to only records from 2020 onwards
6. Removes rows with null values in key columns
7. Uploads to GCS as Parquet (columnar format for efficiency)

**Input:** External XLSX from fetchseries.com

**Output:** `gs://de-zoomcamp-project-terra-bucket/raw/climate/{DATE}_weather.parquet`

**Format:** Parquet (Apache columnar format)

**Compression:** Snappy (default, balanced speed/ratio)

**Sample Data After Processing:**
```
date	city	country	avg_temp
2025-03-22 00:00:00 UTC	Farah	Afghanistan	23.61
2025-03-22 00:00:00 UTC	Herat	Afghanistan	18.57
2025-03-22 00:00:00 UTC	Jalalabad	Afghanistan	17.86
```

### Task 2: Update BigQuery

This task runs three SQL statements:

#### 2a. Create External Table
```sql
CREATE OR REPLACE EXTERNAL TABLE `PROJECT.DATASET.ext_weather`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://BUCKET/raw/climate/*.parquet']
);
```
- References all Parquet files in GCS
- Updated daily to include new data
- No data copied; queries read directly from GCS

#### 2b. Create Optimized Table (if not exists)
```sql
CREATE TABLE IF NOT EXISTS `PROJECT.DATASET.city_weather_optimized`
(
  date TIMESTAMP,
  city STRING,
  country STRING,
  avg_temp FLOAT64
)
PARTITION BY DATE(date)
CLUSTER BY country, city;
```
- **Partitioning**: Splits table by date for faster filtering and lower query costs
- **Clustering**: Orders data by country and city for faster lookups on these dimensions
- **Cost Optimization**: Queries on partitions/clusters avoid scanning entire table

#### 2c. Merge Data (Incremental Load)
```sql
MERGE INTO `PROJECT.DATASET.city_weather_optimized` T
USING `PROJECT.DATASET.ext_weather` S
ON T.date = S.date AND T.city = S.city AND T.country = S.country
WHEN NOT MATCHED THEN
  INSERT (date, city, country, avg_temp)
  VALUES (S.date, S.city, S.country, S.avg_temp);
```
- **Why MERGE?** Prevents duplicate rows when re-running the pipeline
- **Incremental Load**: Only inserts new rows not already in the table
- **Idempotent**: Safe to run multiple times without side effects

---

## 9. dbt Transformation Layers

### Silver Layer: `stg_weather`

**Purpose**: Clean and standardize raw data

**Materialization**: View (no storage overhead)

**Location**: `city_weather_dataset.stg_weather`

**Transformations:**
- Converts temperature from Celsius to Fahrenheit
- Removes null values
- Deduplicates records (keeps first occurrence by date)

**Data Quality Tests:**
- `not_null` on `date` and `city`
- Ensures data integrity before gold layer aggregation

### Gold Layer: `fct_monthly_city_stats`

**Purpose**: Aggregate data for analytics and reporting
**Materialization**: Table (partitioned and clustered)
**Location**: `city_weather_dataset.fct_monthly_city_stats`

**Aggregations:**
- Monthly average temperature (Celsius & Fahrenheit)
- Minimum and maximum temperatures per month
- Count of days recorded

**Data Quality Tests:**
- `not_null` on monthly_avg_temp_c
- `accepted_range` (-60 to 60°C) - catches impossible temperatures

**Performance Optimization:**
- Partitioned by month for faster time-series queries
- Clustered by country and city for geographic filtering

---

## 10. Running Tests & Validation

### Execute dbt Tests

```bash
cd city_weather_dbt

# Run all tests
dbt test

# Run tests for a specific model
dbt test --select stg_weather
```

### View Generated dbt Documentation

```bash
dbt docs generate
dbt docs serve --port 8001
# Open http://localhost:8001 in your browser
```

---

## 11. Data Visualization

Link to the Looker Studio visualization: https://lookerstudio.google.com/u/2/reporting/5bb4e362-83c4-4b2b-a554-480a7a4071c5/page/hNTsF

WARNING: there is a bug with temperatures in C and F grad -- both way above what they should be. My gut feeling is that temperatures in Celsius are actually in Fahrenheit, and that temperatures in Fahrenheit are converted to Fahrenheit from Celsius twice, i.e. after applying another layer of Celsius -> Fahrenheit conversion).


<img width="1156" height="803" alt="image" src="https://github.com/user-attachments/assets/aef6de7b-59e8-4469-a950-bf1bb49fa688" />
