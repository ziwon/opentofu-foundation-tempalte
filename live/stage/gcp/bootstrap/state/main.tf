module "stack" {
  source     = "../../../../../stacks/gcp/bootstrap/state"
  context    = { id = module.context.id, tags = module.context.tags }
  project_id = var.project_id
  region     = var.region
}
