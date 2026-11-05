# Add environments, stacks, and clouds

## Another environment

```sh
python3 tools/infra.py new preview/aws/network/core --from dev/aws/network/core
```

Only live data is created when the stack path already exists. The environment
field is updated automatically. Review copied account IDs, region, CIDRs, state
storage, and names before using it. The state address is derived from the new path.

## Another stack

```sh
python3 tools/infra.py new dev/aws/network/analytics --from dev/aws/network/core
```

This copies the stack code, tests, lock file, and live data, excluding transient
working files. The new stack has its own state. Update its purpose and README,
then replace resources as appropriate. The generator never overwrites an existing
deployment or an unrelated existing stack.

The `bootstrap` group is reserved for state-storage stacks with local backends.
Create another one from an existing bootstrap deployment and use the explicit
bootstrap commands described in [bootstrap operations](bootstrap.md).

Keep Terraform inputs typed and documented. Commit tests that describe observable
properties: private networking, encryption, retention, identity boundaries, or
resource outputs. Do not merely assert an implementation's line-by-line shape.
All bundled cloud tests use mocked providers and `command = plan`.

## Reuse a module

Place a demonstrated reusable capability under `modules/<name>` or
`modules/<cloud>/<name>`. Modules declare required provider sources when needed
but do not configure providers, select accounts, or declare backends. Pass inputs
from stacks and return useful outputs. The [context module](../modules/context/README.md)
demonstrates the pattern. Keep its call in `context.tf` and use `module.context.id`
and `module.context.tags` for resource names and tags. Pass optional live-input
tags through `var.tags`; the standard context keys remain reserved.

A provider's physical resource model is not interchangeable with another cloud's.
Share genuinely common policies or metadata rather than building a single module
with conditional branches for every cloud.

## Another cloud or backend

The path model has no hardcoded list of cloud names. Add a stack under a new cloud
slug and a matching live deployment. Use `backend.tf.json` to declare one of the
supported native backends: local, S3, Azure Blob, or GCS. A provider does not have
to use a backend from the same cloud.

To support another backend type, extend the allowed non-secret fields and derived
state-address logic in `tools/infra.py`, with tests for isolation and input
validation. Keep credentials in the backend's native identity chain.

Every new stack should include:

- `context.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, and `backend.tf.json`;
- `providers.tf` for external providers;
- a committed `.terraform.lock.hcl` for provider-backed roots;
- plan-only mocked tests under `tests/`;
- a README with purpose, costs, permissions, and deployment notes;
- at least one live data pair.

Run `python3 tools/infra.py lock <deployment>` when first introducing a provider,
then run the checks for both engines. Inventory and CI discover the new deployment
without adding it to a separate manifest.
For a new cloud, review scanner coverage and add its pinned TFLint plugin to
`.tflint.hcl` and the cloud/plugin mapping in `tools/quality.py` when available.
