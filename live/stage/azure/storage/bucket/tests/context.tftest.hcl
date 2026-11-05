mock_provider "azurerm" {
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Storage/storageAccounts/example" }
  }
}
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
