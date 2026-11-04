plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

# The runner enables only the selected deployment's cloud plugin.
plugin "aws" {
  enabled = false
  version = "0.50.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

plugin "azurerm" {
  enabled = false
  version = "0.33.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}

plugin "google" {
  enabled = false
  version = "0.41.0"
  source  = "github.com/terraform-linters/tflint-ruleset-google"
}
