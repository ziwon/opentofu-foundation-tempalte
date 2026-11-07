locals {
  compact_id = replace(var.context.id, "-", "")
  # Keep existing names when nothing is truncated; otherwise hash the full ID so environments stay distinct.
  account_suffix = sha1(length(local.compact_id) > 18 ? "${var.subscription_id}/${var.context.id}" : var.subscription_id)
}

resource "azurerm_resource_group" "this" {
  name     = "${var.context.id}-rg"
  location = var.location
  tags     = var.context.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_storage_account" "this" {
  name                            = "${substr(local.compact_id, 0, 18)}${substr(local.account_suffix, 0, 6)}"
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  tags                            = var.context.tags
  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = var.allowed_subnet_ids
  }
  lifecycle { prevent_destroy = true }
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 30 }
    container_delete_retention_policy { days = 30 }
  }
}
resource "azurerm_storage_container" "this" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
  lifecycle { prevent_destroy = true }
}
