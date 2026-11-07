variables {
  name         = "starter-fixture-dev"
  network_cidr = "10.10.0.0/16"
  subnet_cidr  = "10.10.1.0/24"
}

mock_provider "aws" {}
run "private_network" {
  command = plan
  assert {
    condition     = aws_vpc.this.cidr_block == "10.10.0.0/16" && aws_vpc.this.enable_dns_support && aws_vpc.this.enable_dns_hostnames && aws_vpc.this.tags == tomap({ Name = "starter-fixture-dev" })
    error_message = "The VPC must use the supplied range and name with DNS support and hostnames."
  }
  assert {
    condition     = aws_subnet.private.vpc_id == aws_vpc.this.id && aws_subnet.private.cidr_block == "10.10.1.0/24" && aws_subnet.private.tags == tomap({ Name = "starter-fixture-dev-private" })
    error_message = "The private subnet must use the supplied range inside the VPC."
  }
  assert {
    condition     = aws_subnet.private.map_public_ip_on_launch == false
    error_message = "Subnets must not assign public IP addresses."
  }
  assert {
    condition     = aws_default_security_group.this.vpc_id == aws_vpc.this.id && length(aws_default_security_group.this.ingress) == 0 && length(aws_default_security_group.this.egress) == 0 && aws_default_security_group.this.tags == tomap({ Name = "starter-fixture-dev-default-deny" })
    error_message = "The default security group must deny ingress and egress."
  }
  assert {
    condition     = output.id == aws_vpc.this.id
    error_message = "The module must expose the VPC ID."
  }
}
