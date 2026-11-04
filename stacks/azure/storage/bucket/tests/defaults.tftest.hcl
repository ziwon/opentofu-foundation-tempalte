mock_provider "azurerm" {
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example" }
  }
}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = azurerm_storage_account.this.network_rules[0].default_action == "Deny"
    error_message = "Storage must deny clients outside explicit network rules."
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
