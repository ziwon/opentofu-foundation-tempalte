# GCP storage

Private object storage with versioning. Encryption uses the cloud-managed default keys.

Code is shared by dev, stage, and prod. Edit the matching
`live/<environment>/gcp/storage/bucket/terraform.tfvars.json` and `backend.json`.
Run commands from the repository root:

```sh
python3 tools/infra.py show dev/gcp/storage/bucket
python3 tools/infra.py test dev/gcp/storage/bucket
python3 tools/infra.py init dev/gcp/storage/bucket
python3 tools/infra.py plan dev/gcp/storage/bucket
```

Tests use mocked providers and do not access a cloud account. Real plans require
configured state storage and cloud credentials. Review the saved plan before applying.
See [cloud setup](../../../../docs/cloud-setup.md) for permissions, costs, and production additions.
