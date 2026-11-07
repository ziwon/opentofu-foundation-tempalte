output "virtual_network_id" {
  description = "Virtual network resource ID."
  value       = azurerm_virtual_network.this.id
}
output "network_cidr" {
  description = "Virtual network IPv4 CIDR."
  value       = one(azurerm_virtual_network.this.address_space)
}
output "subnet_cidr" {
  description = "Private subnet IPv4 CIDR."
  value       = one(azurerm_subnet.private.address_prefixes)
}
