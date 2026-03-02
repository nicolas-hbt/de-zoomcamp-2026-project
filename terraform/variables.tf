variable "project" {
  type        = string
  description = "GCP project ID"
  default     = "de-zoomcamp-project-488915"
}

variable "location" {
  type        = string
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default     = "europe-west1"
}

variable "storage_class" {
  type        = string
  description = "The Storage Class of the new bucket. Ref: https://cloud.google.com/storage/docs/storage-classes"
  default     = "STANDARD"
}

variable "bq_dataset_name" {
  type        = string
  description = "Dataset in BigQuery where raw data (from Google Cloud Storage) will be loaded."
  default     = "city_weather_dataset"
}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  default     = "de-zoomcamp-project-terra-bucket"
}

# For ingestion service account
variable "ingest_sa_id" {
  description = "ID for the ingestion service account"
  type        = string
  default     = "weather-data-ingest"
}

variable "credentials" {
  description = "My Credentials"
  default     = "keys/my-gcp-key.json" 
}