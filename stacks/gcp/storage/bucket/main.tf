locals {
  name = "${var.context.id}-${var.project_id}"
}

resource "google_storage_bucket" "this" {
  name                        = local.name
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = var.context.tags
  versioning { enabled = true }
  lifecycle {
    precondition {
      condition     = length(local.name) <= 63
      error_message = "GCS bucket name \"${local.name}\" exceeds the 63-character limit. Shorten the namespace, name, environment, or project ID."
    }
  }
}
