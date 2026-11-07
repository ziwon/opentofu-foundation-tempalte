# Changelog

## Unreleased

First release of the template.

- 30 native OpenTofu roots under `live/<environment>/<cloud>/<group>/<stack>` for
  dev, stage, and prod. They cover AWS, Azure, and GCP network, storage, and
  state-bootstrap examples, plus a cloud-free local catalog. Each root owns its
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
  `mise.toml`, and optional `just` aliases for native commands.
- English and Korean getting-started guides, plus architecture, cloud setup,
  bootstrap, operations, quality, Atlantis, security, and contribution guides.
