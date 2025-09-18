FROM python:3.12-slim

WORKDIR /app

# 安裝必要套件
COPY services/jupyter_agent_api/jupyter_agent_api.py /app/
COPY services/jupyter_agent_api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼
COPY . /app

# 預設啟動指令
CMD ["uvicorn", "jupyter_agent_api.py:app", "--host", "0.0.0.0", "--port", "8002"]
# ENTRYPOINT ["uvicorn"]
