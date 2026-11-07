# aws/vpc

Core module that owns a VPC with DNS support, one private subnet that assigns no
public IP addresses, and a default security group that denies all ingress and egress.
Pass `name`, `network_cidr`, and `subnet_cidr`. The resources carry `Name` tags
derived from `name`. Common tags come from the calling root's provider `default_tags`.

`stacks/aws/network/core` calls it as `module "vpc"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
