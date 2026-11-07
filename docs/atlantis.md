# Enable Atlantis for a trusted repository

Atlantis runs native OpenTofu commands in each configured live root. The examples
use built-in init, plan, and apply with explicit quality checks. They do not deploy
an Atlantis server or configure cloud identities.

## Prepare the server

1. Install Atlantis 0.49.0 and Python 3.10 or later for the quality helper.
2. Install the pinned OpenTofu, Trivy, and TFLint versions from [mise.toml](../mise.toml).
3. Expose OpenTofu as `tofu1.12.5` on the server's `PATH` for Atlantis's pinned
   version discovery. Keep `tofu`, `trivy`, and `tflint` available for verification tools.
   Put the executables themselves on the Atlantis process's `PATH`. Do not expose mise
   or asdf shims, and do not run `mise activate` for that process. A shim selects its
   version from configuration in the current directory, which is the PR checkout.
4. Provide persistent storage for Atlantis's data directory and retained PR plans.
5. Configure least-privilege cloud and backend identities through [cloud setup](cloud-setup.md).

The server example sets `tf-download: false`. Install the pinned OpenTofu binary
before starting Atlantis. Ordinary local deployment commands have no Atlantis or
Python dependency. The server quality steps require Python and the scanner tools.

Optional local installation through mise, for workstations and CI only:

```sh
mise trust
mise install
mise trust integrations/atlantis/mise.toml
mise -C integrations/atlantis install
```

Review the [Atlantis 0.49.0 release notes](https://github.com/runatlantis/atlantis/releases/tag/v0.49.0)
before changing its pin.

## Install server-owned policy

1. Copy [repos.yaml.example](../integrations/atlantis/repos.yaml.example) and
   [server.yaml.example](../integrations/atlantis/server.yaml.example) outside PR checkouts.
2. Replace `REPLACE_OWNER/REPLACE_REPOSITORY` with the exact trusted repository in both files.
3. Point `repo-config` at the installed server repository policy.
4. Keep `allowed_overrides` empty and `allow_custom_workflows` false.
5. Keep the `foundation` workflow and its `approved`, `mergeable`, and `undiverged` apply requirements.
6. Configure the VCS identity and webhook secret through your secret manager.
7. Configure HTTPS, authenticated web access, branch protection, and required CI checks.
   Replace the team in [CODEOWNERS](../.github/CODEOWNERS) and require Code Owner review.
8. Dismiss stale approvals on new commits and keep `checkout-strategy: merge`.

```sh
atlantis server --config /etc/atlantis/server.yaml
```

Keep `allow-fork-prs: false`. Restrict command authors with VCS permissions and
Atlantis team allowlists. Server-owned workflow definitions still execute reviewed
repository code, providers, and the quality helper. Apply approval alone does not
make an untrusted plan safe.

The quality helper, its tool pins, and its lint rules come from the PR checkout.
A PR can change the policy that checks it. The plan stage runs that changed policy.
Code Owner review protects the policy files in the reviewed commit. GitHub does not
report the PR as mergeable until the owning team approves, so the `mergeable`
requirement blocks apply. Plan-stage code runs in the same checkout and can still
change files on disk before apply. See [Atlantis security](https://www.runatlantis.io/docs/security.html).

## Activate selected deployments

Configure live inputs and remote backends before activation. Complete
[bootstrap](bootstrap.md) independently. Bootstrap cannot be selected for Atlantis.

The checked-in [project example](../integrations/atlantis/atlantis.yaml.example)
is usable as a starting configuration without generation. To generate one selected project:

```sh
python3 tools/atlantis.py --deployment dev/aws/network/core --output atlantis.yaml
```

Repeat `--deployment` for more targets. Omitting it selects remote workload roots
and excludes local and bootstrap roots. Review and commit `atlantis.yaml` in your
adopted repository. The template leaves the active root file absent.

Request a plan in a PR:

```text
atlantis plan -p dev/aws/network/core
```

Review the plan and satisfy server requirements before requesting apply:

```text
atlantis apply -p dev/aws/network/core
```

The plan stage uses built-in init and plan. The quality steps scan root source
and Atlantis's saved `PLANFILE`. The apply stage scans source and the same saved plan before
the built-in apply step. Additional comment arguments are rejected. Preserve this ownership when customizing the workflow.
Do not mix the old adapter with native plan or apply steps.

Native operations do not recreate former checkout fingerprints or plan receipts.
Bind approval to the reviewed change through trusted server policy, branch protection,
and plan handling. Retain the checkout and plan until apply or cancellation.

To enable automatic plans, generate with `--autoplan` and set `disable-autoplan`
to false after the trust and authentication controls are ready. Automatic merge
and automatic apply remain disabled.

## Update the project inventory

After adding or removing roots, regenerate active projects with the same selection
and options. Add the matching check command to your adopted repository's CI.

```sh
python3 tools/atlantis.py --output integrations/atlantis/atlantis.yaml.example
python3 tools/atlantis.py --output integrations/atlantis/atlantis.yaml.example --check
```

`python3 tools/check.py` checks the default example. Watch patterns cover root HCL,
inputs, provider locks, the HCL of every local module the root reaches (its stack,
`modules/context`, and any core modules the stack calls), quality policy, tool pins,
and active configuration.
See the [integration reference](../integrations/atlantis/README.md).

## Verify without cloud credentials

```sh
mise -C integrations/atlantis exec -- python3 ../../tools/atlantis_native_smoke.py
```

The test starts the real Atlantis server with the example configuration and
executes its exact configured security commands against safe and unsafe fixtures.
Those fixtures create plans with fake credentials and never apply cloud resources.
The separate `python3 tools/smoke.py` test verifies the native local lifecycle.
The Atlantis check does not execute hosted plan or apply events or prove approval
enforcement in your VCS. Verify those when connecting the trusted repository.

An explicit local project is available for a separate server demonstration:

```sh
python3 tools/atlantis.py --deployment dev/local/foundation/catalog --output atlantis.yaml
```

Use a disposable repository and retain its local state until cleanup.
