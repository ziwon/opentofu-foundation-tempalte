module "naming" {
  source      = "../../../../modules/naming"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
}

resource "google_storage_bucket" "this" {
  name                        = "${module.naming.id}-${var.project_id}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = module.naming.tags
  versioning { enabled = true }
}
