# AWS storage

Private object storage with versioning and a rotating customer-managed KMS key.
Key storage and encryption operations incur additional charges. Principals reading
or writing objects need appropriate KMS permissions as well as S3 permissions.
The key has `prevent_destroy`; retiring storage requires a reviewed key-retention
decision so a failed bucket deletion cannot leave retained objects without a key.

Code is shared by dev, stage, and prod. Edit the matching
`live/<environment>/aws/storage/bucket/terraform.tfvars.json` and `backend.json`.
Run commands from the repository root:

```sh
python3 tools/infra.py show dev/aws/storage/bucket
python3 tools/infra.py test dev/aws/storage/bucket
python3 tools/infra.py init dev/aws/storage/bucket
python3 tools/infra.py plan dev/aws/storage/bucket
```

Tests use mocked providers and do not access a cloud account. Real plans require
configured state storage and cloud credentials. Review the saved plan before applying.
See [cloud setup](../../../../docs/cloud-setup.md) for permissions, costs, and production additions.
