# Bootstrap remote state storage

Bootstrap roots create state storage independently of workloads. They live under
`live/<environment>/<cloud>/bootstrap/state` and call the stacks under
`stacks/<cloud>/bootstrap/state`. Use ordinary native OpenTofu commands in these
roots. Initialization connects to a backend and never provisions storage by itself.

| Cloud | Created resources and protections |
| --- | --- |
| AWS | S3 bucket, versioning, public-access blocking, ownership enforcement, TLS policy, rotating customer-managed KMS key, S3 lock-file settings |
| Azure | Resource group, ZRS storage account, private Blob container, Entra authentication, network default deny, versioning, 30-day blob and container soft deletion |
| GCP | GCS bucket, uniform IAM access, public-access prevention, versioning, 30-day soft deletion |

AWS bucket and key, Azure resource group, account, and container, and the GCP
bucket use `prevent_destroy`. These protections depend on the configuration
remaining present. Cloud permissions and recovery controls must enforce retention.
Bootstrap roots are excluded from Atlantis. Retire state storage only through a
separately reviewed change after all consumers have moved to another backend.

## Create state storage

1. Install the pinned OpenTofu version and authenticate to the target cloud.
2. Edit `live/dev/<cloud>/bootstrap/state/terraform.tfvars.json`. Set the real
   namespace, account, subscription, or project, and the region or location.
3. Preserve the local backend path in `backend.tf`. Bootstrap starts without remote storage.
4. For Azure, configure `allowed_ip_ranges` or `allowed_subnet_ids` for operators
   and runners. Subnets need the `Microsoft.Storage` service endpoint.
5. Run the relevant quality checks, initialize the root, and review a saved plan.

For AWS, run from the repository root:

```sh
tofu -chdir=live/dev/aws/bootstrap/state init -lockfile=readonly
tofu -chdir=live/dev/aws/bootstrap/state test
tofu -chdir=live/dev/aws/bootstrap/state plan -out=bootstrap.tfplan
tofu -chdir=live/dev/aws/bootstrap/state show bootstrap.tfplan
```

Run source and saved-plan security checks and obtain approval before applying:

```sh
tofu -chdir=live/dev/aws/bootstrap/state apply bootstrap.tfplan
tofu -chdir=live/dev/aws/bootstrap/state output -json backend_config
```

Substitute `azure` or `gcp` for another cloud. Applying a saved plan has no
confirmation prompt. Native commands do not enforce automatic security scans.

Review the non-secret `backend_config` output and transfer its attributes into
the consuming root's `backend.tf`. Keep that workload's explicit key or prefix.
The output does not overwrite configuration, grant permissions, or migrate state.

## Configure access

The AWS bootstrap operator needs bucket and KMS creation permissions. Backend
identities need S3 object, list, and lock-file permissions, plus `kms:Encrypt`,
`kms:Decrypt`, and `kms:GenerateDataKey` on the exported key. Its key policy also
applies. Customer-managed KMS keys and requests incur charges.

For Azure, register `Microsoft.Storage` beforehand. The operator needs control-plane
creation permissions. Backend users need **Storage Blob Data Contributor**, network
access, and any endpoint-discovery permissions. Empty network allowlists deny ordinary
Blob clients. Trusted Azure services bypass the firewall but still need authorization.
Confirm ZRS support for the chosen location. Private endpoints and DNS are separate additions.

For GCP, enable the Storage API and grant bucket-creation permissions to the
bootstrap operator. Grant backend identities object access separately. Versioned
and soft-deleted objects consume storage. The examples do not create IAM bindings.

Avoid retention policies that prevent lock-file deletion. Choose separate state
storage and identities for separate trust boundaries. A dev bucket should not
become the prod backend without an explicit isolation decision.

## Back up and recover bootstrap state

Bootstrap state lives at
`.infra/state/<environment>/<cloud>/bootstrap/state/terraform.tfstate` relative
to the repository. It is ignored by Git and may contain sensitive values.
Back it up to encrypted, access-controlled storage after every apply. The backup
must remain available independently of the storage being bootstrapped.
Copying the repository does not copy its ignored state.

For another machine, restore the reviewed state securely to the same relative
path before initialization and planning. Missing state can make existing resources
appear absent. Do not apply that plan as a recovery step. Recover a backup or
import verified resource identities through an authorized procedure.

The native-root refactor preserves this state path. Follow the
[migration guide](migration.md) before upgrading an existing bootstrap deployment.
Moving bootstrap state to different storage is a separate operation described in
[operations](operations.md). See [cloud setup](cloud-setup.md) for authentication.
