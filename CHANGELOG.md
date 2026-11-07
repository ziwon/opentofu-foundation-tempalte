# Changelog

## Unreleased

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
