FROM python:3.12-slim

WORKDIR /app

# 安裝必要套件
COPY services/llm_api/llm_api.py /app/
COPY services/llm_api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼
# COPY ../../ .
COPY . /app

# 預設啟動指令
CMD ["uvicorn", "llm_api:app", "--host", "0.0.0.0", "--port", "7001"]
# ENTRYPOINT ["uvicorn"]
