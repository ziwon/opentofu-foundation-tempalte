output "resource_id" {
  description = "Provider identifier for the stack's primary resource."
  value       = module.network.network_id
}
output "deployment_name" {
  description = "Stable resource name for this deployment."
  value       = var.context.id
}
