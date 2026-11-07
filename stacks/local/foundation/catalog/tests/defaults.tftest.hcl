variables {
  description = "Local dev example; safe to apply without a cloud account."
  context     = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

run "catalog_context" {
  command = apply
  assert {
    condition     = output.catalog.name == var.context.id && tomap(output.catalog.tags) == tomap(var.context.tags) && output.catalog.description == var.description
    error_message = "The catalog must preserve all supplied context and content."
  }
}
