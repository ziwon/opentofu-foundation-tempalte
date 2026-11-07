output "oidc_provider_arn" {
  description = "ARN of the account's GitHub Actions OIDC provider that the roles trust."
  value       = module.federation.oidc_provider_arn
}

output "roles" {
  description = "ARN and name of each GitHub Actions role, keyed like the roles input."
  value       = module.federation.roles
}
