module "stack" {
  source               = "../../../../../stacks/aws/identity/github-actions-oidc"
  context              = { id = module.context.id, tags = module.context.tags }
  create_oidc_provider = var.create_oidc_provider
  roles                = var.roles
  audit_subjects       = var.audit_subjects
}
