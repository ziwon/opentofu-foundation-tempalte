terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "prod/gcp/storage/bucket"
  }
}
