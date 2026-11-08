# Operate a deployment

## Select a context

A context is a `.env.<name>` file that sets `DEPLOY_ENV`, `DEPLOY_CLOUD`, and the
variables your cloud CLI reads. The repository ships examples for each cloud:

```sh
cp .env.aws.dev.example .env.aws.dev
```

Set the CLI variables in the copy. AWS uses `AWS_PROFILE` and `AWS_REGION`, Azure can
use `AZURE_CONFIG_DIR`, and GCP uses `CLOUDSDK_ACTIVE_CONFIG_NAME`. Then select it:

```sh
just use aws.dev   # or `just use` to pick from a numbered list
```

`just use` points `.env` at the file. `just` loads `.env` into every recipe, so root
recipes take `<group> <stack>` and fill in the environment and cloud. Run
`direnv allow` once if you want your shell to load the same variables for native
`tofu` commands. Context files are ignored by Git.

A context does not hold account IDs, expected regions, or state buckets. Those stay in
each root's `terraform.tfvars.json` and `backend.tf`, so a context cannot point a root
at different state.

Before a root recipe runs `tofu`, `tools/context.py` prints the context, the stack,
the root, the backend, the state key or path, and the OpenTofu data directory. It
stops when any of these is true:

- The context file still has a `REPLACE_ME` value, or names an environment and cloud
  with no roots.
- A value uses `$`, `\`, or a trailing `# comment`. `just` would expand or strip these,
  so write plain values, such as an absolute path.
- The selected `.env.<name>` file was deleted, or the repository has no `.env` but a
  parent directory does. `just` searches parent directories for `.env`.
- A full target such as `prod/aws/network/core` is outside the selected context.
- Your shell already sets a credential variable to a value other than the context's,
  for example from an earlier `direnv` load. `just` does not override shell variables.

`init`, `plan`, `destroy-plan`, `apply`, `output`, and the state recipes also run the
preflight below. `validate`, `test`, `lock`, and `cost` need no cloud login and skip it.
Every root recipe also accepts the full `<environment>/<cloud>/<group>/<stack>` path.
Without a context, any root works. With one, the path must be inside it. A `.env`
that you wrote by hand is loaded by `just` but is not a context, so only full paths work.

## Check your identity before planning

Before you plan a cloud root, confirm that your terminal is logged in to the
account, subscription, or project that the root expects:

```sh
just preflight dev/aws/network/core
```

`just preflight` prints the context summary and runs the same check as
`python3 tools/preflight.py dev/aws/network/core`. The check
reads the root's `terraform.tfvars.json` and `backend.tf`, then asks the installed
`aws`, `az`, or `gcloud` CLI for the active identity. It prints one line for each
mismatch, with the active value and the value the root expects, and exits with code 1.
It also fails when the root still has placeholder values such as `000000000000` or
`REPLACE_ME_STATE_BUCKET`, when the CLI is not installed, or when you are not logged in.
Local roots have nothing to check. [Cloud setup](cloud-setup.md#check-your-identity-before-planning)
lists the values it compares for each cloud.

The preflight reads files and CLI output only. It never runs `tofu`, so it does not
initialize, plan, or touch state. The root recipes that use credentials run it first.
Native `tofu` commands do not, and keep working without Python or `just`.

## Plan and apply a normal change

Edit a root's inputs or its stack. Run the relevant checks, initialize
that root, and save a plan. The following commands run from the repository root:

```sh
tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
tofu -chdir=live/dev/aws/network/core test
tofu -chdir=live/dev/aws/network/core plan -out=plan.tfplan
tofu -chdir=live/dev/aws/network/core show plan.tfplan
```

Review the complete plan and obtain your deployment approval before applying it:

```sh
tofu -chdir=live/dev/aws/network/core apply plan.tfplan
```

Applying a saved plan has no confirmation prompt. Native commands run no
approval checks or automatic security scans. Use [trusted automation](atlantis.md) when those scans and approvals
must be enforced. The [quality helper](quality.md) can also scan a local source tree
and saved plan explicitly.

To estimate the cost of a saved plan, see the optional
[Infracost integration](../integrations/infracost/README.md). Its estimates are advisory.

Use the default workspace. Keep credentials in native cloud authentication, and
avoid hidden variable or CLI overrides when working from reviewed inputs.
Initialization with `-lockfile=readonly` preserves committed provider selections.
If you request `-detailed-exitcode` for planning, exit code 2 means changes are present.

## Inspect outputs and state

```sh
tofu -chdir=live/dev/local/foundation/catalog output
tofu -chdir=live/dev/local/foundation/catalog state list
tofu -chdir=live/dev/local/foundation/catalog state show module.stack.module.catalog.terraform_data.catalog
```

Initialize the root before reading its state. Quote addresses with map keys,
for example `'module.stack.aws_instance.worker["blue"]'`.
State and JSON output can expose sensitive attributes. Use an authorized terminal
and keep the output out of public logs and committed files.

## Recover from a failed command

Inspect OpenTofu's output and actual state before retrying. A partial apply may
have changed resources. Do not delete state to retry.

Native commands do not remove old saved plans after failed plans or apply attempts.
Discard obsolete plan files and create a fresh plan after any failure, source
change, input change, provider update, or policy change. Native state checks do not
bind a saved plan to the current source checkout.

## Retire a deployment

The following example affects only the local catalog:

```sh
tofu -chdir=live/dev/local/foundation/catalog plan -destroy -out=destroy.tfplan
tofu -chdir=live/dev/local/foundation/catalog show destroy.tfplan
tofu -chdir=live/dev/local/foundation/catalog apply destroy.tfplan
```

Review destruction separately from ordinary changes. Storage examples retain data,
use `prevent_destroy`, or refuse nonempty bucket deletion. Keep the live directory
and state until retirement and recovery requirements are satisfied. Bootstrap
retirement requires a separate review after all consumers move to another backend.

## Update providers

Each root's `versions.tf` pins an exact provider version, and its lock file records
that selection. Stacks and core modules accept a range within the current major
version, such as `>= 6.71.0, < 7.0.0`, so a minor or patch update changes only
roots. Dependabot watches the roots for this reason. A major update also needs
the range widened in every stack and core module that uses the provider, after
you review their code against the provider's upgrade guide.

Change the pin in each affected root, then resolve and review its lock file:

```sh
tofu -chdir=live/dev/aws/network/core init -backend=false -upgrade
tofu -chdir=live/dev/aws/network/core providers lock
tofu -chdir=live/dev/aws/network/core test
```

Use a disposable checkout or separate `TF_DATA_DIR` for backend-free checks so they
do not disturb an operational root's initialized backend. Commit version and lock
changes together. Review provider migration notes and a fresh plan against existing state.
Mock tests do not prove live-state compatibility.

Provider sources explicitly use `registry.opentofu.org`. Preserve these identities
when moving code. Changing a registry address is a separate provider/state migration.
OpenTofu is the supported CLI.

## Change a backend

To move a root's state to different storage:

1. Stop concurrent operations and obtain authorization for the state migration.
2. Back up the current state securely and verify the old and new storage identities.
3. Retain the initialized root's backend metadata while editing `backend.tf`.
4. Follow OpenTofu's `init -migrate-state` procedure and review every migration prompt.
5. Verify the destination state and review a fresh plan before resuming deployments.

Do not use `-reconfigure` as a substitute for copying state. Pointing at an empty
backend can make existing resources appear unmanaged. See
[OpenTofu initialization](https://opentofu.org/docs/cli/commands/init/).

## Configure deployment automation

The supplied CI is credential-free. Deployment workflows need trusted source,
short-lived cloud identity, explicit approvals, deployment-scoped permissions,
and one concurrency boundary per state. Bind approval to the reviewed commit and
plan artifact. Treat saved plans as confidential and limit their access and retention.

The [Atlantis integration](atlantis.md) keeps approvals in server-owned configuration.
It uses native init, plan, and apply with source and saved-plan checks. Keep fork
PRs disabled and retain the trusted repository and author boundary. Do not execute
untrusted PR code with deployment credentials.
