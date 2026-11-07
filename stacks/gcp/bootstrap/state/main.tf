module "bucket" {
  source                        = "../../../../modules/gcp/storage-bucket"
  id                            = var.context.id
  project_id                    = var.project_id
  location                      = var.region
  labels                        = var.context.tags
  soft_delete_retention_seconds = 2592000
}
