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
output "replication_type" {
  description = "Planned account replication type."
  value       = azurerm_storage_account.this.account_replication_type
}
output "delete_retention_days" {
  description = "Planned retention for deleted blobs."
  value       = one(one(azurerm_storage_account.this.blob_properties).delete_retention_policy).days
}
