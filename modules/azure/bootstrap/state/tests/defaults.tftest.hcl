variables {
  location           = "eastus"
  subscription_id    = "00000000-0000-0000-0000-000000000000"
  allowed_ip_ranges  = []
  allowed_subnet_ids = []
  context            = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "azurerm" {
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example" }
  }
}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = azurerm_storage_account.this.network_rules[0].default_action == "Deny" && azurerm_storage_account.this.blob_properties[0].delete_retention_policy[0].days == 30 && azurerm_storage_account.this.account_replication_type == "ZRS"
    error_message = "State must restrict network access, retain deleted blobs for 30 days, and use zone replication."
  }
  assert {
    condition     = output.backend_config.use_azuread_auth && output.backend_config.subscription_id == var.subscription_id
    error_message = "Backend settings must use Entra authentication in the selected subscription."
  }
  assert {
    condition     = !azurerm_storage_account.this.allow_nested_items_to_be_public && !azurerm_storage_account.this.shared_access_key_enabled && azurerm_storage_container.this.container_access_type == "private"
    error_message = "Storage must use private containers and identity-based access."
  }
  assert {
    condition     = azurerm_storage_account.this.blob_properties[0].versioning_enabled && azurerm_storage_account.this.https_traffic_only_enabled
    error_message = "Blob versions and HTTPS must remain enabled."
  }
}
