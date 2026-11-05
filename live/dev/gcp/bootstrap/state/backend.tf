terraform {
  backend "local" {
    path = "../../../../../.infra/state/dev/gcp/bootstrap/state/terraform.tfstate"
  }
}
