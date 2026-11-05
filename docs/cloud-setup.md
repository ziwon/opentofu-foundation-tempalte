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
key, prefix, or local path. Preserve those values for an existing deployment.
Replace storage placeholders before initialization. Native `tofu init` connects
to that backend through its normal authentication mechanism.

## AWS

1. Create a private S3 state bucket in the intended account/region. Enable
   versioning, default encryption, public-access blocking, and a TLS-only policy.
2. Grant the operator access to that bucket and deployment prefix. S3 locking
   additionally needs `GetObject`, `PutObject`, and `DeleteObject` on `.tflock`
   objects. Consult the [backend permission examples](https://opentofu.org/docs/language/settings/backends/s3/).
3. Configure AWS CLI SSO or a role-based credential chain. For CI, prefer OIDC
   with a repository/environment-scoped trust policy.
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
deletion, but that is not a backup or retention policy.

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
For an existing shared-root deployment, follow [migration](migration.md) first.
