terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.location
}


resource "google_storage_bucket" "de-zoomcamp-project-bucket" {
  name          = var.gcs_bucket_name
  storage_class = var.storage_class
  location      = var.location
  force_destroy = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}


resource "google_bigquery_dataset" "de_zoomcamp_project_dataset" {
  dataset_id = var.bq_dataset_name
  location   = var.location
}

# --- New Ingestion Service Account Logic ---

# Create the dedicated Service Account for Python/Kestra ingestion
resource "google_service_account" "ingest_sa" {
  account_id   = var.ingest_sa_id
  display_name = "Weather Ingestion Service Account"
}

# Grant Storage Object Admin ONLY on the specific bucket created above
resource "google_storage_bucket_iam_member" "ingest_role" {
  bucket = google_storage_bucket.de-zoomcamp-project-bucket.name 
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingest_sa.email}"
}

# Create the JSON key for local testing with 'uv'
resource "google_service_account_key" "ingest_key" {
  service_account_id = google_service_account.ingest_sa.name
}

# Output the key so you can decode it locally
output "ingest_sa_key" {
  value     = google_service_account_key.ingest_key.private_key
  sensitive = true
}