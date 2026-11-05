terraform {
  backend "local" {
    path = "../../../../../.infra/state/dev/aws/bootstrap/state/terraform.tfstate"
  }
}
