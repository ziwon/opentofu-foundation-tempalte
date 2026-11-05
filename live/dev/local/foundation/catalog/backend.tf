terraform {
  backend "local" {
    path = "../../../../../.infra/state/dev/local/foundation/catalog/terraform.tfstate"
  }
}
