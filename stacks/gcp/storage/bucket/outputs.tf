output "resource_id" {
  description = "Provider identifier for the stack's primary resource."
  value       = google_storage_bucket.this.name
}
output "deployment_name" {
  description = "Stable resource name for this deployment."
  value       = module.context.id
}
