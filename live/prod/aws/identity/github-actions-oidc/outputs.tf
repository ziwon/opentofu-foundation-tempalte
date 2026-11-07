output "oidc_provider_arn" {
  description = "ARN of the account's GitHub Actions OIDC provider that the roles trust."
  value       = module.stack.oidc_provider_arn
}
output "roles" {
  description = "ARN and name of each GitHub Actions role. Use an ARN as role-to-assume in aws-actions/configure-aws-credentials."
  value       = module.stack.roles
}
output "deployment_name" {
  description = "Stable resource name for this deployment."
  value       = module.context.id
}
