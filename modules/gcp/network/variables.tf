variable "name" {
  description = "Network name; the subnet and firewall names derive from it."
  type        = string
}

variable "region" {
  description = "GCP region for the private subnet."
  type        = string
}

variable "subnet_cidr" {
  description = "Private subnet IPv4 CIDR."
  type        = string
}
