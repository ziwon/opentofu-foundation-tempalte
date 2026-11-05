run "environment_namespacing" {
  command = plan
  assert {
    condition     = output.deployment_name == "${var.namespace}-${var.name}-${var.environment}"
    error_message = "Names must include the selected environment."
  }
}

run "additional_tags_keep_resource_identity" {
  command = plan
  variables {
    tags = {
      owner       = "platform"
      cost_center = "research"
    }
  }
  assert {
    condition     = terraform_data.catalog.input.name == "${var.namespace}-${var.name}-${var.environment}"
    error_message = "Adding tags must not rename resources."
  }
  assert {
    condition = terraform_data.catalog.input.tags == {
      project     = var.namespace
      environment = var.environment
      managed_by  = "iac"
      owner       = "platform"
      cost_center = "research"
    }
    error_message = "Resources must receive both the standard and additional tags."
  }
}
