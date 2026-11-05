# Changelog

## Unreleased

- Security scans reject inline `trivy:ignore` and `tfsec:ignore` comments in source
  and saved-plan configuration. Trivy otherwise drops suppressed findings silently.
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
