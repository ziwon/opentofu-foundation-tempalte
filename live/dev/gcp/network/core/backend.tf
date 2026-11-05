terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_STATE_BUCKET"
    prefix = "dev/gcp/network/core"
  }
}
