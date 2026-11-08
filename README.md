<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="OpenTofu foundation template: every deployment is its own OpenTofu root. The address dev/aws/storage/bucket maps to a live root, a stack, and core modules.">
</p>

<p align="center">
  <a href="README.ko.md">한국어</a> ·
  <a href="docs/architecture.md">Architecture</a> ·
  <a href="docs/cloud-setup.md">Cloud setup</a> ·
  <a href="docs/operations.md">Operations</a> ·
  <a href="docs/quality.md">Quality checks</a> ·
  <a href="docs/atlantis.md">Atlantis</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

An OpenTofu monorepo template for AWS, Azure, and GCP. Each deployment is one
directory with its own backend, providers, inputs, and lock file, and you run it with
plain `tofu`. Deployments need no Python, generator, or repository runner.

## Try it without a cloud account

Install OpenTofu 1.12.5, or run `mise install` to get every pinned tool from
[mise.toml](mise.toml). The local catalog uses only the built-in `terraform_data`
resource, so it creates local state and no cloud resources.

```sh
cd live/dev/local/foundation/catalog
tofu init -lockfile=readonly
tofu plan -out=plan.tfplan
tofu apply plan.tfplan
tofu state list
```

```text
Plan: 1 to add, 0 to change, 0 to destroy.
deployment_name = "starter-catalog-dev"
module.stack.module.catalog.terraform_data.catalog
```

State lands in `.infra/state/dev/local/foundation/catalog/terraform.tfstate`. A saved
plan applies without a prompt, so review it first. Remove the catalog with
`tofu plan -destroy -out=destroy.tfplan` and `tofu apply destroy.tfplan`.

## What you get

33 deployment roots for dev, stage, and prod.

| Cloud | Network | Storage | Remote state |
| --- | --- | --- | --- |
| AWS | VPC, private subnet, default-deny security group | Private, encrypted, versioned S3 bucket | S3 with lock files |
| Azure | VNet, subnet, network security group | Private containers, versioning, identity-based access | Azure Blob with leases |
| GCP | Custom VPC, subnet, ingress firewall | Private, versioned bucket with uniform access | GCS with locking |
| Local | Built-in catalog | Local state only | Local file |

- Each cloud has a state bootstrap root that creates its own backend storage, with
  deletion protection. See [bootstrap](docs/bootstrap.md).
- AWS has GitHub Actions OIDC roles, so workflows assume short-lived roles instead
  of storing keys. See [cloud setup](docs/cloud-setup.md#let-github-actions-assume-an-aws-role).
- The examples create no compute, NAT gateways, or public IPs. Storage, requests,
  keys, versions, and logs can still incur charges.

## How it fits together

<p align="center">
  <img src="./assets/readme/layers.svg" width="100%" alt="The dev, stage, and prod roots each own their state, lock, and inputs, and all call the same stack, which composes the kms-key and s3-bucket core modules.">
</p>

A deployment address is `environment/cloud/group/stack`, such as
`dev/aws/storage/bucket`. The address names three layers:

- **`live/<address>`** is the root you run. It owns the backend, providers, inputs,
  and lock file, and calls one stack as `module "stack"`.
- **`stacks/<cloud>/<group>/<stack>`** composes resources for one purpose. Every
  environment calls the same stack.
- **`modules/<cloud>/<name>`** holds reusable building blocks, such as `kms-key` and
  `s3-bucket`. `modules/context` builds the `<namespace>-<name>-<environment>` ID
  and tags that every root uses.

Stacks and modules configure no providers or backends. Each root keeps an explicit
state key that matches its address. See [architecture](docs/architecture.md),
[names and tags](docs/context.md), and [adding deployments](docs/adding-stacks.md).

## Start a cloud deployment

1. Pick a root under `live/<environment>/<cloud>/<group>/<stack>`.
2. Set its account, subscription, or project, region, and names in `terraform.tfvars.json`.
3. Create state storage with [bootstrap](docs/bootstrap.md), or use storage you already manage.
4. Replace the storage placeholders in `backend.tf`. Keep its explicit key or prefix.
5. Log in through your cloud's identity mechanism. See [cloud setup](docs/cloud-setup.md).
6. Optionally run `just preflight dev/aws/network/core`. It checks that your login
   matches the root and changes nothing.
7. Review a saved plan, then apply it through your approved process.

```sh
tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
tofu -chdir=live/dev/aws/network/core plan -out=plan.tfplan
tofu -chdir=live/dev/aws/network/core apply plan.tfplan
```

`just init`, `just plan`, and `just apply` are optional aliases for the same native
commands. Run `just --list` for every recipe.

## Checks

<p align="center">
  <img src="./assets/readme/gates.svg" width="100%" alt="Every pull request runs format and layout checks, validation with mocked plans, TFLint, a Trivy source scan, and a local smoke test. The optional Atlantis workflow plans, scans the saved plan, requires Code Owner approval, and applies the same plan.">
</p>

Run the same checks locally with Python 3.10 or later and the tools from `mise.toml`:

```sh
python3 tools/check.py
python3 tools/smoke.py
python3 tools/quality_smoke.py
gitleaks dir . --redact --no-banner
```

[CI](.github/workflows/check.yml) also runs Gitleaks on the full history. Cloud tests
are plan-only and use mocks or fake credentials. Native local commands run no scans or
approvals. Trusted automation must run the source and saved-plan scans and require
approval. Trivy checks configuration, not what an IAM role may do, so review role
permissions in the pull request. See [quality checks](docs/quality.md) and
[verification](docs/verification.md).

## Optional integrations

None of these is required. Ordinary `tofu` commands work without them.

| Integration | What it adds | Status |
| --- | --- | --- |
| [Atlantis](docs/atlantis.md) | Pull request plans and applies with source and saved-plan scans and Code Owner approval | Server config tested locally |
| [GitHub Actions OIDC](docs/cloud-setup.md#let-github-actions-assume-an-aws-role) | AWS roles that trust exact repository, branch, or environment claims | Not yet run against a live account |
| [Prowler](integrations/prowler/README.md) | Opt-in read-only audit role and a scheduled account scan workflow | Not yet run against a live account |
| [Infracost](integrations/infracost/README.md) | `just cost <deployment>` prices a saved plan | Needs an API key; not run here |
| [Preflight](docs/operations.md) | `just preflight <deployment>` compares your cloud login with a root | Tested with fake CLIs |

## Security and state

State, saved plans, provider metadata, and reports can contain secrets. Keep them out
of Git and public logs. Local and bootstrap state live under `.infra/state/`, so
deleting `.infra/` deletes that state. Read [security](SECURITY.md) and the
[publication checklist](docs/publishing.md) before you enable deployments or publish a fork.

## License

[MIT](LICENSE). Installed providers and tools keep their own licenses.
