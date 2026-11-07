variable "name" {
  description = "VPC name; the subnet and default security group names extend it."
  type        = string
}

variable "network_cidr" {
  description = "VPC IPv4 CIDR."
  type        = string
}

variable "subnet_cidr" {
  description = "Private subnet IPv4 CIDR within the VPC range."
  type        = string
}
