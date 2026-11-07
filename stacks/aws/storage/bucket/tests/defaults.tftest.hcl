variables {
  aws_account_id = "000000000000"
  context        = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "aws" {}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = output.resource_id == module.bucket.id && output.deployment_name == var.context.id
    error_message = "The stack must expose its bucket and deployment name."
  }
}
