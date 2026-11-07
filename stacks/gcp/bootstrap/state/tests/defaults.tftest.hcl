variables {
  region     = "us-central1"
  project_id = "example-project"
  context    = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "google" {}
run "state_bucket" {
  command = plan
  assert {
    condition     = output.backend_config == { bucket = "starter-fixture-dev-example-project" }
    error_message = "Export only the state bucket name, derived from the deployment and project."
  }
  assert {
    condition     = module.bucket.soft_delete_retention_seconds == 2592000
    error_message = "Retain deleted state for 30 days."
  }
}
