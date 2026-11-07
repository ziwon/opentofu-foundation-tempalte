# OpenTofu foundation template

An infrastructure monorepo template for AWS, Azure, and GCP. Each deployment is
an executable OpenTofu root with its own backend, inputs, providers, and lock file.
Run native `tofu` commands from that directory. Ordinary deployment operations do
not require Python, a generator, or a repository runner.

[한국어 안내](README.ko.md) · [Architecture](docs/architecture.md) ·
[Cloud setup](docs/cloud-setup.md) · [Operations](docs/operations.md) ·
[Bootstrap](docs/bootstrap.md) · [Names and tags](docs/context.md) ·
[Quality checks](docs/quality.md) · [Atlantis](docs/atlantis.md) · [Contributing](CONTRIBUTING.md)

## Deployment model

```text
live/dev/aws/network/core/       executable deployment root
  backend.tf                    explicit state location
  context.tf                    shared name and tags
  main.tf                       module "stack" call
  providers.tf                  account and provider configuration
  versions.tf                   OpenTofu and provider requirements
  .terraform.lock.hcl           provider selections
  variables.tf                  root inputs
  terraform.tfvars.json         non-secret deployment values
  outputs.tf                    deployment outputs
stacks/aws/network/core/        purpose-specific composition the root calls
modules/context/                name and tag convention
modules/<cloud>/<module>/       reusable core building blocks
```

A deployment is `environment/cloud/group/stack`. The 30 supplied roots cover AWS,
Azure, and GCP network, storage, and state bootstrap examples, plus a local catalog,
in dev, stage, and prod. Each leaf runs independently and uses the default workspace.

The repository has three layers. A `live/` root owns state, providers, and inputs,
and calls exactly one stack as `module "stack"`. A stack under
`stacks/<cloud>/<group>/<stack>` composes resources for one purpose and may call core
modules from `modules/`. Core modules hold reusable building blocks and the shared
`modules/context` convention. Stacks and modules have no backend or provider configuration.

## Quick start without a cloud account

Install OpenTofu 1.12.5. Review [mise.toml](mise.toml) if you use
[mise](https://mise.jdx.dev/) to install the pinned development tools.
Python and the quality tools are optional for this local lifecycle.

```sh
cd live/dev/local/foundation/catalog
tofu init -lockfile=readonly
tofu plan -out=plan.tfplan
tofu apply plan.tfplan
tofu output
tofu state list
```

The catalog uses only the built-in `terraform_data` resource. Applying the saved
plan creates local state and no cloud resources. Its name is `starter-catalog-dev`.
The backend stores state at repository-relative
`.infra/state/dev/local/foundation/catalog/terraform.tfstate`.
A saved-plan apply does not ask for confirmation. Review the plan before running it.

To remove the local catalog, review and apply a destroy plan:

```sh
tofu plan -destroy -out=destroy.tfplan
tofu apply destroy.tfplan
```

From the repository root, `just init dev/local/foundation/catalog`, `just plan dev/local/foundation/catalog`, and `just apply dev/local/foundation/catalog` are
optional aliases for native commands. Use `just --list` for the available recipes.

## Start a cloud deployment

1. Select a root under `live/<environment>/<cloud>/<group>/<stack>`.
2. Set its account, subscription, or project, region, and names in `terraform.tfvars.json`.
3. Create state storage through [bootstrap](docs/bootstrap.md), or use storage you already manage.
4. Replace the storage placeholders in `backend.tf`. Preserve its explicit key or prefix.
5. Authenticate through your cloud's supported identity mechanism, following [cloud setup](docs/cloud-setup.md).
6. Run `just preflight dev/aws/network/core` to confirm that your login matches the root.
   The preflight is read-only and optional. Native `tofu` commands do not need it.
7. Run the checks, initialize the backend, review a saved plan, and apply it through your approved deployment process.

```sh
tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
tofu -chdir=live/dev/aws/network/core plan -out=plan.tfplan
tofu -chdir=live/dev/aws/network/core apply plan.tfplan
```

| Cloud | Network example | Storage example | Workload backend |
| --- | --- | --- | --- |
| AWS | VPC, private subnet, default-deny security group | Private, encrypted, versioned S3 bucket | S3 with lock files |
| Azure | VNet, subnet, network security group | Private containers, versioning, identity-based access | Azure Blob with leases |
| GCP | Custom VPC, subnet, ingress firewall | Private, versioned bucket with uniform access | GCS with locking |
| Local | Built-in catalog | Local state only | Local file |

The examples create no compute workloads, NAT gateways, or public IPs. Storage,
requests, keys, versions, and network logging can incur charges. Review identity,
monitoring, retention, private connectivity, and recovery requirements before production.

## Names, tags, and reuse

Each root calls `modules/context` in `context.tf`. Its `module.context.id` is
`<namespace>-<name>-<environment>`. Its `module.context.tags` combines standard
metadata with optional `tags` from the live inputs. The keys `project`,
`environment`, and `managed_by` are reserved.

The root passes these outputs to its stack through a typed `context`
object with `id` and `tags`. The stack composes resources, and the core modules
it calls own cloud-specific name rules. Providers remain in the root. See [names and tags](docs/context.md)
and [adding deployments](docs/adding-stacks.md).

## State

State identity is explicit in each root's `backend.tf`. Local and bootstrap state
live under `.infra/state/<deployment>/terraform.tfstate`. Remote workloads use
`<deployment>/terraform.tfstate` keys for S3 and Azure, or `<deployment>` prefixes
for GCS. Deleting `.infra/` deletes local and bootstrap state, so back it up first.

## Verification and CI

Python 3.10 or later is a development dependency for repository checks, report
validation, and fixture tests. It is not part of native deployment execution.
Install the pinned quality tools before running:

```sh
python3 tools/check.py
python3 tools/smoke.py
python3 tools/quality_smoke.py
gitleaks dir . --redact --no-banner
```

The [CI workflow](.github/workflows/check.yml) supports OpenTofu only. It checks
formatting, layout, provider validation, lint, source security, mocked cloud plans,
and local lifecycle behavior. The real scanner fixtures test rejection as well as
acceptance. Cloud tests are plan-only and use mocks or isolated fake credentials.
Actual fixture applies and destroys use local `terraform_data` resources.
See [verification scope](docs/verification.md) for commands and limits.

Native local commands run no approval prompts or automatic scans. Trusted
deployment automation must run the source and saved-plan security checks, require
approvals, and restrict untrusted code.
The optional [Atlantis integration](docs/atlantis.md) uses built-in `init`, `plan`,
and `apply` with explicit quality steps and server-owned approval requirements.

State, plans, provider metadata, and reports can contain secrets. Keep generated
artifacts out of Git and public logs. Read [security](SECURITY.md) and the
[publication checklist](docs/publishing.md) before enabling deployments or publishing a fork.

## License

[MIT](LICENSE). Installed providers and tools retain their own licenses.
