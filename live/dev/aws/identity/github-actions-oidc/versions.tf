terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "registry.opentofu.org/hashicorp/aws"
      version = "6.72.0"
    }
  }
}
