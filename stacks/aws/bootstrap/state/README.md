# AWS state bootstrap

Create remote state storage with a separately managed local state. These resources
have deletion protection through `prevent_destroy`; this is not an IAM boundary.
Edit `live/<environment>/aws/bootstrap/state/terraform.tfvars.json` first.

```sh
python3 tools/infra.py test dev/aws/bootstrap/state
python3 tools/infra.py bootstrap init dev/aws/bootstrap/state
python3 tools/infra.py bootstrap plan dev/aws/bootstrap/state
python3 tools/infra.py bootstrap apply dev/aws/bootstrap/state
python3 tools/infra.py bootstrap output dev/aws/bootstrap/state
```

The last command prints the non-secret JSON for regular deployments' `backend.json`.
Back up the bootstrap state securely after each apply. Read [bootstrap operations](../../../../docs/bootstrap.md)
for authentication, permissions, network access, recovery, and cost considerations.
Tests use mocked providers and never provision cloud resources.
