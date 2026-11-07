variables {
  roles = {
    deploy = {
      name = "starter-fixture-dev-deploy"
      subjects = [
        "repo:octo-org/octo-repo:environment:dev",
        "repo:octo-org/octo-repo:ref:refs/heads/main",
      ]
      managed_policy_arns  = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
      inline_policy_json   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"s3:ListBucket\",\"Resource\":\"arn:aws:s3:::starter-fixture\"}]}"
      max_session_duration = 7200
      permissions_boundary = "arn:aws:iam::000000000000:policy/github-actions-boundary"
    }
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

run "exact_subject_trust" {
  command = plan
  assert {
    condition     = one(aws_iam_openid_connect_provider.github).url == "https://token.actions.githubusercontent.com" && one(aws_iam_openid_connect_provider.github).client_id_list == toset(["sts.amazonaws.com"])
    error_message = "The module must create the GitHub Actions OIDC provider for the STS audience."
  }
  assert {
    condition = jsondecode(aws_iam_role.this["deploy"].assume_role_policy) == {
      Version = "2012-10-17"
      Statement = [{
        Effect    = "Allow"
        Principal = { Federated = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com" }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = ["repo:octo-org/octo-repo:environment:dev", "repo:octo-org/octo-repo:ref:refs/heads/main"]
          }
        }
      }]
    }
    error_message = "The trust policy must federate the created provider and match aud and the exact subjects with StringEquals."
  }
  assert {
    condition     = aws_iam_role.this["deploy"].name == "starter-fixture-dev-deploy" && aws_iam_role.this["deploy"].max_session_duration == 7200 && aws_iam_role.this["deploy"].permissions_boundary == "arn:aws:iam::000000000000:policy/github-actions-boundary"
    error_message = "The role must use the supplied name, session limit, and permissions boundary."
  }
  assert {
    condition     = [for attachment in values(aws_iam_role_policy_attachment.this) : [attachment.role, attachment.policy_arn]] == [["starter-fixture-dev-deploy", "arn:aws:iam::aws:policy/ReadOnlyAccess"]]
    error_message = "Each managed policy ARN must be attached to its role."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.this["deploy"].policy) == jsondecode(var.roles.deploy.inline_policy_json) && aws_iam_role_policy.this["deploy"].role == "starter-fixture-dev-deploy"
    error_message = "The inline policy must be attached to its role unchanged."
  }
  assert {
    condition     = output.oidc_provider_arn == "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com" && output.roles.deploy.name == "starter-fixture-dev-deploy" && output.roles.deploy.arn == aws_iam_role.this["deploy"].arn
    error_message = "The module must expose the provider ARN and each role's ARN and name."
  }
}

run "defaults_grant_nothing_extra" {
  command = plan
  variables {
    roles = {
      deploy = {
        name     = "starter-fixture-dev-deploy"
        subjects = ["repo:octo-org/octo-repo:ref:refs/tags/v1.0.0"]
      }
    }
  }
  assert {
    condition     = aws_iam_role.this["deploy"].max_session_duration == 3600 && aws_iam_role.this["deploy"].permissions_boundary == null
    error_message = "A role must default to a one-hour session and no permissions boundary."
  }
  assert {
    condition     = length(aws_iam_role_policy_attachment.this) == 0 && length(aws_iam_role_policy.this) == 0
    error_message = "A role without policies must receive no attachments or inline policy."
  }
}

run "prefix_patterns_are_opt_in" {
  command = plan
  variables {
    roles = {
      release = {
        name             = "starter-fixture-dev-release"
        subjects         = ["repo:octo-org/octo-repo:ref:refs/heads/main"]
        subject_patterns = ["repo:octo-org/octo-repo:ref:refs/heads/release/*"]
      }
    }
  }
  assert {
    condition = jsondecode(aws_iam_role.this["release"].assume_role_policy).Statement == [
      {
        Effect    = "Allow"
        Principal = { Federated = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com" }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = ["repo:octo-org/octo-repo:ref:refs/heads/main"]
          }
        }
      },
      {
        Effect    = "Allow"
        Principal = { Federated = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com" }
        Action    = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" }
          StringLike   = { "token.actions.githubusercontent.com:sub" = ["repo:octo-org/octo-repo:ref:refs/heads/release/*"] }
        }
      },
    ]
    error_message = "Prefix patterns must match with StringLike in their own statement so exact subjects still match on their own."
  }
}

run "existing_provider_is_looked_up" {
  command = plan
  variables {
    create_oidc_provider = false
  }
  assert {
    condition     = length(aws_iam_openid_connect_provider.github) == 0
    error_message = "The module must not create a second provider in an account that already has one."
  }
  assert {
    condition     = jsondecode(aws_iam_role.this["deploy"].assume_role_policy).Statement[0].Principal.Federated == "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com" && output.oidc_provider_arn == "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com"
    error_message = "Roles must trust the provider that already exists in the account."
  }
}

run "iam_limits_are_inclusive" {
  command = plan
  variables {
    roles = { deploy = { name = "a23456789012345678901234567890123456789012345678901234567890123b", subjects = ["repo:octo-org/octo-repo:environment:dev"], max_session_duration = 43200 } }
  }
  assert {
    condition     = length(aws_iam_role.this["deploy"].name) == 64 && aws_iam_role.this["deploy"].max_session_duration == 43200
    error_message = "A 64-character role name and a 12-hour session must be accepted."
  }
}

run "bare_wildcard_subject" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["*"] } }
  }
  expect_failures = [var.roles]
}

run "wildcard_in_exact_subject" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["repo:octo-org/octo-repo:ref:refs/heads/*"] } }
  }
  expect_failures = [var.roles]
}

run "subject_without_ref_or_environment" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["repo:octo-org/octo-repo"] } }
  }
  expect_failures = [var.roles]
}

run "pull_request_subject" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["repo:octo-org/octo-repo:pull_request"] } }
  }
  expect_failures = [var.roles]
}

run "pattern_for_every_branch" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subject_patterns = ["repo:octo-org/octo-repo:ref:refs/heads/*"] } }
  }
  expect_failures = [var.roles]
}

run "pattern_for_every_claim" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subject_patterns = ["repo:octo-org/octo-repo:*"] } }
  }
  expect_failures = [var.roles]
}

run "role_without_subjects" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy" } }
  }
  expect_failures = [var.roles]
}

run "session_shorter_than_iam_minimum" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["repo:octo-org/octo-repo:environment:dev"], max_session_duration = 3599 } }
  }
  expect_failures = [var.roles]
}

run "session_longer_than_iam_maximum" {
  command = plan
  variables {
    roles = { deploy = { name = "starter-fixture-dev-deploy", subjects = ["repo:octo-org/octo-repo:environment:dev"], max_session_duration = 43201 } }
  }
  expect_failures = [var.roles]
}

run "role_name_longer_than_iam_limit" {
  command = plan
  variables {
    roles = { deploy = { name = "a234567890123456789012345678901234567890123456789012345678901234b", subjects = ["repo:octo-org/octo-repo:environment:dev"] } }
  }
  expect_failures = [var.roles]
}
