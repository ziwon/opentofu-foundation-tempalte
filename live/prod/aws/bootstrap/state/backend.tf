terraform {
  backend "local" {
    path = "../../../../../.infra/state/prod/aws/bootstrap/state/terraform.tfstate"
  }
}
