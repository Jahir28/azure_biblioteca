output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "container_group_fqdn" {
  value = azurerm_container_group.main.fqdn
}

output "frontend_url" {
  value = "http://${azurerm_container_group.main.fqdn}"
}

output "backend_url" {
  value = "http://${azurerm_container_group.main.fqdn}:8000"
}
