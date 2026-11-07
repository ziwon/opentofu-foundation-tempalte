output "name" {
  description = "Bucket name."
  value       = google_storage_bucket.this.name
}

output "soft_delete_retention_seconds" {
  description = "Effective soft delete retention in seconds."
  value       = one(google_storage_bucket.this.soft_delete_policy[*].retention_duration_seconds)
}
