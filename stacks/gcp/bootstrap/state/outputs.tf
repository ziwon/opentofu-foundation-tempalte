output "backend_config" {
  description = "Copy this non-secret object to a regular deployment's backend.json; prefixes are derived by the runner."
  value       = { bucket = google_storage_bucket.this.name }
}
