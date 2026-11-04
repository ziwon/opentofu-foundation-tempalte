# Azure state bootstrap

Create remote state storage with a separately managed local state. These resources
have deletion protection through `prevent_destroy`; this is not an IAM boundary.
Edit `live/<environment>/azure/bootstrap/state/terraform.tfvars.json` first.

```sh
python3 tools/infra.py test dev/azure/bootstrap/state
python3 tools/infra.py bootstrap init dev/azure/bootstrap/state
python3 tools/infra.py bootstrap plan dev/azure/bootstrap/state
python3 tools/infra.py bootstrap apply dev/azure/bootstrap/state
python3 tools/infra.py bootstrap output dev/azure/bootstrap/state
```

The last command prints the non-secret JSON for regular deployments' `backend.json`.
Back up the bootstrap state securely after each apply. Read [bootstrap operations](../../../../docs/bootstrap.md)
for authentication, permissions, network access, recovery, and cost considerations.
Tests use mocked providers and never provision cloud resources.
