output "catalog" {
  description = "Local catalog entry; no cloud resources are created."
  value       = terraform_data.catalog.output
}
output "deployment_name" {
  description = "Name scoped to the deployment environment."
  value       = var.context.id
}
