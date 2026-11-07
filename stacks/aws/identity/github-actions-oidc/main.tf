module "federation" {
  source               = "../../../../modules/aws/github-actions-oidc"
  create_oidc_provider = var.create_oidc_provider
  roles                = { for key, role in var.roles : key => merge(role, { name = "${var.context.id}-${key}" }) }
}
