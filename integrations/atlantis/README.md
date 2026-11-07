# Atlantis integration reference

This optional integration targets Atlantis 0.49.0 and OpenTofu 1.12.5. The project
directory is the native live root. See [Atlantis setup](../../docs/atlantis.md).

| File | Purpose |
| --- | --- |
| `atlantis.yaml.example` | Checked-in cloud workload projects |
| `repos.yaml.example` | Server-owned native workflow and apply requirements |
| `server.yaml.example` | Server flags with fork PRs, automatic plans, and automatic merge disabled |
| `mise.toml` | Optional integration verification tool pins |

## Optional project generator

`python3 tools/atlantis.py` prints JSON-formatted YAML, which Atlantis accepts.
The checked-in example can be used without running the generator.

| Option | Meaning |
| --- | --- |
| `--deployment <ID>` | Select a root explicitly. Repeat for more projects. |
| `--autoplan` | Enable project automatic plans. The server must also permit them. |
| `--output <path>` | Write the generated configuration. |
| `--check` | Compare `--output` with the selected configuration without writing. |

The default selection includes remote workload roots. It excludes bootstrap and
local backends. Explicit selection permits a local catalog demonstration.
Bootstrap is always excluded. Regenerate with the same selection and autoplan option.

Each project uses its deployment ID as its name, `live/<ID>` as its directory,
the default workspace, and the pinned OpenTofu distribution and version.
Watch patterns include the root's HCL, input JSON, provider lock, every local module
the root reaches through module calls, quality helper and policy, tool pins, and
active Atlantis configuration.

## Native workflow

The server workflow uses built-in `init`, `plan`, and `apply` steps. Quality steps
run from the native live root and scan source plus the saved `PLANFILE`.
The helper reports policy failures and never initializes, plans, or applies infrastructure.

Atlantis owns the saved plan, project locks, plan status, and apply requirements.
Native backend locking still protects the state. Plans and applies are serial by
default. The server keeps `approved`, `mergeable`, and `undiverged` requirements,
disables custom workflows and overrides, and restricts repository access. Additional comment arguments are rejected.

Native saved-plan checks do not establish approval of current source. Trusted server policy, VCS permissions,
branch protection, and protected plan handling provide the deployment boundary.

The server installs the pinned OpenTofu executable as `tofu1.12.5` because automatic
binary downloads are disabled. Python, Trivy, and TFLint are required by explicit
quality steps. They are not prerequisites for ordinary local `tofu` commands.
Install them as server-owned executables, not version-manager shims. See
[what the checks trust](../../docs/atlantis.md#know-what-the-checks-trust).

See the [server policy example](repos.yaml.example), [quality checks](../../docs/quality.md),
and [security policy](../../SECURITY.md).
