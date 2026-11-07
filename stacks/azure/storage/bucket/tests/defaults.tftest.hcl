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

run "short_account_name_is_stable" {
  command = plan
  assert {
    condition     = azurerm_storage_account.this.name == "starterfixturedevb602d5"
    error_message = "Names that fit without truncation must keep their existing value."
  }
}

run "truncated_dev_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-dev", "tags" : { "project" : "acmeplatform", "environment" : "dev", "managed_by" : "iac" } }
  }
  assert {
    condition     = azurerm_storage_account.this.name == "acmeplatformstoragf2a1ba"
    error_message = "A truncated name must keep the full deployment identity in its suffix."
  }
}

run "truncated_prod_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-prod", "tags" : { "project" : "acmeplatform", "environment" : "prod", "managed_by" : "iac" } }
  }
  assert {
    condition     = azurerm_storage_account.this.name == "acmeplatformstorag9c711f"
    error_message = "Environments in one subscription must not share a truncated name."
  }
}
