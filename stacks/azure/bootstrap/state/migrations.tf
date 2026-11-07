moved {
  from = azurerm_storage_account.this
  to   = module.storage_account.azurerm_storage_account.this
}

moved {
  from = azurerm_storage_container.this
  to   = module.storage_account.azurerm_storage_container.this
}
