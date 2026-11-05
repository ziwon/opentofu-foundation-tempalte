moved {
  from = azurerm_resource_group.this
  to   = module.stack.azurerm_resource_group.this
}

moved {
  from = azurerm_virtual_network.this
  to   = module.stack.azurerm_virtual_network.this
}

moved {
  from = azurerm_subnet.private
  to   = module.stack.azurerm_subnet.private
}

moved {
  from = azurerm_network_security_group.this
  to   = module.stack.azurerm_network_security_group.this
}

moved {
  from = azurerm_subnet_network_security_group_association.this
  to   = module.stack.azurerm_subnet_network_security_group_association.this
}
