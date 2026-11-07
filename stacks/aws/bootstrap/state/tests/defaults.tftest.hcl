variables {
  region         = "us-east-1"
  aws_account_id = "000000000000"
  context        = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "aws" {}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = output.backend_config.bucket == module.bucket.id && output.backend_config.kms_key_id == module.key.arn
    error_message = "Generated backend settings must name the state bucket and its encryption key."
  }
  assert {
    condition     = output.backend_config.encrypt && output.backend_config.use_lockfile && output.backend_config.allowed_account_ids == [var.aws_account_id] && output.backend_config.region == var.region
    error_message = "Generated backend settings must require encryption, native locking, the expected account, and the region."
  }
}
