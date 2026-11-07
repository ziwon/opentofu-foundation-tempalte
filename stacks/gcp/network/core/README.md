# gcp/network/core

Stack that each `live/<environment>/gcp/network/core` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The network, private subnet, and deny-ingress firewall live in the core module
[`modules/gcp/network`](../../../../modules/gcp/network), called as `module "network"`.
`migrations.tf` moves them from this stack into it.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
