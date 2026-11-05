terraform {
  backend "local" {
    path = "../../../../../.infra/state/stage/aws/bootstrap/state/terraform.tfstate"
  }
}
