output "backend_config" {
  description = "Backend settings for a workload root; add its explicit state key or prefix."
  value = {
    resource_group_name  = azurerm_resource_group.this.name
    storage_account_name = module.storage_account.name
    container_name       = module.storage_account.container_name
    subscription_id      = var.subscription_id
    use_azuread_auth     = true
  }
}
