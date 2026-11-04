output "backend_config" {
  description = "Copy this non-secret object to a regular deployment's backend.json; keys are derived by the runner."
  value = {
    resource_group_name  = azurerm_resource_group.this.name
    storage_account_name = azurerm_storage_account.this.name
    container_name       = azurerm_storage_container.this.name
    subscription_id      = var.subscription_id
    use_azuread_auth     = true
  }
}
