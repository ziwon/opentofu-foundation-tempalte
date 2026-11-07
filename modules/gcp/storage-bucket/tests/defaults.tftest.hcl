variables {
  id         = "starter-fixture-dev"
  project_id = "example-project"
  location   = "us-central1"
  labels     = { "project" : "starter", "environment" : "dev", "managed_by" : "iac" }
}

mock_provider "google" {}
run "private_versioned_bucket" {
  command = plan
  assert {
    condition     = google_storage_bucket.this.name == "starter-fixture-dev-example-project" && output.name == google_storage_bucket.this.name
    error_message = "Name the bucket <id>-<project_id> and export that name."
  }
  assert {
    condition     = google_storage_bucket.this.location == "us-central1" && google_storage_bucket.this.storage_class == "STANDARD" && google_storage_bucket.this.labels == tomap(var.labels)
    error_message = "Place the bucket in the given location with standard storage and the given labels."
  }
  assert {
    condition     = google_storage_bucket.this.uniform_bucket_level_access && google_storage_bucket.this.public_access_prevention == "enforced"
    error_message = "Public access must be prevented and access controlled by IAM."
  }
  assert {
    condition     = google_storage_bucket.this.versioning[0].enabled && !google_storage_bucket.this.force_destroy
    error_message = "Retain object versions and refuse deletion of nonempty buckets."
  }
  assert {
    condition     = length(google_storage_bucket.this.soft_delete_policy) == 0
    error_message = "Leave the soft delete policy to the provider when no retention is given."
  }
}

run "soft_delete_retention" {
  command = plan
  variables {
    soft_delete_retention_seconds = 2592000
  }
  assert {
    condition     = google_storage_bucket.this.soft_delete_policy[0].retention_duration_seconds == 2592000 && output.soft_delete_retention_seconds == 2592000
    error_message = "Apply and export the requested soft delete retention."
  }
}

run "bucket_name_at_limit" {
  command = plan
  variables {
    id         = "starter-fixture-development-0001"
    project_id = "example-project-abcdefghijklmn"
  }
  assert {
    condition     = length(google_storage_bucket.this.name) == 63
    error_message = "A 63-character bucket name must plan."
  }
}

run "bucket_name_over_limit" {
  command = plan
  variables {
    id         = "starter-fixture-development-00001"
    project_id = "example-project-abcdefghijklmn"
  }
  expect_failures = [google_storage_bucket.this]
}
