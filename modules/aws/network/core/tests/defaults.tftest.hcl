variables {
  network_cidr = "10.10.0.0/16"
  subnet_cidr  = "10.10.1.0/24"
  context      = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "aws" {}
run "private_network" {
  command = plan
  assert {
    condition     = aws_subnet.private.map_public_ip_on_launch == false
    error_message = "Subnets must not assign public IP addresses."
  }
  assert {
    condition     = length(aws_default_security_group.this.ingress) == 0 && length(aws_default_security_group.this.egress) == 0
    error_message = "The default security group must deny ingress and egress."
  }
}
