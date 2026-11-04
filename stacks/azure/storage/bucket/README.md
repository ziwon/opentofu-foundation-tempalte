# AZURE storage

Private object storage with versioning. Encryption uses the cloud-managed default keys.
Network rules default to Deny. Configure `allowed_ip_ranges` or `allowed_subnet_ids`
for Blob clients; empty lists deny ordinary clients. Trusted Azure services may
bypass network rules but still require authorization.
The storage account and container have `prevent_destroy`. Retirement requires a
reviewed retention/recovery decision before removing that protection.

Code is shared by dev, stage, and prod. Edit the matching
`live/<environment>/azure/storage/bucket/terraform.tfvars.json` and `backend.json`.
Run commands from the repository root:

```sh
python3 tools/infra.py show dev/azure/storage/bucket
python3 tools/infra.py test dev/azure/storage/bucket
python3 tools/infra.py init dev/azure/storage/bucket
python3 tools/infra.py plan dev/azure/storage/bucket
```

Tests use mocked providers and do not access a cloud account. Real plans require
configured state storage and cloud credentials. Review the saved plan before applying.
See [cloud setup](../../../../docs/cloud-setup.md) for permissions, costs, and production additions.
