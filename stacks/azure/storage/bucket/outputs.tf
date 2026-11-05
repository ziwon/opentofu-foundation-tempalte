output "resource_id" {
  description = "Provider identifier for the stack's primary resource."
  value       = azurerm_storage_account.this.id
}
output "deployment_name" {
  description = "Stable resource name for this deployment."
  value       = module.context.id
}
