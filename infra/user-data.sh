#!/bin/bash
# ComfyUI GPU VM Setup Script
# Installs NVIDIA drivers, CUDA, and ComfyUI

set -e

echo "=== ComfyUI VM Setup Starting ==="
echo "Timestamp: $(date)"

# Update system packages
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    python3-pip \
    python3-dev \
    python3-venv \
    libssl-dev \
    libffi-dev \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install NVIDIA GPU drivers
echo "Installing NVIDIA drivers and CUDA toolkit..."
apt-get install -y nvidia-driver-550 nvidia-cuda-toolkit

# Verify GPU
echo "Verifying GPU installation..."
which nvidia-smi || echo "Warning: nvidia-smi not found yet"

# Create ComfyUI user and directory
echo "Setting up ComfyUI..."
mkdir -p /opt/comfyui
cd /opt/comfyui

# Clone ComfyUI repository
git clone https://github.com/comfyanonymous/ComfyUI.git . || true

# Format and mount data disk if it exists
if [ -b /dev/sdc ]; then
    echo "Found data disk, formatting and mounting..."
    mkfs.ext4 -F /dev/sdc
    mkdir -p /mnt/comfyui-data
    mount /dev/sdc /mnt/comfyui-data
    chmod 777 /mnt/comfyui-data
    
    # Make persistent in fstab
    echo "/dev/sdc /mnt/comfyui-data ext4 defaults,nofail 0 0" >> /etc/fstab
    
    # Create symlink for models
    ln -sf /mnt/comfyui-data/models /opt/comfyui/models || true
fi

# Create Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv /opt/comfyui/venv
source /opt/comfyui/venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "Installing ComfyUI dependencies..."
pip install -r /opt/comfyui/requirements.txt || echo "Warning: Some pip installs may have failed"

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Create systemd service for ComfyUI
echo "Creating systemd service..."
cat > /etc/systemd/system/comfyui.service <<'EOF'
[Unit]
Description=ComfyUI Server
After=network.target
Requires=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/comfyui
ExecStart=/opt/comfyui/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable comfyui
systemctl start comfyui

echo "=== ComfyUI Setup Complete ==="
echo "Access ComfyUI at: http://$(hostname -I | awk '{print $1}'):8188"
echo "Service status: systemctl status comfyui"
echo "Service log: journalctl -u comfyui -f"
