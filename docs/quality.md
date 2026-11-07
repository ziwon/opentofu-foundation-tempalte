# Run quality and security checks

Repository checks are optional local developer tools and required CI checks.
They use Python 3.10 or later, OpenTofu, and the tool versions in `mise.toml`.
Ordinary native deployment commands do not call these helpers automatically.

```sh
python3 tools/check.py
python3 tools/quality.py lint live/dev/aws/storage/bucket
python3 tools/quality.py source live/dev/aws/storage/bucket
python3 tools/quality.py plan live/dev/aws/storage/bucket live/dev/aws/storage/bucket/plan.tfplan
```

`check.py` checks the layout and documentation links, Python behavior tests,
formatting, provider validation, lint, source security, and mocked tests.
Cloud tests are plan-only. `check.py` isolates its native working directories
from each root's operational backend metadata. Use the same separation for
manual backend-free validation in an operational checkout.

## Lint and source scans

TFLint uses its recommended language rules and the selected cloud's pinned rules.
`.tflint.hcl` pins the AWS, AzureRM, and Google plugins. Initial tool, plugin, and
provider downloads need network access. The checks do not require cloud credentials.
CI provides a read-only GitHub token for plugin downloads to avoid shared-IP rate limits.

Trivy checks the source with the root's input values and follows its local modules.
The helper checks that the scanner and linter report the versions pinned in `mise.toml`.
It cannot prove that the executable is genuine, so trusted automation must own the
executables on its `PATH`.
Trivy uses bundled checks and disables automatic check updates. Each scan uses a
new temporary cache, so cached checks or modules in the checkout cannot replace them.
Updating Trivy is a reviewed policy change.

## Scan the saved plan

Scan the actual saved binary plan after planning and again before an approved apply.
The Atlantis workflow passes its native `PLANFILE` to the helper. Scanning only
the current source does not inspect a plan created from earlier or different source.

The helper rejects HIGH and CRITICAL misconfigurations. It also requires recognized
checks from the expected source or plan scanner. Missing tools, corrupt plans,
malformed reports, and unrecognized inputs cannot silently pass. Only diagnostic
check IDs are printed. Raw reports and configuration values stay in memory.

Global Trivy configuration, ignore files, `TRIVY_*` overrides, telemetry, and
automatic check downloads are disabled. Trivy removes suppressed findings from
its report, so the helper rejects inline `trivy:ignore` and `tfsec:ignore` comments.
A source scan checks every `.tf` and `.tf.json` file in the repository. A plan scan
checks the configuration embedded in the saved plan, including downloaded modules.
To accept a finding, change the quality policy in a reviewed pull request.
Create a new plan after changing source, inputs, or quality policy.

Native `tofu plan` and `tofu apply` do not enforce these checks. Trusted automation
must run them as explicit steps and stop on failure. The helper does not approve
plans, bind them to a commit, remove artifacts, or perform infrastructure operations.
See [deployment policy](../SECURITY.md).

## Prove acceptance and rejection

```sh
python3 tools/quality_smoke.py
python3 tools/smoke.py
python3 tools/migration_smoke.py
```

The quality fixture tests safe and unsafe AWS source and saved plans with fake
credentials and disabled identity probes. It never applies cloud resources.
It checks that open SSH fails, that a saved unsafe plan still fails after source is
fixed, that corrupt plans fail, and that invalid lint input fails.

The local lifecycle fixture applies and destroys only disposable `terraform_data`
resources. The migration fixture starts from the [frozen legacy catalog](../tests/fixtures/legacy-local/README.md)
and supplies the same frozen inputs to the old and current HCL. It checks that
dev and prod keep their resource IDs, typed outputs, and state paths while recording address moves with no resource changes. Dev moves from the
shared-stack address. Prod first moves to the native-root address `module.stack.terraform_data.catalog`,
so the check also covers the stack's move into its core module. It works in a new
repository created from this template without the original Git history.

Gitleaks remains a separate secret scan:

```sh
gitleaks dir . --redact --no-banner
```

A clean scan does not establish account security or organization-specific compliance.
