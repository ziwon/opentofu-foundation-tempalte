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
run "storage_account" {
  command = plan
  assert {
    condition     = output.resource_id == module.storage_account.id && output.resource_id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example"
    error_message = "The stack must expose the account that the storage-account module manages."
  }
  assert {
    condition     = module.storage_account.container_name == "objects"
    error_message = "Workload blobs must keep the objects container."
  }
  assert {
    condition     = module.storage_account.replication_type == "LRS" && module.storage_account.delete_retention_days == 7
    error_message = "Workload storage must use local replication and keep deleted blobs and containers for 7 days."
  }
  assert {
    condition     = azurerm_resource_group.this.name == "starter-fixture-dev-rg" && azurerm_resource_group.this.location == var.location && azurerm_resource_group.this.tags == tomap(var.context.tags)
    error_message = "The resource group must use the deployment name, location, and context tags."
  }
}

run "short_account_name_is_stable" {
  command = plan
  assert {
    condition     = module.storage_account.name == "starterfixturedevb602d5"
    error_message = "Names that fit without truncation must keep their existing value."
  }
}

run "truncated_dev_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-dev", "tags" : { "project" : "acmeplatform", "environment" : "dev", "managed_by" : "iac" } }
  }
  assert {
    condition     = module.storage_account.name == "acmeplatformstoragf2a1ba"
    error_message = "A truncated name must keep the full deployment identity in its suffix."
  }
}

run "truncated_prod_account_name" {
  command = plan
  variables {
    context = { "id" : "acmeplatform-storage-prod", "tags" : { "project" : "acmeplatform", "environment" : "prod", "managed_by" : "iac" } }
  }
  assert {
    condition     = module.storage_account.name == "acmeplatformstorag9c711f"
    error_message = "Environments in one subscription must not share a truncated name."
  }
}
