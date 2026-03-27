variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
  default     = "comfyui-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westus2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "comfyui-gpu"
}

variable "vm_size" {
  description = "Size of the virtual machine"
  type        = string
  default     = "Standard_NC6s_v3"
  # Other options:
  # "Standard_NC12s_v3" - 2x V100 (more expensive)
  # "Standard_NC24s_v3" - 4x V100 (much more expensive)
}

variable "admin_username" {
  description = "Administrator username"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "data_disk_size_gb" {
  description = "Size of the data disk for ComfyUI models (GB)"
  type        = number
  default     = 200
}

variable "enable_auto_shutdown" {
  description = "Enable automatic shutdown to save costs"
  type        = bool
  default     = true
}

variable "auto_shutdown_time" {
  description = "Time to auto-shutdown VM (HHmm format, 24h)"
  type        = string
  default     = "1800" # 6 PM
}

variable "timezone" {
  description = "Timezone for auto-shutdown schedule"
  type        = string
  default     = "America/Los_Angeles"
}
