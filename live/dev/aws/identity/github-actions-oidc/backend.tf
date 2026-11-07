terraform {
  backend "s3" {
    bucket              = "REPLACE_ME_STATE_BUCKET"
    region              = "us-east-1"
    encrypt             = true
    use_lockfile        = true
    allowed_account_ids = ["000000000000"]
    key                 = "dev/aws/identity/github-actions-oidc/terraform.tfstate"
  }
}
