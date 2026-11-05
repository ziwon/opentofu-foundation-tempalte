output "catalog" {
  description = "Local catalog entry; no cloud resources are created."
  value       = module.stack.catalog
}
output "deployment_name" {
  description = "Name scoped to the deployment environment."
  value       = module.context.id
}
