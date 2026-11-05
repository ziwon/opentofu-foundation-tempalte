resource "aws_vpc" "this" {
  cidr_block           = var.network_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = module.context.id }
}
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = false
  tags                    = { Name = "${module.context.id}-private" }
}
resource "aws_default_security_group" "this" {
  vpc_id  = aws_vpc.this.id
  ingress = []
  egress  = []
  tags    = { Name = "${module.context.id}-default-deny" }
}
