resource "google_storage_bucket" "this" {
  name                        = "${module.context.id}-${var.project_id}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = module.context.tags
  versioning { enabled = true }
}
