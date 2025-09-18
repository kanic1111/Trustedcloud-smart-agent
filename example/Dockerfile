# 使用官方 Python 映像檔
FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 複製需求檔 & 安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式檔與 .env
COPY . .

# 設定預設命令
CMD ["python", "test_ollama_qdrant.py"]