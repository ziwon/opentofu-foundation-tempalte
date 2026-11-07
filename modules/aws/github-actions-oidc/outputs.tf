output "oidc_provider_arn" {
  description = "ARN of the account's GitHub Actions OIDC provider that the roles trust."
  value       = local.provider_arn
}

output "roles" {
  description = "ARN and name of each role, keyed like the roles input. Pass an ARN to role-to-assume in aws-actions/configure-aws-credentials."
  value       = { for key, role in aws_iam_role.this : key => { arn = role.arn, name = role.name } }
}
