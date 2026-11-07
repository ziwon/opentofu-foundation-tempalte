# Changelog

## Unreleased

- Roots no longer repeat name and CIDR validations that `modules/context` or their
  stack already applies. Invalid values still fail with the same message, now
  reported at the module call. Roots keep validations for account, subscription,
  and project IDs, because their provider configuration reads those values before
  any module runs. Stacks and core modules now accept a
  provider range within the current major version, and each root's exact pin and
  lock file select the version. Dependabot now updates roots only. Plans and
  provider selections are unchanged.
- The local catalog entry moved into the core module `modules/local/catalog`, which
  `stacks/local/foundation/catalog` calls as `module "catalog"`. Its address changed
  from `module.stack.terraform_data.catalog` to
  `module.stack.module.catalog.terraform_data.catalog`. A `moved` block in the stack
  continues the root's move, so state at either earlier address plans a no-op move.
  `tools/migration_smoke.py` now proves both starting states with OpenTofu. Run
  `tofu init` again in existing local working directories.
- Stacks moved from `modules/<cloud>/<group>/<stack>` to `stacks/<cloud>/<group>/<stack>`.
  A stack is the purpose-specific composition that a root calls as `module "stack"`.
  `modules/` now holds reusable core building blocks and `modules/context`. Resource
  addresses, `moved` blocks, and plans do not change. Run `tofu init` again in existing
  working directories, because the `module "stack"` source path changed. This `stacks/`
  layer holds no backends or state. It differs from the shared executable `stacks/`
  layout that native roots replaced.
- `tools/check.py` runs the tests of every stack and of every core module that has a
  `tests/` directory. Atlantis projects watch every local module their root reaches.
- The layout check requires every managed address from the shared-root layout,
  frozen in `tools/legacy-addresses.json`, to reach a distinct current resource
  through `moved` blocks. It follows local module calls at every depth. A missing
  move, which would plan a destroy and create, now fails the check before any plan.
  `count`, `for_each`, and non-local module sources fail as unsupported.
- Trivy scans use a new temporary cache and module directory. A checks bundle
  committed under `.infra/` can no longer replace the bundled checks.
- `.github/CODEOWNERS` assigns the quality helper, tool pins, lint rules, CI, and
  Atlantis configuration to a policy team. With Code Owner review required, a PR
  that changes this policy cannot reach Atlantis apply without that team's approval.
- Security scans reject inline `trivy:ignore` and `tfsec:ignore` comments in source
  and saved-plan configuration. Trivy otherwise drops suppressed findings silently.
- Azure storage account names that exceed 18 characters after hyphen removal now
  hash the full deployment ID. Shorter names do not change. Existing accounts with
  longer names plan a replacement, which `prevent_destroy` blocks.
- GCP bucket and bootstrap state bucket plans fail when the deployment ID plus
  project ID exceeds 63 characters. The GCS API previously rejected these at apply.
- Native OpenTofu roots for all 30 live deployments. Ordinary init, plan, apply,
  output, and state operations no longer require repository Python.
- Shared resources moved into `modules/<cloud>/<group>/<stack>`. Roots retain
  provider configuration, locks, backend identity, and `module.context` names and tags.
- Explicit moved blocks preserve state addresses during the module transition.
  Local and bootstrap state paths and remote keys remain unchanged.
- OpenTofu-only tooling and CI. Removed Terraform CLI support and the custom deployment runner.
- Optional `just` aliases expose native commands. Python remains available for checks,
  scanner reports, fixture tests, and Atlantis project generation.
- Atlantis uses built-in init, plan, and apply with source and saved-plan scans,
  server-owned approvals, disabled fork PRs, and separate bootstrap management.
- Local native commands no longer enforce checkout fingerprints, plan receipts,
  exact-name prompts, automatic scans, or runner-managed plan cleanup.
  Trusted deployment automation owns security and approval enforcement.
- Plan-only mocked cloud tests, local lifecycle and migration fixtures, and real
  scanner and linter acceptance and rejection checks.
- AWS, Azure, and GCP network, storage, and protected state-bootstrap examples
  for dev, stage, and prod, plus a cloud-free local catalog.
- Native-root migration, operating, security, and contribution guides in addition
  to English and Korean getting-started documentation.
- AWS stacks call the core modules `modules/aws/kms-key`, `modules/aws/s3-bucket`,
  and `modules/aws/vpc`. The bootstrap and storage stacks no longer duplicate the
  bucket and key, and the S3 module owns the `<name>-<account id>` naming rule. A
  plan fails when that name exceeds 63 characters. Resources moved from
  `module.stack.<address>` to `module.stack.module.<key|bucket|vpc>.<address>`, and
  both KMS keys are now `aws_kms_key.this`. Stack `moved` blocks continue the roots'
  moves, so state at either earlier address plans only moves. The workload storage
  bucket gains `prevent_destroy`. Run `tofu init` again in existing AWS working directories.
- Azure storage accounts and their containers moved into the core module
  `modules/azure/storage-account`, which `stacks/azure/bootstrap/state` and
  `stacks/azure/storage/bucket` call as `module "storage_account"`. The Azure virtual
  network, subnet, network security group, and association moved into
  `modules/azure/network`, which `stacks/azure/network/core` calls as `module "network"`.
  Resource groups stay in the stacks at unchanged addresses. Stack `moved` blocks
  continue the roots' moves, so state at either earlier address plans a no-op move to
  `module.stack.module.storage_account.*` or `module.stack.module.network.*`. Names,
  arguments, outputs, and `prevent_destroy` settings do not change. Run `tofu init`
  again in existing Azure working directories.
- The GCP stacks call the core modules `modules/gcp/storage-bucket` as
  `module "bucket"` and `modules/gcp/network` as `module "network"`. Their resources
  moved from `module.stack.<resource>` to `module.stack.module.bucket.<resource>` and
  `module.stack.module.network.<resource>`. `moved` blocks in each stack continue the
  roots' moves, and planned attributes do not change. The bucket name-length tests
  now run in the core module. The workload bucket in `gcp/storage/bucket` now uses
  `prevent_destroy`. Run `tofu init` again in existing GCP working directories.
