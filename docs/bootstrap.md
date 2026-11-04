# Bootstrap remote state storage

Bootstrap stacks create state storage separately from workloads. They live in
`stacks/<cloud>/bootstrap/state`, with dev/stage/prod data in `live/`. They use the
same validation, saved-plan checks, and security gates as other stacks, but require
an explicit `bootstrap` command for init/plan/apply. Ordinary `init` only initializes
a backend; it never provisions storage.

| Cloud | Created resources and protections |
| --- | --- |
| AWS | S3 bucket, versioning, public-access blocking, ownership enforcement, TLS policy, rotating customer-managed KMS key, native S3 lock-file settings |
| Azure | Resource group, ZRS storage account, private Blob container, Entra authentication, network default deny, versioning, 30-day blob/container soft deletion |
| GCP | GCS bucket, uniform IAM access, public-access prevention, versioning, 30-day soft deletion |

AWS bucket/key, Azure resource group/account/container, and the GCP bucket have
`prevent_destroy`. This protects resources while that configuration remains in
place; cloud permissions and recovery controls must enforce your retention policy.
Bootstrap has no destroy command. Retirement requires a separately reviewed change
after every consuming deployment has moved to another backend.

## First deployment

1. Install the pinned tools with `mise install` and authenticate to the target cloud.
2. Edit `live/dev/<cloud>/bootstrap/state/terraform.tfvars.json`. Replace the example
   namespace and account/subscription/project; select an appropriate region/location.
   Keep bootstrap `backend.json` as `{}` so it can start without remote storage.
3. For Azure, set `allowed_ip_ranges` to operators' and runners' public IPv4 addresses
   or supported CIDRs, or set `allowed_subnet_ids` for subnets with the
   `Microsoft.Storage` service endpoint. Empty lists deny ordinary Blob clients.
4. Run checks, initialize, and review a plan. Substitute `azure` or `gcp` below:

```sh
python3 tools/infra.py lint dev/aws/bootstrap/state
python3 tools/infra.py security dev/aws/bootstrap/state
python3 tools/infra.py test dev/aws/bootstrap/state
python3 tools/infra.py bootstrap init dev/aws/bootstrap/state
python3 tools/infra.py bootstrap plan dev/aws/bootstrap/state
python3 tools/infra.py bootstrap apply dev/aws/bootstrap/state
python3 tools/infra.py bootstrap output dev/aws/bootstrap/state
```

Apply asks for the full deployment name. The output command prints a JSON object
containing non-secret backend settings. Review and copy it into each consuming
deployment's `backend.json`, for example `live/dev/aws/network/core/backend.json`.
Keys/prefixes remain derived by the runner. Bootstrap does not overwrite live files,
grant workload identities permissions, migrate state, or create resources during init.

## Access and cost considerations

- AWS: the bootstrap operator needs bucket and KMS creation/configuration permissions.
  Backend identities need S3 object/list permissions, lock-file permissions, and
  `kms:Encrypt`, `kms:Decrypt`, and `kms:GenerateDataKey` on the exported key, subject
  to its key policy. Customer-managed KMS keys and requests incur additional charges.
- Azure: register `Microsoft.Storage` beforehand. The operator needs control-plane
  creation permissions; backend users need **Storage Blob Data Contributor** at
  the intended scope, network access, and any endpoint-discovery read permissions.
  The firewall allows trusted Azure services as well as explicit IP/subnet rules;
  identity authorization still applies. ZRS must be supported in your location.
  A private endpoint and DNS are separate additions if required by your network.
- GCP: enable the Storage API and grant bucket-creation permissions to the bootstrap
  operator, then object access to backend identities. Versioned and soft-deleted
  objects consume storage. IAM bindings are deliberately managed separately.

Avoid immutable retention policies that prevent lock-file deletion. Versioning and
soft deletion preserve recovery options without locking every object against deletion.
Choose a separate bootstrap deployment per trust boundary; a dev bucket should not
automatically become the backend for prod.

## Back up and recover bootstrap state

Bootstrap state lives at
`.infra/state/<environment>/<cloud>/bootstrap/state/terraform.tfstate`. It is shared
by the two supported engines, ignored by Git, and may contain sensitive values.
Choose one engine for actual use and back up this state to an access-controlled,
encrypted location after every apply. That backup must not depend on access to
the storage being bootstrapped. Copying the repository does not copy its state.

For another operator or machine, restore the reviewed state securely to the same
deployment path before initializing and planning. A missing bootstrap state can
make existing resources appear absent; never apply that plan as a recovery step.
If state is lost, recover a backup or import verified resource identities using
the engine's documented procedure. Migration to independently provisioned remote
storage is a separate operation described in [operations](operations.md).

See [cloud setup](cloud-setup.md) for native authentication and permissions.
