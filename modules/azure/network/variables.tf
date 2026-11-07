variable "name" {
  description = "Virtual network name; the security group appends -nsg."
  type        = string
}
variable "resource_group_name" {
  description = "Resource group that holds the network resources."
  type        = string
}
variable "location" {
  description = "Azure location."
  type        = string
}
variable "network_cidr" {
  description = "Virtual network IPv4 CIDR."
  type        = string
}
variable "subnet_cidr" {
  description = "Private subnet IPv4 CIDR within the network range."
  type        = string
}
variable "tags" {
  description = "Tags applied to the virtual network and security group."
  type        = map(string)
  nullable    = false
}
