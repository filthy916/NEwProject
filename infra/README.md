# ComfyUI GPU Infrastructure (Terraform)

Automated deployment of a GPU-accelerated ComfyUI instance on Azure using Terraform.

## 📋 Quick Start

### Prerequisites

1. **Azure CLI** — [Install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Terraform** — [Install](https://www.terraform.io/downloads)
3. **SSH Key** — Generate if you don't have one:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

### Deployment Steps

#### 1. Login to Azure
```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

#### 2. Initialize Terraform
```bash
cd infra/
terraform init
```

#### 3. Review Plan
```bash
terraform plan
```

#### 4. Deploy
```bash
terraform apply
```

When prompted, enter `yes` to confirm deployment.

**Takes ~15-20 minutes** ☕

#### 5. Get Connection Details
After deployment completes, Terraform will output:
- `public_ip_address` — Your VM's public IP
- `ssh_command` — Ready-to-use SSH command
- `comfyui_url` — ComfyUI web UI URL

```bash
# Example:
# SSH: ssh -i ~/.ssh/id_rsa azureuser@20.50.100.123
# ComfyUI: http://20.50.100.123:8188
```

---

## 🎮 Using ComfyUI

### Access the Web UI
Open your browser:
```
http://<PUBLIC_IP>:8188
```

### SSH into VM (for debugging/model management)
```bash
ssh -i ~/.ssh/id_rsa azureuser@<PUBLIC_IP>
```

### Check ComfyUI Status
```bash
ssh azureuser@<PUBLIC_IP> "systemctl status comfyui"
ssh azureuser@<PUBLIC_IP> "journalctl -u comfyui -f"
```

---

## 💰 Cost Management

### Stop VM (pauses costs while keeping state)
```bash
az vm deallocate --resource-group comfyui-rg --name comfyui-gpu
```

### Start VM
```bash
az vm start --resource-group comfyui-rg --name comfyui-gpu
```

### Auto-Shutdown
VM automatically shuts down at **6 PM Pacific Time** daily (configurable in `terraform.tfvars`)

**Solo usage estimates:**
- 100 hrs/month: ~$60-70
- 50 hrs/month: ~$35-40
- 200 hrs/month: ~$120-130

---

## 📁 Configuration

Edit `terraform.tfvars` to customize:

| Variable | Default | Notes |
|----------|---------|-------|
| `location` | `westus2` | Azure region |
| `vm_size` | `Standard_NC6s_v3` | GPU VM size (1x V100) |
| `data_disk_size_gb` | `200` | Storage for models |
| `admin_username` | `azureuser` | SSH username |
| `auto_shutdown_time` | `1800` | Daily shutdown time |
| `timezone` | `America/Los_Angeles` | Shutdown timezone |

### Upgrade VM Size
To use more GPUs, edit `terraform.tfvars`:

```hcl
vm_size = "Standard_NC12s_v3"  # 2x V100 (more expensive)
vm_size = "Standard_NC24s_v3"  # 4x V100 (much more expensive)
```

Then:
```bash
terraform plan
terraform apply  # VM will be recreated
```

---

## 🛑 Cleanup

### Delete All Resources
```bash
terraform destroy
```

This will:
- ✅ Delete VM, disks, network, and resource group
- ✅ Stop all Azure charges
- ❌ Cannot be undone!

---

## 🐛 Troubleshooting

### GPU not detected
```bash
ssh azureuser@<IP>
nvidia-smi  # Should show Tesla V100
```

### ComfyUI not running
```bash
ssh azureuser@<IP>
sudo systemctl restart comfyui
sudo journalctl -u comfyui -n 50  # Last 50 log lines
```

### Can't SSH
- Check NSG allows port 22: `az network nsg rule list -g comfyui-rg --nsg-name comfyui-gpu-nsg`
- Verify your SSH key is correct: `ssh -i ~/.ssh/id_rsa -vvv azureuser@<IP>`

### Slow model downloads
- Increase data disk size in `terraform.tfvars` and reapply
- Use `az network public-ip show` to verify public IP

---

## 📚 Files

| File | Purpose |
|------|---------|
| `main.tf` | Core infrastructure (VM, network, storage) |
| `variables.tf` | Input variables |
| `outputs.tf` | Output values (IP, commands, etc.) |
| `terraform.tfvars` | Default configuration values |
| `user-data.sh` | VM initialization script |

---

## 🔐 Security Notes

- ✅ Uses Spot instances (can be interrupted, saves 70%)
- ✅ SSH key-based authentication (no password)
- ✅ NSG restricts inbound to SSH (22) + ComfyUI (8188)
- ✅ Private IP for internal VMX communication
- ⚠️ Consider your security posture before exposing port 8188 to `0.0.0.0/0`

---

## 📞 Support

For issues, check:
1. Terraform logs: `terraform apply -var-file=terraform.tfvars -lock=false`
2. Azure Portal: [Resource Group Status](https://portal.azure.com)
3. VM serial console: `az vm boot-diagnostics get-boot-log -g comfyui-rg -n comfyui-gpu`

---

**Happy ComfyUI-ing! 🎨**
