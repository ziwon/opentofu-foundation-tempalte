# GCP network

An isolated network and one private subnet. It creates no compute, NAT gateway, or public IP.

Code is shared by dev, stage, and prod. Edit the matching
`live/<environment>/gcp/network/core/terraform.tfvars.json` and `backend.json`.
Run commands from the repository root:

```sh
python3 tools/infra.py show dev/gcp/network/core
python3 tools/infra.py test dev/gcp/network/core
python3 tools/infra.py init dev/gcp/network/core
python3 tools/infra.py plan dev/gcp/network/core
```

Tests use mocked providers and do not access a cloud account. Real plans require
configured state storage and cloud credentials. Review the saved plan before applying.
See [cloud setup](../../../../docs/cloud-setup.md) for permissions, costs, and production additions.
