module "naming" {
  source      = "../../../../modules/naming"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
}

resource "azurerm_resource_group" "this" {
  name     = "${module.naming.id}-rg"
  location = var.location
  tags     = module.naming.tags
}
resource "azurerm_storage_account" "this" {
  lifecycle { prevent_destroy = true }
  name                            = "${substr(replace(module.naming.id, "-", ""), 0, 18)}${substr(sha1(var.subscription_id), 0, 6)}"
  resource_group_name             = azurerm_resource_group.this.name
  location                        = azurerm_resource_group.this.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  tags                            = module.naming.tags
  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = var.allowed_subnet_ids
  }
  blob_properties {
    versioning_enabled = true
    delete_retention_policy { days = 7 }
    container_delete_retention_policy { days = 7 }
  }
}
resource "azurerm_storage_container" "this" {
  lifecycle { prevent_destroy = true }
  name                  = "objects"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
