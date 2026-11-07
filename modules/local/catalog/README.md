# local/catalog

Core module that owns one local `terraform_data` catalog entry. It creates no cloud
resources. `stacks/local/foundation/catalog` calls it as `module "catalog"` and passes
`name`, `tags`, and `description`.

Run checks with `tofu init -backend=false` and `tofu test`. The test plans the local
`terraform_data` resource and needs no mocks or cloud credentials.
