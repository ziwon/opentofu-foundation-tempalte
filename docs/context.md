# Resource names and tags

Every executable root calls the local [context module](../modules/context/README.md)
in `context.tf`. The module produces the deployment name and common tag map.

```hcl
module "context" {
  source      = "../../../../../modules/context"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
  tags        = var.tags
}
```

`context.tf` is an ordinary root file. Provider configuration can reference
`module.context.id` and `module.context.tags` directly. The root passes these
outputs into its stack:

```hcl
context = {
  id   = module.context.id
  tags = module.context.tags
}
```

The stack declares `context` as `object({ id = string, tags = map(string) })`.
Its resources use `var.context.id` and `var.context.tags`. Cloud-specific name
transformations stay with those resources.

AWS S3 bucket names are the ID plus the account ID. `modules/aws/s3-bucket` builds
the name, and a plan fails if it exceeds 63 characters.

Azure storage account names allow 24 lowercase letters and digits. The core module
`modules/azure/storage-account` receives the ID as `name_base`. It removes hyphens
and keeps the first 18 characters. If the ID fits, the suffix is 6 characters of
the subscription ID hash. If it is truncated, the suffix hashes the subscription
and the full ID, so environments in one subscription stay distinct.

GCS bucket names are the ID plus the project ID, and a plan fails if the total exceeds 63 characters.

## Provider and resource tags

AWS provider defaults receive the common tags from the root:

```hcl
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.aws_account_id]
  default_tags { tags = module.context.tags }
}
```

The VPC core module keeps the resource-specific `Name` tag separate. The network
stack passes `var.context.id` as `name`:

```hcl
resource "aws_vpc" "this" {
  cidr_block = var.network_cidr
  tags       = { Name = var.name }
}
```

Azure stacks pass `var.context.tags` to their resource groups and to the `tags`
input of their core modules. GCP provider defaults and supported resource labels use the common map. GCP Compute Engine network tags are a different feature.

## Add environment metadata

Add a `tags` object to the root's `terraform.tfvars.json`. Retain its cloud-specific inputs.

```json
{
  "namespace": "starter",
  "name": "core",
  "environment": "dev",
  "tags": {
    "owner": "platform",
    "cost_center": "research"
  }
}
```

The ID is `starter-core-dev`. The tags are `project=starter`, `environment=dev`,
`managed_by=iac`, `owner=platform`, and `cost_center=research`. Omitting `tags`
retains the three standard tags. The context module rejects reserved-key overrides,
nonportable characters, null values, and maps exceeding its tag budget.

The template uses a shared subset of cloud tag and label constraints. Check a
resource's own limits before adding resource-specific metadata. The ID does not
contain cloud or group, so it is not globally unique across deployment paths.

The native-root migration preserves existing names, tags, and cloud-specific
transformations. It changes managed-resource addresses through `module.stack`.
Follow the [migration guide](migration.md) for existing state.
