# Scan an AWS account with Prowler

This optional integration runs Prowler 5.48.0 from GitHub Actions against a live AWS
account. The template's checks, CI, and Atlantis workflow do not use it. The identity
roots create no audit role until you set `audit_subjects`, and no workflow runs until
you copy the example into `.github/workflows/`.

**Verification status.** The audit role's plan and the workflow syntax are checked
offline. Neither has run against a live AWS account. Test the workflow in a sandbox
account before you rely on its reports.

Prowler calls read-only AWS APIs and reports how the account is configured. Version
5.48.0 has 672 AWS checks across 90 services, such as IAM password policy, root
account MFA, public S3 buckets, CloudTrail coverage, and unencrypted volumes. It maps
them to frameworks that include the CIS AWS Foundations Benchmark and AWS Foundational
Security Best Practices. Run `prowler aws --list-checks` or `prowler aws --list-compliance`
for the full lists.

## How Prowler differs from the Trivy gate

`tools/quality.py` runs Trivy on source and saved plans before apply, with no cloud
credentials. It blocks HIGH and CRITICAL findings in trusted automation. See
[quality checks](../../docs/quality.md).

Prowler reads what exists in the account after apply. That includes resources created
in the console, by other tools, or by roots outside this repository. It needs
credentials for the account, and this integration reports its findings without
blocking anything. Neither check replaces the other.

## Install the pinned CLI

The pin lives in this directory's `mise.toml`, so a plain `mise install` at the
repository root does not download Prowler. The `pipx` backend uses `uv` or `pipx`,
and Prowler 5.48.0 needs Python 3.10 to 3.13.

```sh
mise -C integrations/prowler install
mise -C integrations/prowler exec -- prowler --version
```

A local scan is a real cloud operation that uses your own credentials. The audit role
trusts only GitHub Actions, so do not widen its trust for a workstation.

## Create the audit role

1. In the identity root for the account to scan, set `audit_subjects` in
   `terraform.tfvars.json`. For prod, edit
   `live/prod/aws/identity/github-actions-oidc/terraform.tfvars.json`:

   ```json
   "audit_subjects": [
     "repo:REPLACE_ME_GITHUB_OWNER/REPLACE_ME_GITHUB_REPOSITORY:environment:security-audit"
   ]
   ```

2. Plan the root and review the plan. It adds
   `module.stack.module.federation.aws_iam_role.this["audit"]`, two managed policy
   attachments, and one inline policy. Apply it through your normal reviewed process.
3. Read the role ARN from the `audit` entry:

   ```sh
   tofu -chdir=live/prod/aws/identity/github-actions-oidc output roles
   ```

To scan more than one account, set `audit_subjects` in each account's identity root.

The role is named `<deployment name>-audit`, such as `starter-github-prod-audit`. The
`audit` key in `roles` is reserved while `audit_subjects` is set. The role has these
permissions:

- Its trust policy matches the token's `sub` against `audit_subjects` with
  `StringEquals`. The role has no prefix patterns, and the
  [module's validation](../../modules/aws/github-actions-oidc/README.md) rejects wildcards.
- It attaches `arn:aws:iam::aws:policy/SecurityAudit` and
  `arn:aws:iam::aws:policy/job-function/ViewOnlyAccess`, the managed policies that
  [Prowler's AWS authentication guide](https://docs.prowler.com/user-guide/providers/aws/authentication)
  requires.
- Its inline policy is the guide's
  [`prowler-additions-policy.json`](https://github.com/prowler-cloud/prowler/blob/8a5aebb8a8c34dcecd17eba79466b94226440804/permissions/prowler-additions-policy.json)
  at 5.48.0, without `securityhub:BatchImportFindings`. That action is a write that
  only Prowler's `--security-hub` output uses.
- Its sessions last up to two hours, because a scan of every region can take more
  than one hour.

The additions read more than metadata. `lambda:GetFunction*` returns function code
locations and environment variables, `ecr:BatchGetImage` and
`ecr:GetDownloadUrlForLayer` read image layers, `logs:FilterLogEvents` reads log
contents, and `glue:GetConnections` can return Glue connection passwords in plain text. Prowler uses them to look for secrets. Give the role to the scan job only,
never to a deployment job.

## Create the security-audit environment

Create the environment before you copy the workflow. GitHub creates a missing
environment the first time a job names it, and that environment has no protection rules.

1. In the repository settings, open **Environments** and create `security-audit`.
2. Under **Deployment branches and tags**, choose **Selected branches and tags** and
   add only the default branch.

GitHub gives the `environment:security-audit` subject to any job that names the
environment, from any branch. The branch rule is what keeps the role to reviewed code
on the default branch. If you add required reviewers, each scheduled run waits for approval.

## Copy the workflow

```sh
cp integrations/prowler/prowler.yml.example .github/workflows/prowler.yml
```

In the copy, set `AWS_ROLE_ARN` to the audit role ARN and `AWS_REGION` to a region
that the account has enabled. The workflow has these properties:

- It runs when you start it and every Monday at 03:17 UTC. Delete the `schedule`
  trigger to run it only on demand.
- It grants only `id-token: write` and `contents: read`.
- `jdx/mise-action` installs only Prowler, at the version in this directory's `mise.toml`.
- `aws-actions/configure-aws-credentials` assumes the audit role for two hours.
- `prowler aws` scans every region and writes CSV, HTML, and JSON-OCSF reports.
- The reports upload as the artifact `prowler-<run ID>-<attempt>`, even when the scan fails.

Each action is pinned to a full commit SHA. Dependabot updates the pins once the copy
is in `.github/workflows/`. It does not update the Prowler version in `mise.toml`.

Start a scan with `gh workflow run prowler.yml`, or with **Run workflow** on the
workflow's Actions page.

## Handle the reports

The reports list account IDs, resource names and ARNs, regions, and every failed
check. Together they map the account and its weak points. Treat them like state files.

- The artifact expires after 7 days. Your repository or organization may set a lower
  maximum. Delete it sooner from the run page if you no longer need it.
- Anyone with read access to the repository can download artifacts and read the job
  log, which includes Prowler's summary table. In a public repository, that is every
  signed-in GitHub user. Run the workflow only in a private repository, or remove the
  upload step.
- Do not commit reports or paste them into issues or pull requests.

## Treat findings as advisory

The workflow passes `--ignore-exit-code-3`. Without that flag, Prowler exits with
code 3 when any check fails. With it, failed checks leave the job green. The job
fails only when Prowler, the role, or the runner fails.

To fail the workflow on findings, remove `--ignore-exit-code-3`. To fail only on
severe findings, also add `--severity critical high`. That flag limits which checks
run, so the reports then omit lower severities.

A scan with no failed checks does not prove that the account is secure or compliant.
Some checks report `MANUAL` and need a person to review them.

## Upgrade Prowler

1. Raise the version in `integrations/prowler/mise.toml`.
2. Compare `permissions/prowler-additions-policy.json` at the new release tag with the
   inline policy in [`audit.tf`](../../stacks/aws/identity/github-actions-oidc/audit.tf).
   Update the policy, the version in its comment, and the link in this file.
3. Check the workflow's flags against `prowler aws --help`.
4. Plan and apply each identity root that sets `audit_subjects`.

## What this integration leaves out

The workflow does not summarize reports, open issues, send findings to Security Hub or
S3, or upload to Prowler Cloud. Add those in your copy if you need them, and give any
job that writes to issues its own permissions without the audit role.
