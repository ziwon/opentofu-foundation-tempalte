# Publish your template

This checkout can be prepared locally without creating a remote repository.
Before making a fork public:

1. Read the MIT license and set the repository name, description, maintainers,
   and support/security reporting channels for your project.
2. Inspect every tracked file and the Git history for credentials, state, plans,
   account-specific details, internal domains, and proprietary material. Run
   Gitleaks on both the directory and history. A clean secret scan is only one
   part of that review.
3. Run the documented checks and local smoke test with both engines. Review
   any provider-version or lock-file changes.
4. Create a public repository, push the reviewed files, and enable GitHub's
   **Template repository** setting if users should generate independent copies.
5. Enable private vulnerability reporting and configure repository rules to
   require `check (tofu)`, `check (terraform)`, and `secrets` when supported by
   your GitHub plan. Disable force pushes to the default branch.
6. Run hosted CI, review the results, then tag the first release. The included
   workflow definitions are not evidence that a hosted run has happened.

Examples contain placeholder account/project IDs. They deliberately do not contain
working credentials, a deployment identity, or automatically provisioned remote
state. Keep the local `.infra/` directory out of releases and repository history.

Do not infer cloud deployment readiness from mock tests. An organization adopting
this template should perform a sandbox deployment and recovery exercise with its
own identities and policies before enabling production changes.
