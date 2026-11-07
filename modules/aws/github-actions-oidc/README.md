# aws/github-actions-oidc

Core module that lets GitHub Actions jobs assume AWS IAM roles through OpenID
Connect, without stored access keys. It owns the account's IAM OIDC provider for
`token.actions.githubusercontent.com` and one IAM role for each entry in `roles`.

An AWS account holds at most one OIDC provider for each issuer URL. With
`create_oidc_provider = true`, the default, the module creates that provider with
the `sts.amazonaws.com` audience. With `false`, it looks up the provider that
another deployment in the same account manages and trusts that one instead.

Each role's trust policy allows `sts:AssumeRoleWithWebIdentity` from the provider
only when the token's `aud` is `sts.amazonaws.com` and its `sub` is one of the role's
`subjects`. Both conditions use `StringEquals`. A role may also list
`subject_patterns`, which match `sub` with `StringLike` in a second statement that
keeps the same `aud` condition. IAM requires every condition in one statement to
match, so a separate statement adds the patterns to the exact subjects instead of
narrowing them.

| Input | Rule |
| --- | --- |
| `subjects` | `repo:<owner>/<repo>:ref:refs/heads/<branch>`, `repo:<owner>/<repo>:ref:refs/tags/<tag>`, or `repo:<owner>/<repo>:environment:<name>`, with no `*` or `?` |
| `subject_patterns` | The same forms with a nonempty branch, tag, or environment prefix and one trailing `*`, such as `repo:<owner>/<repo>:ref:refs/heads/release/*` |
| `subjects` and `subject_patterns` | At least one value per role |
| `name` | At most 64 letters, digits, or `+=,.@_-` characters |
| `max_session_duration` | 3600 to 43200 seconds. The default is 3600 |
| `managed_policy_arns` | Optional. Each ARN is attached to the role |
| `inline_policy_json` | Optional. Attached unchanged as the role's inline policy named `inline` |
| `permissions_boundary` | Optional policy ARN |

Validation rejects a bare `*`, a subject without a ref or environment,
`pull_request` subjects, and patterns such as `repo:<owner>/<repo>:*` or
`repo:<owner>/<repo>:ref:refs/heads/*` that would trust every branch. A subject
from a customized GitHub `sub` claim template passes only when it starts with one
of the accepted forms. GitHub sets the
`environment:<name>` subject for any job that names an environment, whatever
branch it runs on, so protect that environment with deployment branch rules.

The `oidc_provider_arn` output is the provider the roles trust. The `roles`
output maps each role key to its `arn` and `name`.

`stacks/aws/identity/github-actions-oidc` calls it as `module "federation"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
