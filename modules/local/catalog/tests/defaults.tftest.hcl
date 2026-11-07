variables {
  name        = "starter-fixture-dev"
  tags        = { "project" : "starter", "environment" : "dev", "managed_by" : "iac" }
  description = "Local dev example; safe to apply without a cloud account."
}

run "catalog_inputs" {
  command = plan
  assert {
    condition     = terraform_data.catalog.input.name == var.name && tomap(terraform_data.catalog.input.tags) == tomap(var.tags) && terraform_data.catalog.input.description == var.description
    error_message = "The catalog must record the supplied name, tags, and description."
  }
}
