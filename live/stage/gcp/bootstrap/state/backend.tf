terraform {
  backend "local" {
    path = "../../../../../.infra/state/stage/gcp/bootstrap/state/terraform.tfstate"
  }
}
