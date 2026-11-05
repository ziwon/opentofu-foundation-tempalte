terraform {
  backend "azurerm" {
    resource_group_name  = "REPLACE_ME_STATE_RG"
    storage_account_name = "REPLACE_ME_STATE_ACCOUNT"
    container_name       = "tfstate"
    subscription_id      = "REPLACE_ME_SUBSCRIPTION_ID"
    use_azuread_auth     = true
    key                  = "dev/azure/storage/bucket/terraform.tfstate"
  }
}
