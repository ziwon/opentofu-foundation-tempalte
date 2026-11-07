# local/catalog

Core module that owns one local `terraform_data` catalog entry. It creates no cloud
resources. `stacks/local/foundation/catalog` calls it as `module "catalog"` and passes
`name`, `tags`, and `description`.

The resource input keeps the object type of the tags that earlier state recorded, so
existing deployments plan a no-op move instead of an update.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
