# Resource names and tags

Every executable stack defines `module "context"` in `context.tf`, calling the
local [context module](../modules/context/README.md). It produces one canonical
deployment ID and a common tag map from the stack's live inputs.

```hcl
module "context" {
  source      = "../../../../modules/context"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
  tags        = var.tags
}
```

`main.tf` owns resources, `variables.tf` declares inputs, and `providers.tf` owns
cloud authentication and defaults. `context.tf` is an ordinary file in that same
root module, so all these files can reference `module.context` directly.

## Use the shared convention

For resources accepting a name and tags:

```hcl
resource "azurerm_resource_group" "this" {
  name     = "${module.context.id}-rg"
  location = var.location
  tags     = module.context.tags
}
```

AWS resources supporting provider defaults receive the common tags automatically:

```hcl
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.aws_account_id]
  default_tags { tags = module.context.tags }
}

resource "aws_vpc" "this" {
  cidr_block = var.network_cidr
  tags       = { Name = module.context.id }
}
```

When passing tags into a child module, use `tags = module.context.tags`. A resource
that needs an explicit map including its name can use
`merge(module.context.tags, { Name = "${module.context.id}-private" })`.
Keep resource-specific `Name` outside the shared map so distinct resources retain
their own display names. GCP uses `default_labels = module.context.tags` and explicit
`labels` on supported resources; Compute Engine network tags are a different feature.

## Add environment metadata

Add a `tags` object to the selected live `terraform.tfvars.json`:

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

Retain the existing cloud-specific inputs in that file. This produces ID
`starter-core-dev` and tags `project=starter`, `environment=dev`, `managed_by=iac`,
`owner=platform`, and `cost_center=research`. Omitting `tags` preserves the original
three tags. The module rejects reserved-key overrides, nonportable characters,
null tag values, and maps exceeding its tag budget.

The template deliberately uses a shared subset of the
[GCP label requirements](https://cloud.google.com/compute/docs/labeling-resources#requirements),
[AWS tag restrictions](https://docs.aws.amazon.com/tag-editor/latest/userguide/reference.html),
and [Azure tag limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources).
Check the particular resource's constraints when adding more resource-specific tags.

## Updating an existing checkout

The former `modules/naming` and `module.naming` are now `modules/context` and
`module.context`. Update custom callers, then run `init` for each affected deployment
(`bootstrap init` for bootstrap stacks). The module creates no resources, so no
state-address move is needed for the supplied examples. Existing IDs, default tags,
resource addresses, backend paths, and per-cloud name transformations are preserved.

This source change invalidates previously saved plans. Create a fresh plan before
applying; do not reuse a plan from before the change. The `new` generator copies
`context.tf` with the rest of a stack automatically.
