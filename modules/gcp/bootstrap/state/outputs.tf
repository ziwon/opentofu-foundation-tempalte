output "backend_config" {
  description = "Backend settings for a workload root; add its explicit state key or prefix."
  value       = { bucket = google_storage_bucket.this.name }
}
