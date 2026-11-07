variables {
  region     = "us-central1"
  project_id = "example-project"
  context    = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "google" {}
run "workload_bucket" {
  command = plan
  assert {
    condition     = output.resource_id == "starter-fixture-dev-example-project" && output.resource_id == module.bucket.name
    error_message = "Export the core module's bucket name, derived from the deployment and project."
  }
  assert {
    condition     = output.deployment_name == var.context.id
    error_message = "Export the deployment name."
  }
}
