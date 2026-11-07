output "id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}
output "network_cidr" {
  description = "VPC IPv4 CIDR."
  value       = aws_vpc.this.cidr_block
}
output "subnet_cidr" {
  description = "Private subnet IPv4 CIDR."
  value       = aws_subnet.private.cidr_block
}
