output "resource_group_name" {
  value       = azurerm_resource_group.main.name
  description = "The name of the resource group"
}

output "resource_group_id" {
  value       = azurerm_resource_group.main.id
  description = "The ID of the resource group"
}

output "public_ip_address" {
  value       = azurerm_public_ip.main.ip_address
  description = "The public IP address of the VM"
}

output "vm_name" {
  value       = azurerm_linux_virtual_machine.main.name
  description = "The name of the virtual machine"
}

output "vm_id" {
  value       = azurerm_linux_virtual_machine.main.id
  description = "The ID of the virtual machine"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/id_rsa ${var.admin_username}@${azurerm_public_ip.main.ip_address}"
  description = "SSH command to connect to the VM"
}

output "comfyui_url" {
  value       = "http://${azurerm_public_ip.main.ip_address}:8188"
  description = "ComfyUI web UI URL"
}

output "vm_size" {
  value       = azurerm_linux_virtual_machine.main.size
  description = "The size of the virtual machine"
}

output "stop_command" {
  value       = "az vm deallocate --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_linux_virtual_machine.main.name}"
  description = "Command to stop/deallocate the VM (saves costs when not in use)"
}

output "start_command" {
  value       = "az vm start --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_linux_virtual_machine.main.name}"
  description = "Command to start the VM"
}
