# Publish your template

Prepare the checkout locally before creating a public repository.

1. Review the MIT license and set the repository name, description, maintainers,
   and private security reporting channel.
2. Inspect tracked files and history for credentials, state, plans, account-specific
   values, internal domains, and proprietary material. Run both Gitleaks scans.
3. Run the [documented checks](verification.md), local lifecycle, and migration fixtures.
   Review provider constraints and root lock files.
4. Create the public repository and push the reviewed files. Enable GitHub's
   **Template repository** setting if users should generate independent copies.
5. Enable private vulnerability reporting and branch protection. Require the
   OpenTofu checks and secret scan. Disable force pushes to the default branch.
   Replace the team in `.github/CODEOWNERS` and require Code Owner review.
6. Run hosted CI and review its results before tagging a release. A checked-in
   workflow is not evidence that a hosted run passed.

Example account and project IDs are placeholders. They are not credentials or
a deployment identity. Keep `.infra/`, native working directories, state, and
saved plans out of releases and repository history.

Read [security policy](../SECURITY.md) before enabling cloud credentials. Local
native commands do not enforce the previous repository approval or fingerprint
checks. Trusted automation must enforce scans and approvals.

Mock tests do not prove cloud deployment readiness. Exercise sandbox deployment,
migration, and recovery with your own identities before enabling production changes.
