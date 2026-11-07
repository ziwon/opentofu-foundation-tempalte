# Cloud setup

The committed values are examples, not working account credentials. Configure
each environment explicitly. Create remote-state storage separately from these
workload roots so deleting an application cannot delete its own state.
The [bootstrap roots](bootstrap.md) provide an explicit, reviewed way to create
that storage for AWS, Azure, and GCP.

## State storage checklist

Use private storage with encryption, versioning/retention, and least-privilege
access. Keep a recovery path independent of the workload being managed. Separate
storage and identities across trust boundaries. Never put passwords, access keys,
service-account JSON, tokens, SAS URLs, or encryption keys in `backend.tf`.

Each root declares its complete backend in `backend.tf`, including an explicit
key, prefix, or local path. Keep those values once a deployment has state.
Replace storage placeholders before initialization. Native `tofu init` connects
to that backend through its normal authentication mechanism.

## AWS

1. Create a private S3 state bucket in the intended account/region. Enable
   versioning, default encryption, public-access blocking, and a TLS-only policy.
2. Grant the operator access to that bucket and deployment prefix. S3 locking
   additionally needs `GetObject`, `PutObject`, and `DeleteObject` on `.tflock`
   objects. Consult the [backend permission examples](https://opentofu.org/docs/language/settings/backends/s3/).
3. Configure AWS CLI SSO or a role-based credential chain. For GitHub Actions,
   [assume a role through OIDC](#let-github-actions-assume-an-aws-role).
4. Set `aws_account_id` and `region` in the deployment's `terraform.tfvars.json`.
   Set the backend bucket, region, and `allowed_account_ids` in `backend.tf`.

```sh
aws sso login --profile your-profile
AWS_PROFILE=your-profile tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
AWS_PROFILE=your-profile tofu -chdir=live/dev/aws/network/core plan -out=plan.tfplan
```

The AWS provider checks `allowed_account_ids` independently of the backend's
state-account restriction. They may intentionally be different accounts.

The network example has no Internet gateway, NAT gateway, public IP, or compute.
The default security group denies both directions. Add workload security groups,
routes, and VPC flow logs deliberately. The storage example enables SSE-KMS with
a rotating customer-managed key,
versioning, TLS-only access, bucket-owner enforcement, and public-access blocking.
Add access logging, retention/lifecycle rules, and
replication where your requirements call for them. Nonempty buckets resist
deletion, and `prevent_destroy` in `modules/aws/s3-bucket` and `modules/aws/kms-key`
makes any plan that destroys the bucket or key fail. That is not a backup or retention policy.

### Let GitHub Actions assume an AWS role

The `live/<environment>/aws/identity/github-actions-oidc` roots create IAM roles
that GitHub Actions jobs assume with short-lived OIDC tokens instead of stored keys.
See [`modules/aws/github-actions-oidc`](../modules/aws/github-actions-oidc/README.md)
for the trust policy and the subject forms it accepts.

1. In the root's `terraform.tfvars.json`, replace `REPLACE_ME_GITHUB_OWNER` and
   `REPLACE_ME_GITHUB_REPOSITORY` in each role's `subjects`, and set `aws_account_id`.
2. Give each role only the permissions its jobs need, through `managed_policy_arns`,
   `inline_policy_json`, or both. The example `deploy` role has no permissions.
   The Trivy source and saved-plan scans do not judge what a role may do, and an
   `"Action": "*"` inline policy passes both. Review role permissions in the PR,
   and set `permissions_boundary` to cap what a role can grant itself.
3. Set `create_oidc_provider` to `true` in exactly one root per AWS account. An
   account holds one provider for `token.actions.githubusercontent.com`, so set
   `false` in every other root that targets the same account, and apply the root
   that creates the provider first. Destroying that root removes the provider
   that the other roots' roles trust.
4. Review and apply the root's plan, then read the role ARN with
   `tofu -chdir=live/dev/aws/identity/github-actions-oidc output roles`.
5. In the workflow, grant `id-token: write` and pass the ARN as `role-to-assume`:

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd # v6.3.0
        with:
          role-to-assume: arn:aws:iam::000000000000:role/starter-github-dev-deploy
          aws-region: us-east-1
      - run: aws sts get-caller-identity
```

A prefix in `subject_patterns` matches every value that starts with it, so
`ref:refs/heads/main*` also matches a branch named `main-test`. End branch prefixes
with `/`, such as `ref:refs/heads/release/*`. A `pull_request_target` job presents the
base branch's subject, so a role trusting `ref:refs/heads/main` also trusts those jobs.

A job that sets `environment: dev` presents the subject
`repo:<owner>/<repo>:environment:dev`. A job without an environment that runs
for a branch push presents `repo:<owner>/<repo>:ref:refs/heads/<branch>`. The role trusts only the subjects
listed in its `subjects` and `subject_patterns`. Restrict which branches can deploy
to a GitHub environment with its deployment branch rules.

To scan an account with Prowler, set `audit_subjects` in its identity root. The root
then adds a read-only `<deployment name>-audit` role. The
[Prowler integration](../integrations/prowler/README.md) has the role's permissions
and a workflow example.

## Azure

1. Register the required resource providers in the target subscription outside
   this template. The provider does not automatically register them.
2. Create a state resource group, storage account, and private Blob container.
   Enable versioning and appropriate soft-delete/retention settings.
3. Grant the state identity **Storage Blob Data Contributor** at the appropriate
   scope, plus any control-plane read permissions needed for endpoint discovery.
   Configure Microsoft Entra authentication rather than account keys.
4. Set `subscription_id` and `location` in `terraform.tfvars.json`. Set the state
   resource group, storage account, container, and state subscription in `backend.tf`.

```sh
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
tofu -chdir=live/dev/azure/network/core init -lockfile=readonly
tofu -chdir=live/dev/azure/network/core plan -out=plan.tfplan
```

For automation, use workload identity federation. Consult the
[Azure backend authentication modes](https://opentofu.org/docs/language/settings/backends/azurerm/)
and [provider documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs).
Role assignments can take time to propagate.

The network example creates one VNet/subnet and explicitly denies Internet
ingress with a network security group. It does not provision a workload or
outbound gateway. The storage example disables shared access keys and anonymous
access and uses versioning and soft deletion. Its firewall defaults to Deny.
Set `allowed_ip_ranges` or `allowed_subnet_ids` for clients; trusted Azure services
can bypass the firewall but still need authorization. Add private endpoints and DNS
for workloads that require private connectivity. Account names are derived from
the deployment name and a subscription hash to reduce global-name collisions.

## GCP

1. Enable the APIs needed by the examples and create a private, versioned GCS
   state bucket. Enforce uniform bucket-level access and public-access prevention.
2. Grant the operator appropriate state object permissions and the permissions
   for the resources in the selected root. Use service-account impersonation
   or workload identity federation for automation.
3. Set `project_id` and `region` in `terraform.tfvars.json`, and the state bucket
   in `backend.tf`. A separate state project is supported.

```sh
gcloud auth application-default login
tofu -chdir=live/dev/gcp/network/core init -lockfile=readonly
tofu -chdir=live/dev/gcp/network/core plan -out=plan.tfplan
```

See [GCS backend authentication](https://opentofu.org/docs/language/settings/backends/gcs/)
for impersonation and federated credentials. Do not commit downloaded service-account keys.

The network has no automatic subnets, enables private access to Google APIs,
records subnet flow logs, and denies unmatched ingress. Define narrower allow
rules for workloads before using it. The storage bucket uses uniform IAM access,
public-access prevention, cloud-managed encryption, and versioning. Add object
retention, customer-managed encryption, and lifecycle policies as needed.

## Check your identity before planning

After you log in and replace the placeholders, run the read-only preflight for the
root you are about to plan:

```sh
just preflight dev/aws/network/core
```

The preflight compares the active CLI identity with the root's `terraform.tfvars.json`:

| Cloud | Root value | Active value |
| --- | --- | --- |
| AWS | `aws_account_id` and `region` | `Account` from `aws sts get-caller-identity`, and `AWS_REGION`, `AWS_DEFAULT_REGION`, or `aws configure get region` |
| Azure | `subscription_id` | `id` from `az account show` |
| GCP | `project_id` | `gcloud config get-value project`, with an active account in `gcloud auth list` |

It fails on any placeholder in `terraform.tfvars.json` or `backend.tf`. It does not
compare your identity with the backend's `allowed_account_ids` or `subscription_id`,
because state can live in a different account or subscription than the workload.
The preflight prints account, subscription, and project IDs only. It never prints
credentials or tokens. See [operations](operations.md#check-your-identity-before-planning)
for when to run it.

## Costs and production rollout

The examples create no VMs, managed databases, NAT gateways, or load balancers.
Object data, versions, requests, KMS keys/operations, replication, and logs can still incur charges.
Review a provider-specific cost estimate before applying and set budgets/alerts
in each account, subscription, or project.

The `prod` examples demonstrate data separation, not production certification.
Before rollout, review identity boundaries, availability, private connectivity,
observability, retention, backup recovery, and deletion permissions against your
actual requirements. No cloud deployment is performed by repository setup or CI.

Native local commands do not automatically scan or approve plans. Use the explicit
[quality checks](quality.md) and your approved deployment process before applying.
