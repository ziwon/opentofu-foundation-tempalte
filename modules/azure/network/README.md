# azure/network

Core module that owns an Azure virtual network, one subnet named `private`, and a
network security group associated with that subnet. The security group's
`DenyInternetInbound` rule denies inbound traffic from the `Internet` service tag.
`stacks/azure/network/core` calls it as `module "network"` and keeps the resource
group itself.

The virtual network takes `name`, and the security group takes `<name>-nsg`. Pass
the resource group name, location, address ranges, and tags explicitly.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
