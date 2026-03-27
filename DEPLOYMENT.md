# 🚀 Complete Deployment Guide: Flux 2 Media Generator + ComfyUI GPU

This project includes two major components:
1. **Flux 2 Media Generator** — Node.js + React web app for AI image generation
2. **ComfyUI GPU Infrastructure** — Terraform-managed Azure GPU VM

---

## 📦 What's Included

```
flux-2-media-generator/
├── client/                    # React frontend
├── server/                    # Express backend
├── infra/                     # Terraform infrastructure for GPU VM
│   ├── main.tf               # Azure resources
│   ├── variables.tf          # Configuration variables
│   ├── outputs.tf            # Output values
│   ├── terraform.tfvars      # Default values
│   ├── user-data.sh          # VM setup script
│   └── README.md             # Detailed deployment guide
├── .azure/
│   └── plan.md               # Deployment strategy & plan
├── QUICKSTART.md             # App-level quick start
├── README.md                 # This file
└── deployment-guide.md       # You are reading this!
```

---

## 🎯 Quick Decision Tree

**What do you want to do?**

- **A) Run the Flux 2 app locally** → Go to [Local Development](#local-development)
- **B) Deploy Flux 2 to Azure** → Go to [Deploy Flux 2 to Azure](#deploy-flux-2-to-azure)
- **C) Set up GPU-accelerated ComfyUI** → Go to [ComfyUI GPU Setup](#comfyui-gpu-setup)
- **D) Do everything (full stack)** → Go to [Full Stack Deployment](#full-stack-deployment)

---

## 🏃 Local Development

### Prerequisites
- Node.js 16+
- Python 3.8+ (for potential future Python services)
- Hugging Face API key

### Setup & Run

```bash
# 1. Get Hugging Face API key
# Go to https://huggingface.co/settings/tokens and create a token

# 2. Configure environment
cd server
cp .env.example .env
# Edit .env and add: HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx

# 3. Install dependencies
npm install
cd ../client && npm install && cd ..

# 4. Start development servers
npm run dev
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

👉 See [QUICKSTART.md](QUICKSTART.md) for detailed steps.

---

## ☁️ Deploy Flux 2 to Azure

The Flux 2 app can run on:
- **Azure App Service** (easy, no DevOps)
- **Azure Container Apps** (scalable, containerized)
- **Azure VM** (most control)

*Coming soon: Automated `azure-prepare` integration*

---

## 🎮 ComfyUI GPU Setup

### What is ComfyUI?
Node-based Stable Diffusion editor. Powerful for creative workflows.

### Prerequisites
- **Azure subscription** with GPU quota
- **Terraform** ([install](https://www.terraform.io/downloads))
- **Azure CLI** ([install](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **SSH key** (or generate one):
  ```bash
  ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
  ```

### Deployment (5-10 minutes)

**Step 1: Login to Azure**
```bash
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

**Step 2: Deploy with Terraform**
```bash
cd infra/
terraform init
terraform plan   # Review what will be created
terraform apply  # Type 'yes' to confirm
```

**Step 3: Access ComfyUI**
```bash
# Terraform will output:
# - SSH command
# - ComfyUI URL (http://<IP>:8188)

# Example:
ssh -i ~/.ssh/id_rsa azureuser@20.50.100.123
# Then browse to: http://20.50.100.123:8188
```

👉 See [infra/README.md](infra/README.md) for detailed setup & troubleshooting.

### Cost Optimization
- VM auto-shuts down at **6 PM Pacific** daily
- Stop anytime to pause charges:
  ```bash
  az vm deallocate -g comfyui-rg -n comfyui-gpu
  ```
- **Estimated cost**: $60-120/month (solo use, 100-200 hrs/mo)

---

## 🏗️ Full Stack Deployment

To run **both** Flux 2 AND ComfyUI:

### Option 1: Local Flux 2 + Azure GPU ComfyUI
```bash
# Terminal 1: Flux 2 locally
npm run dev

# Terminal 2: Deploy ComfyUI to Azure
cd infra/
terraform apply
```

### Option 2: Both on Azure
```bash
# Deploy Flux 2 to Azure App Service
cd app/
# (Prepare Flux 2 deployment - add this feature)

# Deploy ComfyUI to Azure GPU VM
cd infra/
terraform apply
```

---

## 🔧 Configuration

### Flux 2 Backend (.env)
```bash
PORT=5000
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx
```

### ComfyUI Terraform (infra/terraform.tfvars)
```hcl
location     = "westus2"          # Azure region
vm_size      = "Standard_NC6s_v3" # 1x V100 GPU
data_disk_size_gb = 200           # Model storage
auto_shutdown_time = "1800"       # 6 PM shutdown
```

---

## 📚 File Guides

| File/Folder | Purpose | Read If... |
|-----------|---------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Fast app setup | You want to run Flux 2 locally |
| [infra/README.md](infra/README.md) | GPU VM deployment | You want to deploy ComfyUI |
| [.azure/plan.md](.azure/plan.md) | Deployment strategy | You're curious about decisions made |
| [server/.env.example](server/.env.example) | API config template | You need to add Hugging Face key |

---

## 🔐 Security Notes

### Flux 2
- ✅ Backend validates prompts before API calls
- ✅ Hugging Face API key stored locally (never committed)
- ⚠️ NSFW detection is not foolproof — combine with manual review

### ComfyUI GPU VM
- ✅ SSH key-based auth (no passwords)
- ✅ Firewall restricts SSH (22) + ComfyUI (8188) only
- ⚠️ ComfyUI exposed to `0.0.0.0/0` — consider IP whitelisting for production

---

## 🐛 Troubleshooting

### Flux 2 Issues
```bash
# Clear node_modules & reinstall
rm -rf node_modules client/node_modules
npm install && cd client && npm install && cd ..

# Check API key
cat server/.env | grep HUGGINGFACE_API_KEY
```

### ComfyUI GPU Issues
```bash
# Can't SSH?
# Check subnet rules
az network nsg rule list -g comfyui-rg --nsg-name comfyui-gpu-nsg

# GPU not detected?
ssh azureuser@<IP>
nvidia-smi

# ComfyUI not running?
systemctl status comfyui
journalctl -u comfyui -f
```

---

## 💾 Backing Up Models

ComfyUI models stored on `/mnt/comfyui-data` Azure disk.

**To backup:**
```bash
# From your local machine:
ssh azureuser@<IP> "tar -czf models-backup.tar.gz /mnt/comfyui-data/"
scp azureuser@<IP>:models-backup.tar.gz ./
```

---

## 📊 Cost Breakdown

### Flux 2 (Local Development)
- $0 — Runs on your machine

### Flux 2 + Azure App Service
- ~$15-50/month depending on plan

### ComfyUI GPU VM (Solo Use)
- ~$60-120/month (100-200 hrs/mo)
- Auto-shutdown saves ~30-40% more

### Full Stack on Azure
- ~$75-170/month (both services running)

---

## 🎓 Next Steps

### Short Term
1. ✅ Run Flux 2 locally (`npm run dev`)
2. ✅ Deploy ComfyUI GPU (`terraform apply`)
3. ✅ Test both working

### Medium Term
- [ ] Add authentication to Flux 2
- [ ] Store generated images in Azure Blob Storage
- [ ] Create CI/CD pipeline (GitHub Actions)
- [ ] Add monitoring & alerts

### Long Term
- [ ] Multi-GPU support (NC12s_v3, NC24s_v3)
- [ ] Video generation integration
- [ ] Model caching layer
- [ ] Custom fine-tuning pipeline

---

## 📞 Need Help?

1. **Local Flux 2 issues** → Check [QUICKSTART.md](QUICKSTART.md)
2. **Terraform/ComfyUI** → Check [infra/README.md](infra/README.md)
3. **Azure quota errors** → Check Azure Portal or run `az vm list-skus`
4. **SSH access** → Verify NSG allows port 22: `az network nsg rule list -g comfyui-rg`

---

## 🚀 You're Ready!

**Start here:**
```bash
# Option 1: Local Flux 2
npm run dev

# Option 2: GPU ComfyUI on Azure
cd infra/
terraform apply
```

Happy creating! 🎨
