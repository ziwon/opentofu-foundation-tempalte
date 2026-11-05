module "stack" {
  source     = "../../../../../modules/gcp/storage/bucket"
  context    = { id = module.context.id, tags = module.context.tags }
  project_id = var.project_id
  region     = var.region
}
