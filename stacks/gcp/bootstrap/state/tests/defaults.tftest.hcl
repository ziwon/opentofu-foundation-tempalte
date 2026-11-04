mock_provider "google" {}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = google_storage_bucket.this.soft_delete_policy[0].retention_duration_seconds == 2592000 && output.backend_config.bucket == google_storage_bucket.this.name
    error_message = "Retain deleted state for 30 days and export the correct bucket."
  }
  assert {
    condition     = google_storage_bucket.this.uniform_bucket_level_access && google_storage_bucket.this.public_access_prevention == "enforced"
    error_message = "Public access must be prevented and access controlled by IAM."
  }
  assert {
    condition     = google_storage_bucket.this.versioning[0].enabled && !google_storage_bucket.this.force_destroy
    error_message = "Retain object versions and refuse deletion of nonempty buckets."
  }
}
