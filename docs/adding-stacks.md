# Add a deployment, stack, or core module

## Add an environment

Copy an existing native root without generated artifacts. For example, create
`live/preview/aws/network/core` and copy the reviewed `.tf` files,
`terraform.tfvars.json`, tests, and `.terraform.lock.hcl` from the dev root.
Do not copy `.terraform/`, state, or saved plans.

1. Change `environment` in `terraform.tfvars.json` to `preview`.
2. Review the account, region, CIDRs, resource names, and tags.
3. Change the explicit key or prefix in `backend.tf` to the new deployment ID.
   For local state, use `.infra/state/preview/aws/network/core/terraform.tfstate`
   through the root's relative path.
4. Review module source paths if the directory depth changed.
5. Regenerate the checked-in Atlantis project example, then run layout checks,
   native validation, mocked tests, lint, and source security checks.
6. Initialize the new backend and review a plan before an authorized deployment.

Copying HCL does not create a separate state unless the backend identity changes.
Keep the default workspace and verify the selected backend before applying.

## Add a stack

Put the resources for a new kind of deployment in a stack under
`stacks/<cloud>/<group>/<stack>`. Every stack needs at least one root, and the
layout check fails for a stack that no root calls. Declare only the inputs consumed
by those resources, including the common typed context:

```hcl
variable "context" {
  description = "Deployment name and common tags."
  type = object({
    id   = string
    tags = map(string)
  })
}
```

Stacks declare provider requirements but do not configure providers, choose cloud
identities, or declare backends. Declare each provider as a range within its current
major version, such as `>= 6.71.0, < 7.0.0`. Roots pin the exact version. Put
cloud-specific naming and resource relationships in the stack. Return outputs that
callers need.

Validate an input in the module that consumes it. A root validates only a value
that no module it calls validates, such as an account ID that only its provider
configuration reads.

Create a live root that calls `modules/context` in `context.tf` and the stack
as `module "stack"` in `main.tf` with
`source = "../../../../../stacks/<cloud>/<group>/<stack>"`. Pass `module.context.id` and
`module.context.tags` as the context input. Keep account and region selection in
the root's provider configuration.

Include these root files:

- `backend.tf`, `context.tf`, `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf`.
- `providers.tf` for external providers.
- `terraform.tfvars.json` with reviewed non-secret values.
- `.terraform.lock.hcl` for external provider selections.
- Plan-only mocked tests for deployment wiring and input behavior.
- `migrations.tf` when existing resource addresses move.

When a resource's address changes, add a `moved` block in the module that now
declares the new address. Write `from` and `to` relative to that module. For
example, moving `aws_vpc.this` into a nested `module "vpc"` of the stack
needs this block in the stack:

```hcl
moved {
  from = aws_vpc.this
  to   = module.vpc.aws_vpc.this
}
```

Keep the earlier moves. The root's `moved` block still takes the shared-root
address to `module.stack.aws_vpc.this`, and the stack's block continues
the chain. The layout check fails when any address in
`tools/legacy-addresses.json` stops before a declared resource. New resources
need no moves. The check rejects `count`, `for_each`, and non-local module
sources because it cannot trace their addresses.

Test resource behavior within the stack and deployment behavior from the
root. Keep assertions meaningful for encryption, private networking, retention,
identity, names, and tags. A root cannot directly inspect a child module's private
resources. Use a stack test or an intentional output for that assertion.
`tools/check.py` runs each stack's tests with the provider lock of its dev root.

## Add a core module

Put a building block that several stacks share under `modules/<cloud>/<name>`.
Core modules follow the same rules as stacks. They declare provider requirements,
configure no providers or backends, and take only the inputs they consume. Call a
core module from a stack with a local source such as
`source = "../../../../modules/aws/<name>"`.

`modules/local/catalog` is a working example. It owns the local catalog's
`terraform_data.catalog` and takes `name`, `tags`, and `description`. The stack
`stacks/local/foundation/catalog` calls it and keeps its own outputs:

```hcl
module "catalog" {
  source      = "../../../../modules/local/catalog"
  name        = var.context.id
  tags        = var.context.tags
  description = var.description
}
```

Moving a resource from a stack into a core module changes its address. Add the
`moved` block to the stack, in `migrations.tf`, and leave the root's moves unchanged:

```hcl
moved {
  from = terraform_data.catalog
  to   = module.catalog.terraform_data.catalog
}
```

State at the shared-root address `terraform_data.catalog` follows the root's move and
then the stack's move. State at `module.stack.terraform_data.catalog` follows only the
stack's move. Both end at `module.stack.module.catalog.terraform_data.catalog`.
`python3 tools/migration_smoke.py` applies both starting states with OpenTofu and
requires a no-op move. Keep the resource's arguments and their types unchanged when
you move it. A value of a different type, such as a map where state recorded an
object, plans an update even when the JSON looks equal.

Add mocked plan-only tests under the module's `tests/` directory. `tools/check.py`
runs them with the provider lock of any dev root for the same cloud. Regenerate the
Atlantis project example afterward. Each project watches every local module that
its root reaches, so the new module appears in the `when_modified` patterns of the
roots whose stacks call it.

## Add a cloud or backend

Native OpenTofu owns backend configuration and authentication. A new backend type
does not need a deployment runner extension. Declare the backend explicitly in
the root and review its locking, access, and recovery behavior.

Review scanner coverage for a new provider. Add an available cloud linter plugin
with a reviewed pin to `.tflint.hcl` and the quality helper's plugin selection.
Keep generic source and saved-plan scans fail-closed when no recognized checks run.

Resolve provider locks deliberately, then run the full repository checks:

```sh
tofu -chdir=live/dev/aws/network/core init -backend=false
tofu -chdir=live/dev/aws/network/core providers lock
python3 tools/atlantis.py --output integrations/atlantis/atlantis.yaml.example
python3 tools/check.py
```

Use the actual new root path for provider locking. Refresh any active Atlantis
configuration with the same selection and options described in [Atlantis setup](atlantis.md).
