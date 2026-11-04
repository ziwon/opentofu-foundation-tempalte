# Quality and security checks

`check` runs layout/link checks, Python behavior tests, formatting, provider validation,
TFLint, Trivy source scans, and mocked plans for every live deployment. Both engines
use that command in CI. Tools are pinned in `mise.toml`; cloud linter plugins are
pinned in `.tflint.hcl`.

```sh
mise exec -- just lint dev/aws/storage/bucket
mise exec -- just security dev/aws/storage/bucket
mise exec -- just security-plan dev/aws/storage/bucket
mise exec -- just check
```

`lint` enables the selected cloud's AWS, AzureRM, or Google rules, plus TFLint's
recommended language rules and local-module checking. Plugin installation uses a
project-local cache and a lock. Initial tool/plugin/provider downloads need network
access, but these checks need no cloud credentials.
CI supplies its read-only GitHub token for plugin downloads to avoid shared-IP API
limits. The language-only smoke fixture uses bundled rules without downloading
cloud plugins. See [TFLint rate limiting](https://github.com/terraform-linters/tflint/blob/v0.65.0/docs/user-guide/plugins.md#avoiding-rate-limiting).

## Saved-plan security gate

`plan` scans the actual binary plan before saving a successful receipt. `apply`
verifies the receipt, scans that same plan again, and verifies it again before
invoking the engine. `--yes` only skips the deployment-name prompt; it never skips
verification or scanning. An explicitly requested `security --plan` uses the same gate.

The Trivy gate blocks HIGH and CRITICAL misconfigurations. It requires the expected
source or snapshot scanner to report recognized checks, so a missing tool, corrupt
plan, malformed report, or unrecognized input cannot silently pass. A failed `plan`,
including its security scan, removes both the plan and receipt. Only diagnostic check IDs are printed;
raw reports and source values remain in memory and are never written to report files.
Look up an ID in [Trivy's check catalog](https://avd.aquasec.com/misconfig/) to investigate.

The runner verifies the installed scanner/linter versions against `mise.toml`.
Trivy uses its bundled checks with updates disabled and a version-specific local
cache; updating Trivy is a reviewed policy change. Global config/ignore files,
`TRIVY_*` overrides, telemetry, and automatic check downloads are disabled.
There are no blanket suppressions in this template. If an exception is needed,
use a narrowly scoped, reviewed inline Trivy ignore with a reason and expiry.
Inline exceptions are part of the HCL and therefore invalidate an existing plan.
Changes to tool versions, lint configuration, or the security runner also require
a fresh plan. These checks do not replace account audits or organization-specific policy.

Gitleaks remains a separate secret scan. A clean secret scan does not imply that
resource permissions or network exposure are safe.

## Reproduce the checks

```sh
python3 tools/infra.py check
python3 tools/infra.py --engine terraform check
python3 tools/smoke.py --engine tofu
python3 tools/smoke.py --engine terraform
python3 tools/quality_smoke.py --engine tofu
python3 tools/quality_smoke.py --engine terraform
```

The lifecycle smoke applies/destroys only temporary local `terraform_data` resources
and verifies environment-specific state queries. The quality smoke creates safe and
unsafe AWS fixtures, using fake credentials and disabled identity/metadata probes
only inside temporary fixtures. It never applies them or uses real cloud credentials.
It verifies rejection of open SSH in source and binary plans, even when source is
fixed after planning, corrupt plans, and invalid lint inputs.

See [Trivy Terraform support](https://trivy.dev/docs/latest/coverage/iac/terraform/)
and [TFLint documentation](https://github.com/terraform-linters/tflint).
