FROM python:3.12-slim

WORKDIR /app

# 安裝依賴（路徑改成相對於 build context）
COPY services/vm_agent_api/vm_api.py /app/
COPY services/llm_api/llm_api.py /app/
COPY services/jupyter_agent_api/jupyter_agent_api.py /app/
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製所有程式碼
# COPY ../../ .
COPY . /app
COPY data_image/trusted-cloud/image /app/trusted-cloud/image

# 預設啟動指令
#CMD ["uvicorn", "vm_api:app", "--host", "0.0.0.0", "--port", "8001"]
ENTRYPOINT ["uvicorn"]
