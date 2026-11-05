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
outputs into its composition module:

```hcl
context = {
  id   = module.context.id
  tags = module.context.tags
}
```

The composition declares `context` as `object({ id = string, tags = map(string) })`.
Its resources use `var.context.id` and `var.context.tags`. Cloud-specific name
transformations stay with those resources.

## Provider and resource tags

AWS provider defaults receive the common tags from the root:

```hcl
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.aws_account_id]
  default_tags { tags = module.context.tags }
}
```

The network composition keeps the resource-specific `Name` tag separate:

```hcl
resource "aws_vpc" "this" {
  cidr_block = var.network_cidr
  tags       = { Name = var.context.id }
}
```

Azure resources receive `var.context.tags`. GCP provider defaults and supported
resource labels use the common map. GCP Compute Engine network tags are a different feature.

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
