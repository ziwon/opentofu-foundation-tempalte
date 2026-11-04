terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    google = {
      source  = "registry.opentofu.org/hashicorp/google"
      version = "= 8.9.0"
    }
  }
}
