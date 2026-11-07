# azure/network/core

Stack that each `live/<environment>/azure/network/core` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The stack owns the resource group. The virtual network, the `private` subnet, the network
security group, and its subnet association live in the core module
[`modules/azure/network`](../../../../modules/azure/network), called as `module "network"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
