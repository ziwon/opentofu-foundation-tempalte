terraform {
  backend "local" {
    path = "../../../../../.infra/state/prod/local/foundation/catalog/terraform.tfstate"
  }
}
