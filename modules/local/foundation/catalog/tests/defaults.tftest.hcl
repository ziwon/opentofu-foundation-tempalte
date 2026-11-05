variables {
  description = "Local dev example; safe to apply without a cloud account."
  context     = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

run "catalog_context" {
  command = plan
  assert {
    condition     = terraform_data.catalog.input.name == var.context.id && tomap(terraform_data.catalog.input.tags) == tomap(var.context.tags) && terraform_data.catalog.input.description == var.description
    error_message = "The catalog must preserve all supplied context and content."
  }
}
