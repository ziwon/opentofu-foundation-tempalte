output "id" {
  description = "Storage account resource ID."
  value       = azurerm_storage_account.this.id
}
output "name" {
  description = "Storage account name."
  value       = azurerm_storage_account.this.name
}
output "container_name" {
  description = "Private Blob container name."
  value       = azurerm_storage_container.this.name
}
