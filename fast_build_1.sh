#!/bin/bash

# mkdir -p sanh/venv

# 更新系統並安裝必要的套件
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-venv docker.io

sudo systemctl start docker
sudo systemctl enable docker

sudo groupadd docker
sudo usermod -aG docker ubuntu
# newgrp docker

# 更新套件庫並安裝必要的套件
sudo apt-get update
sudo apt install -y python3-pip python3-venv docker-compose

# 安裝 NVIDIA 驅動程式與 Docker NVIDIA 插件
# 安裝 NVIDIA 驅動程式
sudo apt install -y nvidia-driver-525  # 根據需要調整為適當版本

# 重啟
sudo reboot






