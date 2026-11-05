# Changelog

## Unreleased

- Stack-level `context.tf` with shared `module.context.id` and `module.context.tags` outputs.
- Optional portable tags with reserved standard keys, preserving existing resource names.
- TFLint cloud rules and Trivy source/saved-plan gates, including fail-closed apply checks.
- Explicit AWS, Azure, and GCP state bootstrap with deletion protection and backend JSON output.
- Deployment-scoped `state-list` and `state-show` commands.
- Customer-managed AWS storage keys and Azure storage network default deny.
- Real scanner/linter acceptance and rejection smoke tests for both engines.

- Explicit environment/cloud/group/stack deployments with native state backends.
- AWS, Azure, and GCP network/storage examples for dev, stage, and prod.
- A cloud-free local catalog and deployment generator.
- Saved-plan verification, per-deployment working data and process locks.
- OpenTofu and Terraform checks, mocked cloud tests, and real local smoke tests.
- Documentation, contribution guidance, and MIT licensing.
