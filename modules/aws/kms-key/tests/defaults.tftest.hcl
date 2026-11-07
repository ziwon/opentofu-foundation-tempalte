variables {
  description = "Encrypt objects for starter-fixture-dev"
}

mock_provider "aws" {}
run "rotating_key" {
  command = plan
  assert {
    condition     = aws_kms_key.this.enable_key_rotation && aws_kms_key.this.deletion_window_in_days == 30
    error_message = "The key must rotate and keep the 30-day deletion window."
  }
  assert {
    condition     = aws_kms_key.this.description == "Encrypt objects for starter-fixture-dev"
    error_message = "The key must use the supplied description."
  }
  assert {
    condition     = output.arn == aws_kms_key.this.arn
    error_message = "The module must expose the key ARN for encryption settings."
  }
}
