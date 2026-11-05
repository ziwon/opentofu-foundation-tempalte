terraform {
  backend "local" {
    path = "../../../../../.infra/state/stage/local/foundation/catalog/terraform.tfstate"
  }
}
