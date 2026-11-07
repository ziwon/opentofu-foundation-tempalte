variables {
  name_base             = "starter-fixture-dev"
  subscription_id       = "00000000-0000-0000-0000-000000000000"
  resource_group_name   = "starter-fixture-dev-rg"
  location              = "eastus"
  replication_type      = "ZRS"
  delete_retention_days = 30
  container_name        = "tfstate"
  allowed_ip_ranges     = ["203.0.113.10"]
  allowed_subnet_ids    = ["/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example/subnets/private"]
  tags                  = { "project" : "starter", "environment" : "dev", "managed_by" : "iac" }
}

mock_provider "azurerm" {
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example" }
  }
}

run "private_versioned_storage" {
  command = plan
  assert {
    condition     = azurerm_storage_account.this.network_rules[0].default_action == "Deny" && azurerm_storage_account.this.network_rules[0].bypass == toset(["AzureServices"])
    error_message = "Storage must deny clients outside explicit network rules and let trusted Azure services bypass."
  }
  assert {
    condition     = azurerm_storage_account.this.network_rules[0].ip_rules == toset(var.allowed_ip_ranges) && azurerm_storage_account.this.network_rules[0].virtual_network_subnet_ids == toset(var.allowed_subnet_ids)
    error_message = "Storage must allow exactly the supplied IP ranges and subnets."
  }
  assert {
    condition     = !azurerm_storage_account.this.allow_nested_items_to_be_public && !azurerm_storage_account.this.shared_access_key_enabled && azurerm_storage_account.this.default_to_oauth_authentication && azurerm_storage_container.this.container_access_type == "private"
    error_message = "Storage must use private containers and identity-based access."
  }
  assert {
    condition     = azurerm_storage_account.this.blob_properties[0].versioning_enabled && azurerm_storage_account.this.https_traffic_only_enabled && azurerm_storage_account.this.min_tls_version == "TLS1_2"
    error_message = "Blob versions, HTTPS, and TLS 1.2 must remain enabled."
  }
  assert {
    condition     = azurerm_storage_account.this.account_replication_type == "ZRS" && azurerm_storage_account.this.blob_properties[0].delete_retention_policy[0].days == 30 && azurerm_storage_account.this.blob_properties[0].container_delete_retention_policy[0].days == 30
    error_message = "Replication and blob and container soft deletion must follow the inputs."
  }
  assert {
    condition     = azurerm_storage_account.this.resource_group_name == var.resource_group_name && azurerm_storage_account.this.location == var.location && azurerm_storage_account.this.tags == tomap(var.tags)
    error_message = "The account must use the supplied resource group, location, and tags."
  }
  assert {
    condition     = output.container_name == "tfstate" && output.id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example"
    error_message = "Outputs must name the container and identify the account."
  }
}

run "workload_settings" {
  command = plan
  variables {
    replication_type      = "LRS"
    delete_retention_days = 7
    container_name        = "objects"
  }
  assert {
    condition     = azurerm_storage_account.this.account_replication_type == "LRS" && azurerm_storage_account.this.blob_properties[0].delete_retention_policy[0].days == 7 && azurerm_storage_account.this.blob_properties[0].container_delete_retention_policy[0].days == 7 && azurerm_storage_container.this.name == "objects"
    error_message = "Replication, soft deletion, and the container name must follow the inputs."
  }
}

run "short_account_name_is_stable" {
  command = plan
  assert {
    condition     = output.name == "starterfixturedevb602d5"
    error_message = "Names that fit without truncation must keep their existing value."
  }
}

run "truncated_dev_account_name" {
  command = plan
  variables {
    name_base = "acmeplatform-storage-dev"
  }
  assert {
    condition     = output.name == "acmeplatformstoragf2a1ba"
    error_message = "A truncated name must keep the full deployment identity in its suffix."
  }
}

run "truncated_prod_account_name" {
  command = plan
  variables {
    name_base = "acmeplatform-storage-prod"
  }
  assert {
    condition     = output.name == "acmeplatformstorag9c711f"
    error_message = "Environments in one subscription must not share a truncated name."
  }
}
