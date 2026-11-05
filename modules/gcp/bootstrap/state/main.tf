resource "google_storage_bucket" "this" {
  name                        = "${var.context.id}-${var.project_id}"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  lifecycle { prevent_destroy = true }
  labels = var.context.tags
  versioning { enabled = true }
  soft_delete_policy { retention_duration_seconds = 2592000 }
}
