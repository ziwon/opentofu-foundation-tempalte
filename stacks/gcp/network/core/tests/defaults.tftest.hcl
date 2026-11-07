variables {
  region      = "us-central1"
  subnet_cidr = "10.10.1.0/24"
  context     = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "google" {}
run "deployment_network" {
  command = plan
  assert {
    condition     = module.network.network_name == var.context.id && output.resource_id == module.network.network_id
    error_message = "Name the network after the deployment and export its identifier."
  }
  assert {
    condition     = output.deployment_name == var.context.id
    error_message = "Export the deployment name."
  }
}
