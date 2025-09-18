"""
V4 版本的 FastAPI 介面，用於處理 VM 助理 Agent 對話，支援多使用者 session 與錯誤處理。
"""

# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import HTTPException
import traceback  # 若你想 log 更詳細的錯誤

from agent.session import *
from agent.agent_vm import handle_vm_creation_flow  # 🆕 加入建立判斷邏輯


app = FastAPI()

# ➕ 允許 CORS（跨來源請求）
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://vm-assistant.example.com", "https://vm-assistant.example.com"],  # 依實際有無 https 調整
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 依實際有無 https 調整
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定請求格式
class ChatRequest(BaseModel):
    token: str
    message: str

# 定義 API URL
@app.post("/v4/agent/vm")
async def create_vm_chat_v4(req: ChatRequest):
    """
    處理 VM 助理對話請求，透過 token 管理 session 狀態，並回傳 LLM 回應。
    :param req: token 與使用者訊息
    :return: 回應訊息
    """
    try:
        manager = session_store.get_or_create(req.token)
        
        # 第一步：先處理 Agent 回覆（參數收集）
        reply = await manager.chat(req.message)

        # 第二步：如果參數齊全且使用者輸入「確定建立」，則嘗試建立 VM
        finished, system_msg = handle_vm_creation_flow(manager, req.message, session_store)

        # 第三步：如果 VM 建立了，或有錯誤訊息，也加到回傳中
        if system_msg:
            reply += f"\n{system_msg}"

        return {"reply": reply, "done": finished}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="❌ Agent 發生內部錯誤，請稍後再試。")

# 可以加上健查驗證 endpoint
@app.get("/v4/agent/ping")
def ping():
    return {"status": "ok"}