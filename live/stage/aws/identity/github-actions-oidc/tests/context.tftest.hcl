mock_provider "aws" {}
run "deployment_context" {
  command = plan
  assert {
    condition     = module.context.id == "${var.namespace}-${var.name}-${var.environment}"
    error_message = "Resource identity must include the selected environment."
  }
  assert {
    condition     = module.context.tags == merge(var.tags, { project = var.namespace, environment = var.environment, managed_by = "iac" })
    error_message = "The selected deployment must receive standard and additional tags."
  }
}

run "additional_tags_keep_identity" {
  command = plan
  variables {
    tags = { owner = "platform", cost_center = "research" }
  }
  assert {
    condition     = module.context.id == "${var.namespace}-${var.name}-${var.environment}" && module.context.tags.owner == "platform" && module.context.tags.cost_center == "research"
    error_message = "Additional tags must be passed through without renaming resources."
  }
}

run "role_names_follow_deployment" {
  command = plan
  variables {
    roles = { deploy = { subjects = ["repo:octo-org/octo-repo:environment:fixture"] } }
  }
  assert {
    condition     = output.roles.deploy.name == "${var.namespace}-${var.name}-${var.environment}-deploy"
    error_message = "Role names must carry the deployment ID so environments sharing an account do not collide."
  }
}

run "audit_role_is_opt_in" {
  command = plan
  assert {
    condition     = !contains(keys(output.roles), "audit")
    error_message = "The committed inputs must create no audit role."
  }
}

run "audit_role_follows_deployment" {
  command = plan
  variables {
    audit_subjects = ["repo:octo-org/octo-repo:environment:security-audit"]
  }
  assert {
    condition     = output.roles.audit.name == "${var.namespace}-${var.name}-${var.environment}-audit"
    error_message = "Setting audit_subjects must add the <deployment name>-audit role."
  }
}
