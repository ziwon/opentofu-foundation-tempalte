resource "azurerm_resource_group" "this" {
  name     = "${module.context.id}-rg"
  location = var.location
  tags     = module.context.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_storage_account" "this" {
  name                            = "${substr(replace(module.context.id, "-", ""), 0, 18)}${substr(sha1(var.subscription_id), 0, 6)}"
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "ZRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  tags                            = module.context.tags
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
