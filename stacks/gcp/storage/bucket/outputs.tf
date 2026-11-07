output "resource_id" {
  description = "Provider identifier for the stack's primary resource."
  value       = module.bucket.name
}
output "deployment_name" {
  description = "Stable resource name for this deployment."
  value       = var.context.id
}
