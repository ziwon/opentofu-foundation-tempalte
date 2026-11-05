# Local verification record

Verified on 2026-11-03 on Linux x86_64, with full checks, local smoke tests, and
publication scans repeated for the context-module update on 2026-11-05.
These results can be reproduced with the commands in the
[README](../README.md#verification-and-ci).

| Check | Result |
| --- | --- |
| OpenTofu 1.12.5 full check | Passed: structure, links, formatting, 20 Python behavior/report tests, validation of 10 stacks, lint/security checks for 30 deployments, and 33 native plan test runs |
| Terraform 1.15.8 full check | Passed against the same sources and provider lock files |
| OpenTofu real local smoke | Passed init, plan/security, apply, output, state-list/state-show, destroy, environment isolation, tag propagation/validation, stable names, stale/tampered-plan rejection, and failed-plan cleanup |
| Terraform real local smoke | Passed the same local lifecycle checks |
| Context migration, both engines (2026-11-05) | Applied the previous revision's local catalog in a temporary checkout, switched to the context module, rejected the stale saved plan, reinitialized, and produced a new plan with zero changes; destroyed the local fixture afterward |
| Trivy 0.76.1 quality smoke, both engines | Accepted safe source and binary plans; rejected open SSH, unsafe saved plans after source was fixed, and corrupt plans |
| TFLint 0.65.0 quality smoke, both engines | Accepted valid input and rejected invalid/unused variable declarations using bundled rules |
| Gitleaks 8.30.1 directory scan | No leaks found |
| Source-specific publication audit | No original organization names, account IDs, internal domains, or personal filesystem paths found |
| GitHub configuration files | YAML parsed successfully; referenced action revisions verified upstream |

Provider versions: AWS 6.71.0, AzureRM 5.12.0, and Google 8.9.0, installed from
the explicit OpenTofu registry addresses recorded in the committed lock files.
Cloud linter plugins: AWS 0.50.0, AzureRM 0.33.0, Google 0.41.0.
Python behavior tests passed on both Python 3.10 and 3.12.

Stack tests used mocked providers and plan-only runs. Security fixtures also created
AWS plans with fake credentials and disabled credential/metadata probes; they never
applied cloud resources. The only actual applies
and destroys were local `terraform_data` resources in disposable directories.
No AWS, Azure, or GCP infrastructure was deployed. Hosted GitHub Actions runs,
macOS execution, live authentication, and cloud recovery exercises remain to be
verified by adopters in their own environment.
