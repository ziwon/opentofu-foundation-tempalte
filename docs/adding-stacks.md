# Add a deployment or resource composition

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

## Add a resource composition

Put shared resources under `modules/<cloud>/<group>/<stack>`. Declare only the
inputs consumed by those resources, including the common typed context:

```hcl
variable "context" {
  description = "Deployment name and common tags."
  type = object({
    id   = string
    tags = map(string)
  })
}
```

Modules declare provider requirements but do not configure providers, choose cloud
identities, or declare backends. Put cloud-specific naming and resource relationships
in the composition. Return outputs that callers need.

Create a live root that calls `modules/context` in `context.tf` and the composition
as `module "stack"` in `main.tf`. Pass `module.context.id` and
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
example, moving `aws_vpc.this` into a nested `module "vpc"` of the composition
needs this block in the composition:

```hcl
moved {
  from = aws_vpc.this
  to   = module.vpc.aws_vpc.this
}
```

Keep the earlier moves. The root's `moved` block still takes the shared-root
address to `module.stack.aws_vpc.this`, and the composition's block continues
the chain. The layout check fails when any address in
`tools/legacy-addresses.json` stops before a declared resource. New resources
need no moves. The check rejects `count`, `for_each`, and non-local module
sources because it cannot trace their addresses.

Test resource behavior within the composition and deployment behavior from the
root. Keep assertions meaningful for encryption, private networking, retention,
identity, names, and tags. A root cannot directly inspect a child module's private
resources. Use a module test or an intentional output for that assertion.

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
