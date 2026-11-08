# Changelog

## Unreleased

First release of the template.

- 33 native OpenTofu roots under `live/<environment>/<cloud>/<group>/<stack>` for
  dev, stage, and prod. They cover AWS, Azure, and GCP network, storage, and
  state-bootstrap examples, AWS GitHub Actions OIDC roles, and a cloud-free local
  catalog. Each root owns its
  backend, provider configuration, inputs, outputs, and lock file, and runs with
  plain `tofu` commands.
- Each root calls one purpose-specific stack in `stacks/<cloud>/<group>/<stack>` as
  `module "stack"`. Stacks call reusable core modules in `modules/<cloud>/`, and
  `modules/context` sets the shared `<namespace>-<name>-<environment>` ID and tags.
  Stacks and modules configure no providers or backends.
- Data-store modules use `prevent_destroy`. Plans fail when a GCS or S3 bucket name
  exceeds 63 characters. Long Azure storage account names use a hash of the full
  deployment ID.
- Bootstrap roots keep independent local state under `.infra/state/`, output
  non-secret backend settings, and stay out of Atlantis projects.
- `tools/check.py` checks the layout, formatting, provider validation, TFLint, Trivy
  source scans, and mocked plan-only tests for every root, stack, and tested core
  module. `tools/smoke.py` applies and destroys the local catalog in dev, stage, and prod.
- `tools/quality.py` scans source and saved plans. It rejects HIGH and CRITICAL
  findings, inline `trivy:ignore` and `tfsec:ignore` comments, missing checks, and
  unrecognized reports. `tools/quality_smoke.py` proves acceptance and rejection with
  the real scanner and linter.
- An optional Atlantis integration generates one project per workload root, watches
  the local modules each root reaches, and runs source and saved-plan scans with
  server-owned approval requirements. `.github/CODEOWNERS` assigns that policy to a
  reviewing team.
- OpenTofu-only CI, Dependabot updates for root provider locks, pinned tools in
  `mise.toml`, and optional `just` recipes for native commands.
- The check tools use `TF_PLUGIN_CACHE_DIR` and `TFLINT_PLUGIN_DIR` when they are set,
  so provider and plugin caches can live outside the checkout.
- An optional `just cost <group> <stack>` recipe prices a saved plan with Infracost.
  `integrations/infracost/mise.toml` pins the CLI, and no check or CI job uses it.
- English and Korean getting-started guides, plus architecture, cloud setup,
  bootstrap, operations, quality, Atlantis, security, and contribution guides.
- `just preflight <group> <stack>` runs `tools/preflight.py`, a read-only check that
  the active `aws`, `az`, or `gcloud` identity matches the root's account,
  subscription, project, and AWS region, and reports the caller it matched. It fails
  on committed placeholders, a missing CLI, or a missing login.
- `just use` selects a `.env.<name>` context that sets the environment, cloud, and
  cloud CLI variables. Root recipes then take `<group> <stack>` or the full path.
  Before `tofu` runs, `tools/context.py` prints the stack, root, backend, state key,
  and data directory. The recipes that use credentials run the preflight first.
  Contexts hold no account IDs or state buckets, which stay in each root.
- `modules/aws/github-actions-oidc` creates or looks up the account's GitHub Actions
  OIDC provider and IAM roles that trust exact `sub` claims and the
  `sts.amazonaws.com` audience with `StringEquals`. Prefix patterns are an explicit
  per-role opt-in. Validation rejects wildcard, malformed, and `pull_request`
  subjects and session limits outside 1 to 12 hours. The
  `live/<environment>/aws/identity/github-actions-oidc` roots name each role
  `<deployment name>-<key>`.
- Setting `audit_subjects` in an AWS identity root adds `<deployment name>-audit`, a
  read-only role for Prowler that trusts only those exact subjects. It attaches
  `SecurityAudit`, `ViewOnlyAccess`, and Prowler's read-only additions. The committed
  inputs create no audit role. `integrations/prowler` pins Prowler 5.48.0 in
  `mise.toml` and has a GitHub Actions workflow example that scans an account and
  uploads reports with 7-day retention. Its findings are advisory.
