moved {
  from = azurerm_resource_group.this
  to   = module.stack.azurerm_resource_group.this
}

moved {
  from = azurerm_storage_account.this
  to   = module.stack.azurerm_storage_account.this
}

moved {
  from = azurerm_storage_container.this
  to   = module.stack.azurerm_storage_container.this
}
