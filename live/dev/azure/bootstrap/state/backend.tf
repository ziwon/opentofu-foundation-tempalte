terraform {
  backend "local" {
    path = "../../../../../.infra/state/dev/azure/bootstrap/state/terraform.tfstate"
  }
}
