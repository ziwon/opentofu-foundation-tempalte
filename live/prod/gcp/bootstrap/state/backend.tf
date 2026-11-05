terraform {
  backend "local" {
    path = "../../../../../.infra/state/prod/gcp/bootstrap/state/terraform.tfstate"
  }
}
