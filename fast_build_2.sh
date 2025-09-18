#!/bin/bash

# 處理金鑰
sudo curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys DDCAE044F796ECB0

sudo rm /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list -o /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# 更新
sudo apt-get update

# 安裝 nvidia-docker2
sudo apt-get install -y nvidia-docker2

# 重啟 Docker
sudo systemctl restart docker


# 安裝必要的 Python 與 Docker 套件
sudo apt-get update
sudo apt install -y python3-pip python3-venv
sudo apt install -y python3-pip python3-venv docker-compose

# 創建資料夾
mkdir -p /home/ubuntu/storage_qdrant

# 啟動 Qdrant 容器
docker-compose -f ollama-qdrant.yml up -d

# docker pull Qdrant
docker pull qdrant/qdrant:latest
docker pull ollama/ollama

# 拉取ollama需要模型
docker exec -it ollama ollama pull bge-m3

# 創建 Docker 網路
docker network create llm_network

# 確保連線
docker network connect llm_network qdrant
docker network connect llm_network ollama

# 開啟新 shell，並保持虛擬環境中
bash -i

