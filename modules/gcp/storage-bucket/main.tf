locals {
  name = "${var.id}-${var.project_id}"
}

resource "google_storage_bucket" "this" {
  name                        = local.name
  location                    = var.location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = var.labels
  versioning { enabled = true }
  dynamic "soft_delete_policy" {
    for_each = var.soft_delete_retention_seconds == null ? [] : [var.soft_delete_retention_seconds]
    content {
      retention_duration_seconds = soft_delete_policy.value
    }
  }
  lifecycle {
    prevent_destroy = true
    precondition {
      condition     = length(local.name) <= 63
      error_message = "GCS bucket name \"${local.name}\" exceeds the 63-character limit. Shorten the namespace, name, environment, or project ID."
    }
  }
}
