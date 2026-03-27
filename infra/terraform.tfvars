# ComfyUI GPU VM Configuration

resource_group_name = "comfyui-rg"
location            = "westus2"
environment         = "dev"
vm_name             = "comfyui-gpu"
vm_size             = "Standard_NC6s_v3"
admin_username      = "azureuser"
data_disk_size_gb   = 200

# Auto-shutdown at 6 PM Pacific Time to save costs
enable_auto_shutdown = true
auto_shutdown_time  = "1800"
timezone            = "America/Los_Angeles"

# SSH public key path (adjust if needed)
ssh_public_key_path = "~/.ssh/id_rsa.pub"
