# aws/identity/github-actions-oidc

Stack that each `live/<environment>/aws/identity/github-actions-oidc` root calls as
`module "stack"`. Pass `context` from `modules/context`, `create_oidc_provider`, and
`roles`. Provider configuration and backend state belong to the calling root.

The OIDC provider and roles live in
[`modules/aws/github-actions-oidc`](../../../../modules/aws/github-actions-oidc),
called as `module "federation"`. The stack names each role
`<context.id>-<key>`, so the `deploy` role of `starter-github-dev` is
`starter-github-dev-deploy`. Roles of different environments therefore keep
distinct names when they share an account.

Set `audit_subjects` to add `<context.id>-audit`, a read-only role for Prowler account
scans that trusts only those exact subjects. `audit.tf` holds its managed policies and
inline additions. The list defaults to empty, which creates no audit role. See the
[Prowler integration](../../../../integrations/prowler/README.md).

The OIDC provider is account-global. Set `create_oidc_provider = true` in exactly
one deployment per AWS account and `false` in every other deployment that targets
the same account. Apply the deployment that creates the provider first.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
