# Terraform Foundation Template

**One codebase. Multiple clouds, environments, and independent stacks.**

A small infrastructure monorepo template with OpenTofu as the default CLI and
Terraform compatibility verified by the same test suite. It includes AWS, Azure,
and GCP examples, a cloud-free quick start, and a deployment runner written with
the Python standard library.

[한국어 안내](README.ko.md) · [Architecture](docs/architecture.md) ·
[Cloud setup](docs/cloud-setup.md) · [Operations](docs/operations.md) ·
[Bootstrap](docs/bootstrap.md) · [Names and tags](docs/context.md) ·
[Quality checks](docs/quality.md) · [Contributing](CONTRIBUTING.md)

## Deployment model

```text
modules/context                      reusable code; no provider configuration or state
          ↑
stacks/aws/network/core               executable stack shared by environments
          +
live/dev/aws/network/core             non-secret backend and input data
          ↓
dev/aws/network/core/terraform.tfstate independent state in the selected backend
```

A deployment is `environment/cloud/group/stack`. Every command takes that full
name; no active environment file or named workspace changes its meaning.

| Layer | Contains | Example |
| --- | --- | --- |
| `modules/` | Reusable building blocks | `modules/context` |
| `stacks/` | Resources, providers, backend type, lock file, tests | `stacks/aws/network/core` |
| `live/` | `backend.json` and `terraform.tfvars.json` | `live/prod/aws/network/core` |
| `.infra/` | Ignored state, plans, provider cache, and working data | Created by the runner |

The repository includes ten stacks and 30 deployment examples: AWS, Azure,
and GCP network/storage/bootstrap stacks plus a local catalog, each in dev, stage, and prod.

## Quick start without a cloud account

Requires Python 3.10+, OpenTofu, and Trivy; full checks also use TFLint. The runner targets Linux and macOS and is
verified on Linux; use WSL on Windows. Review [mise.toml](mise.toml), then let
[mise](https://mise.jdx.dev/) install the pinned tools:

```sh
mise trust
mise install
mise exec -- python3 tools/infra.py list
mise exec -- python3 tools/infra.py init dev/local/foundation/catalog
mise exec -- python3 tools/infra.py plan dev/local/foundation/catalog
mise exec -- python3 tools/infra.py apply dev/local/foundation/catalog
mise exec -- python3 tools/infra.py output dev/local/foundation/catalog
```

At the apply prompt, type `dev/local/foundation/catalog`. This example uses only
the built-in `terraform_data` resource: it creates local state and no cloud
resources. After installing the pinned tools, it needs neither credentials nor a network
connection. Remove its local resources through a reviewed destroy plan:

```sh
mise exec -- python3 tools/infra.py plan dev/local/foundation/catalog --destroy
mise exec -- python3 tools/infra.py apply dev/local/foundation/catalog
```

With mise activated, the shorter equivalents are `just list`, `just init <deployment>`,
`just plan <deployment>`, `just apply <deployment>`, and `just output <deployment>`.

## Start a cloud deployment

1. Select an example from the table below.
2. Configure its cloud account/project, region, and names in `terraform.tfvars.json`.
3. Use the explicit [bootstrap workflow](docs/bootstrap.md) to create versioned
   remote-state storage, or use storage you already manage. Replace `REPLACE_ME`
   in the workload's `backend.json` with the reviewed backend settings.
4. Authenticate using your cloud's supported identity mechanism; keep credentials
   outside the repository. Follow [cloud setup](docs/cloud-setup.md).
5. Run `show`, `test`, `init`, and `plan`; inspect the plan before `apply`.

```sh
python3 tools/infra.py show dev/aws/network/core
python3 tools/infra.py test dev/aws/network/core
python3 tools/infra.py init dev/aws/network/core
python3 tools/infra.py plan dev/aws/network/core
python3 tools/infra.py apply dev/aws/network/core
```

| Cloud | Network | Storage | Native state backend |
| --- | --- | --- | --- |
| AWS | [VPC, private subnet, default-deny security group](stacks/aws/network/core/README.md) | [Private, encrypted, versioned S3 bucket](stacks/aws/storage/bucket/README.md) | S3 with lock files |
| Azure | [VNet, subnet, network security group](stacks/azure/network/core/README.md) | [Private containers, versioning, identity-based access](stacks/azure/storage/bucket/README.md) | Azure Blob with leases |
| GCP | [Custom VPC, subnet, ingress firewall](stacks/gcp/network/core/README.md) | [Private, versioned bucket with uniform access](stacks/gcp/storage/bucket/README.md) | GCS with locking |
| Local | [Cloud-free catalog](stacks/local/foundation/catalog/README.md) | Built-in state only | Local file |

These examples establish a starting point, not a complete production platform.
They create no compute workloads, NAT gateways, or public IPs. Storage, requests,
versions, and network logging can incur charges. Add organization-specific IAM,
monitoring, retention, private endpoints, and recovery controls before production.

## Consistent resource names and tags

Each stack calls the local context module in `context.tf`. Use its outputs for
resource names and shared metadata:

```hcl
name = module.context.id
tags = module.context.tags
```

The ID is `<namespace>-<name>-<environment>`. Add optional `tags` in live inputs
for metadata such as `owner` or `cost_center`; the standard `project`,
`environment`, and `managed_by` tags remain reserved. AWS provider defaults,
Azure resource tags, and GCP labels use the same map. Resource-specific names
and cloud naming constraints are handled in the stack. See the
[context guide](docs/context.md) for examples and migration instructions.

## Add an environment or stack

Reuse the same executable stack in another environment:

```sh
python3 tools/infra.py new preview/aws/network/core --from dev/aws/network/core
```

Create a separate stack for a different capability:

```sh
python3 tools/infra.py new dev/aws/network/analytics --from dev/aws/network/core
```

The generator preserves existing files and derives a new state address. Review
the copied account, backend, CIDR, and other values before initialization.
See [adding stacks](docs/adding-stacks.md) for modules and new clouds.

## Commands

| Command | Effect |
| --- | --- |
| `list` | Discover deployments from `live/` |
| `show <deployment>` | Print code/data paths and the derived state address |
| `init <deployment>` | Initialize the configured backend; never create state storage |
| `validate <deployment>` | Initialize providers without a backend and validate code |
| `test <deployment>` | Run the stack's tests with that environment's inputs |
| `lint <deployment>` | Run TFLint with language and selected cloud rules |
| `security <deployment> [--plan]` | Scan source/live inputs, or verify and scan the saved plan |
| `plan <deployment> [--destroy]` | Scan and save a plan with a source/input receipt |
| `apply <deployment> [--yes]` | Verify, rescan, and apply only that saved plan |
| `output <deployment>` | Read state outputs |
| `state-list <deployment>` | List resource addresses in that deployment's state |
| `state-show <deployment> <address>` | Show one resource without changing state |
| `bootstrap <init\|plan\|apply\|output> <deployment>` | Explicitly manage state storage; output prints backend JSON |
| `new <deployment> --from <source>` | Copy an environment or stack without overwriting |
| `lock <deployment> [--upgrade]` | Deliberately regenerate the stack's provider lock file |
| `fmt` | Format modules and stacks |
| `check` | Check structure, docs, runner tests, formatting, lint, security, and all deployment tests |

Prefix commands with `python3 tools/infra.py`. `just --list` lists the convenient
wrappers. Every `apply` normally asks for the exact deployment name; `--yes` is
available for an explicitly approved automation workflow.

## OpenTofu and Terraform

OpenTofu is the default. To use Terraform:

```sh
python3 tools/infra.py --engine terraform test dev/aws/network/core
TF_CLI=terraform just check
```

Both engines use explicit `registry.opentofu.org` provider addresses and the same
committed lock files. The tested CLI versions are pinned in [mise.toml](mise.toml).
Working data and plans are separated by engine, while the deployment's state
address stays stable. Choose one engine for an actual deployment; switching a
state between engines is a migration, not an ordinary command-line toggle.

## Verification and CI

```sh
python3 tools/infra.py check
python3 tools/smoke.py --engine tofu
python3 tools/smoke.py --engine terraform
python3 tools/quality_smoke.py --engine tofu
python3 tools/quality_smoke.py --engine terraform
mise exec -- gitleaks dir . --redact --no-banner
```

The [CI workflow](.github/workflows/check.yml) runs the same checks for both
engines. Stack tests mock providers and use plan-only runs. The smoke test
executes real init/plan/apply/output/destroy commands in a disposable local-only
repository and checks environment isolation, tag propagation and validation,
stable resource names, stale plans, and failed-plan cleanup.
The quality smoke also proves that unsafe source and binary plans fail security
checks, using temporary fixtures and fake credentials with identity probes disabled.
CI has no cloud credentials and does not deploy infrastructure. See the
[local verification record](docs/verification.md) for the tested versions and scope.

Plans, state, backend metadata, and caches remain under ignored `.infra/`.
See [security](SECURITY.md) and the [publication checklist](docs/publishing.md)
before publishing a fork or enabling deployments.

## License

[MIT](LICENSE). This template's license does not change the licenses of OpenTofu,
Terraform, providers, or other tools that you install separately.
