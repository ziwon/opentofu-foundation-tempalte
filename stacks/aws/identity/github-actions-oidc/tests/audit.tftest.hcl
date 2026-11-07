variables {
  context = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
  roles = {
    deploy = { subjects = ["repo:octo-org/octo-repo:environment:dev"] }
  }
}

mock_provider "aws" {}

run "audit_role_is_opt_in" {
  command = plan
  assert {
    condition     = keys(output.roles) == ["deploy"]
    error_message = "The stack must create no audit role unless audit_subjects is set."
  }
}

run "audit_role_trusts_exact_subject" {
  command = plan
  variables {
    audit_subjects = ["repo:octo-org/octo-repo:environment:security-audit"]
  }
  assert {
    condition     = output.roles.audit.name == "starter-fixture-dev-audit" && output.roles.deploy.name == "starter-fixture-dev-deploy"
    error_message = "The audit role must be named <context.id>-audit and leave the other roles in place."
  }
  assert {
    condition     = toset(local.audit_roles.audit.subjects) == toset(["repo:octo-org/octo-repo:environment:security-audit"]) && length(try(local.audit_roles.audit.subject_patterns, [])) == 0
    error_message = "The audit role must trust only the exact audit subjects, with no prefix patterns."
  }
  assert {
    condition = toset(local.audit_roles.audit.managed_policy_arns) == toset([
      "arn:aws:iam::aws:policy/SecurityAudit",
      "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
    ])
    error_message = "The audit role must attach exactly the SecurityAudit and ViewOnlyAccess managed policies."
  }
  assert {
    condition = length(jsondecode(local.audit_roles.audit.inline_policy_json).Statement) > 0 && alltrue([
      for statement in jsondecode(local.audit_roles.audit.inline_policy_json).Statement : statement.Effect == "Allow" && alltrue([
        for action in statement.Action : can(regex("^[a-z0-9-]+:(Get|List|Describe|BatchGet|Search|Filter)", action)) || action == "apigateway:GET"
      ])
    ])
    error_message = "The audit role's inline additions must allow only read actions."
  }
}

run "audit_key_is_reserved" {
  command = plan
  variables {
    roles          = { audit = { subjects = ["repo:octo-org/octo-repo:environment:dev"] } }
    audit_subjects = ["repo:octo-org/octo-repo:environment:security-audit"]
  }
  expect_failures = [var.audit_subjects]
}
