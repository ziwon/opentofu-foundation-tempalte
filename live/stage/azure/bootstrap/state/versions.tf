terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    azurerm = {
      source  = "registry.opentofu.org/hashicorp/azurerm"
      version = "5.13.0"
    }
  }
}
