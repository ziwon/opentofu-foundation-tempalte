# aws/network/core

Stack that each `live/<environment>/aws/network/core` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The VPC, private subnet, and default security group live in the core module
[`modules/aws/vpc`](../../../../modules/aws/vpc), called as `module "vpc"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
