# gcp/storage-bucket

Core module that owns one private, versioned GCS bucket. It names the bucket
`<id>-<project_id>` and fails the plan when that name exceeds 63 characters. The
bucket enforces uniform bucket-level access and public access prevention, refuses
deletion while it holds objects, and uses `prevent_destroy`.

Set `soft_delete_retention_seconds` to manage the soft delete policy. Leave it null
to keep the provider's default policy. `stacks/gcp/bootstrap/state` sets 30 days, and
`stacks/gcp/storage/bucket` leaves it null.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
