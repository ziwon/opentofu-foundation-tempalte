variables {
  network_cidr = "10.10.0.0/16"
  subnet_cidr  = "10.10.1.0/24"
  context      = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "aws" {}
run "private_network" {
  command = plan
  assert {
    condition     = output.resource_id == module.vpc.id && output.deployment_name == var.context.id
    error_message = "The stack must expose its VPC and deployment name."
  }
  assert {
    condition     = module.vpc.network_cidr == "10.10.0.0/16" && module.vpc.subnet_cidr == "10.10.1.0/24"
    error_message = "The network and private subnet must use network_cidr and subnet_cidr."
  }
}
