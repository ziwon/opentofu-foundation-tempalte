# Context

One naming and tagging convention for every native deployment root. The module contains only
locals, variables, and outputs; it creates no resources or provider configuration.

```hcl
module "context" {
  source      = "../../../../../modules/context"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
  tags        = var.tags
}
```

Place this call in the live root's `context.tf`. Pass `module.context.id` and
`module.context.tags` to the stack's typed `context` input. Resources use
`var.context.id` for names and `var.context.tags` for common tags or labels. The ID remains
`<namespace>-<name>-<environment>`; each segment accepts 1–16 lowercase letters,
digits, or hyphens, beginning with a letter. Adding tags does not change the ID.

| Output | Value |
| --- | --- |
| `id` | For example, `starter-core-dev` |
| `tags.project` | `namespace` |
| `tags.environment` | `environment` |
| `tags.managed_by` | `iac` |
| Additional `tags` entries | The caller's optional tags |

Extra tags cannot override `project`, `environment`, or `managed_by`. The portable
subset permits lowercase ASCII letters, digits, underscores, and hyphens; keys
start with a letter and contain 1–63 characters, and values may be empty and contain
at most 63 characters. Null values are rejected. At most 46 custom entries leave
room for the three standard tags and one resource-specific AWS `Name` tag under
the common 50-tag limit. Individual resource types may impose narrower limits.

AWS provider `default_tags` and GCP provider `default_labels` receive the common
map where supported. Azure resources receive `tags` explicitly. AWS `Name` tags
belong to individual resources, so subnets can use `${var.context.id}-private`
without sharing the VPC's display name. For GCP, these are labels, not Resource
Manager tags or Compute Engine network tags. Cloud-specific naming adapters
(for example Azure storage-account names without hyphens) remain in each stack.

See [the context guide](../../docs/context.md) for resource examples and
environment configuration.
