variables {
  context = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
  roles = {
    deploy = { subjects = ["repo:octo-org/octo-repo:environment:dev"] }
    plan   = { subjects = ["repo:octo-org/octo-repo:ref:refs/heads/main"] }
  }
}

mock_provider "aws" {
  mock_resource "aws_iam_openid_connect_provider" {
    defaults = { arn = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com" }
  }
  mock_data "aws_iam_openid_connect_provider" {
    defaults = { arn = "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com" }
  }
}

run "roles_named_from_context" {
  command = plan
  assert {
    condition     = { for key, role in output.roles : key => role.name } == { deploy = "starter-fixture-dev-deploy", plan = "starter-fixture-dev-plan" }
    error_message = "Each role name must be the deployment ID followed by the role key."
  }
  assert {
    condition     = output.oidc_provider_arn == "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com"
    error_message = "The stack must create the provider by default and expose its ARN."
  }
}

run "account_provider_managed_elsewhere" {
  command = plan
  variables {
    create_oidc_provider = false
  }
  assert {
    condition     = output.oidc_provider_arn == "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com"
    error_message = "The stack must trust the account's existing provider when another root manages it."
  }
}
