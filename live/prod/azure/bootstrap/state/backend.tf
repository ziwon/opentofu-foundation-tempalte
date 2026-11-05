terraform {
  backend "local" {
    path = "../../../../../.infra/state/prod/azure/bootstrap/state/terraform.tfstate"
  }
}
