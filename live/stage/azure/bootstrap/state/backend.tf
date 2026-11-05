terraform {
  backend "local" {
    path = "../../../../../.infra/state/stage/azure/bootstrap/state/terraform.tfstate"
  }
}
