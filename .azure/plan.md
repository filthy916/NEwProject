# Azure Deployment Plan: ComfyUI GPU Setup

**Status:** Ready for Approval ✅
**Region:** West US 2
**Usage Mode:** Solo-User On-Demand (deallocate when not using)
**Deployment Method:** Terraform

---

## 1. Requirements Summary

| Aspect | Decision |
|--------|----------|
| **Workload** | ComfyUI (Stable Diffusion node editor) for professional use |
| **Compute** | GPU VM with NVIDIA Tesla V100 |
| **VM Type** | Spot Instance (70% cost savings) |
| **VM Size** | Standard_NC6s_v3 (1x V100 GPU, 6 vCPU, 56GB RAM) |
| **Region** | West US 2 (better GPU pricing + availability) |
| **OS** | Ubuntu 22.04 LTS |
| **Storage** | 200GB Premium SSD |
| **Budget** | ~$100-120/month solo-user (deallocate when not using) |
| **Billing Model** | Spot instances + auto-shutdown (interruptible but cheapest) |

---

## 2. Architecture

```
Azure Resource Group
├── Virtual Machine (Spot: NC6s_v3)
│   ├── OS: Ubuntu 22.04 LTS
│   ├── GPU: NVIDIA Tesla V100 (16GB VRAM)
│   ├── CPU: 6 vCores
│   ├── RAM: 56 GB
│   └── ComfyUI installed + systemd service
├── Network Interface & NSG
│   ├── Inbound: SSH (22), ComfyUI HTTP (8188)
│   └── Outbound: All (for model downloads)
├── Storage (Premium SSD)
│   ├── OS Disk: 50GB
│   └── Data Disk: 200GB (models/outputs)
└── Auto-shutdown rule (cost savings)
```

---

## 3. Deployment Components

### Infrastructure (Terraform)
- `main.tf` — Resource group, VM, network, storage
- `variables.tf` — Configurable parameters (region, VM size, admin user)
- `outputs.tf` — Public IP, RDP/SSH connection strings
- `terraform.tfvars` — Environment-specific values

### VM Setup Scripts
- `user-data.sh` — Cloud-init script that:
  1. Installs NVIDIA drivers + CUDA toolkit
  2. Installs Docker (for ComfyUI container, optional)
  3. Downloads & installs ComfyUI
  4. Starts ComfyUI as systemd service
  5. Opens port 8188 in firewall

### `.azure/plan.md` 
- This deployment plan (tracks progress)

---

## 4. Cost Breakdown (Monthly) — Solo User with On-Demand Usage

| Resource | Estimated Cost | Notes |
|----------|-----------------|-------|
| Spot NC6s_v3 VM (200 hrs/mo on-demand) | ~$25 | Only running when you use it |
| Spot NC6s_v3 VM (deallocated, stored state) | ~$10/mo | Storage for VM state when off |
| Premium SSD Storage (200GB) | ~$20 | Persistent for models |
| Public IP (1) | ~$3 | Charged only when running |
| Data transfer (outbound, model downloads) | ~$5-10 | One-time for model DL |
| **Total Estimated** | **~$63-68/month** | ✅ **Way cheaper!** |

**💡 Smart Savings Strategy:**
- Use auto-shutdown: 6pm-8am (no charge when off)
- Deallocate after work: `az vm deallocate --name comfyui-vm`
- Only pay when actually using ComfyUI
- **Potential: $50-100/month** if you use ~100hrs/month

✅ **Well within your $300/month budget — $200+ left over!**

---

## 5. Key Features

✅ **Ready for ComfyUI** — Pre-configured with NVIDIA drivers  
✅ **Cost Optimized** — Spot instances save 70%  
✅ **Auto-Shutdown** — Stops VM at off-peak hours to save more  
✅ **Easy Access** — SSH + HTTP (port 8188) exposed  
✅ **Scalable** — Can upgrade to NC12s_v3 later if needed  
✅ **Git-Ready** — Terraform code committed to your repo  

---

## 6. Deployment Steps

1. **Phase 1 (Planning)** — ✅ You are here
   - [ ] Review this plan
   - [ ] Approve or request changes
   
2. **Phase 2 (Execution)** — Ready to execute after approval
   - [ ] Generate Terraform files
   - [ ] Confirm Azure subscription & region
   - [ ] Create `.azure/` directory structure
   - [ ] Finalize security settings
   
3. **Phase 3 (Validation)** — Run pre-deployment checks
   - [ ] Validate Terraform syntax
   - [ ] Check Azure quotas/limits
   - [ ] Verify SSH keys & security
   
4. **Phase 4 (Deployment)** — Deploy to Azure
   - [ ] terraform init
   - [ ] terraform plan
   - [ ] terraform apply
   - [ ] Verify ComfyUI running at `http://<public-ip>:8188`

---

## 7. Access & Management

After deployment:

**SSH Access:**
```bash
ssh -i ~/.ssh/id_rsa azureuser@<public-ip>
```

**ComfyUI Web UI:**
```
http://<public-ip>:8188
```

**Stop VM (save costs):**
```bash
az vm deallocate -g comfyui-rg -n comfyui-vm
```

**Start VM:**
```bash
az vm start -g comfyui-rg -n comfyui-vm
```

---

## 8. Next Steps

### ✅ If you approve this plan:
→ I'll generate complete Terraform files + setup scripts  
→ Validate everything is Azure-quota compliant  
→ Deploy fully automated  

### ⚠️ If you'd like changes:
- Different region? (US West 2, Europe, etc.)
- Different VM size? (NC12s_v3 for more power?)
- On-demand instead of Spot? (more expensive but no interruptions)
- Docker-based ComfyUI? (add Docker setup)

---

**Ready to proceed? Approve this plan or request modifications!**
