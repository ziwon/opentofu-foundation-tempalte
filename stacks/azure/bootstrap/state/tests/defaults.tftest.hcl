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
run "backend_config" {
  command = plan
  assert {
    condition     = output.backend_config == { resource_group_name = "starter-fixture-dev-rg", storage_account_name = "starterfixturedevb602d5", container_name = "tfstate", subscription_id = var.subscription_id, use_azuread_auth = true }
    error_message = "Backend settings must name the state resource group, account, and container and use Entra authentication in the selected subscription."
  }
  assert {
    condition     = output.backend_config.storage_account_name == module.storage_account.name
    error_message = "Backend settings must name the account that the storage-account module manages."
  }
  assert {
    condition     = azurerm_resource_group.this.location == var.location && azurerm_resource_group.this.tags == tomap(var.context.tags)
    error_message = "The state resource group must use the selected location and context tags."
  }
  assert {
    condition     = module.storage_account.replication_type == "ZRS" && module.storage_account.delete_retention_days == 30
    error_message = "State storage must use zone replication and keep deleted blobs and containers for 30 days."
  }
}

run "truncated_dev_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-dev", "tags" : { "project" : "acmeplatform", "environment" : "dev", "managed_by" : "iac" } }
  }
  assert {
    condition     = output.backend_config.storage_account_name == "acmeplatformstoragf2a1ba"
    error_message = "A truncated name must keep the full deployment identity in its suffix."
  }
}

run "truncated_prod_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-prod", "tags" : { "project" : "acmeplatform", "environment" : "prod", "managed_by" : "iac" } }
  }
  assert {
    condition     = output.backend_config.storage_account_name == "acmeplatformstorag9c711f"
    error_message = "Environments in one subscription must not share a truncated name."
  }
}
