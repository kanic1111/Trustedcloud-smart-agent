"""
V4 版本的 FastAPI 介面，用於處理 VM 助理 Agent 對話，支援多使用者 session 與錯誤處理。
"""

# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Literal, List
import re
import traceback

from agent.session_llm import *
from utils.parser import *

app = FastAPI()

# 提供靜態圖片資料夾服務（預設圖片放在 static/images/）
app.mount("/images", StaticFiles(directory="data_image/trusted-cloud/image"), name="images")

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

# 回應格式：圖片與文字交錯，保持順序
class ContentItem(BaseModel):
    type: Literal["text", "image"]
    value: str

class ChatResponse(BaseModel):
    #reply: str
    content: List[ContentItem]
    #done: bool
    
# 定義 API URL
@app.post("/v1/chat", response_model=ChatResponse)
async def chat_v1(req: ChatRequest):
    """
    處理 VM 助理對話請求，透過 token 管理 session 狀態，並回傳 LLM 回應。
    :param req: token 與使用者訊息
    :return: 回應訊息
    """
    try:
        # 處理圖片路徑
        parser = ImageTagParser()
        
        manager = session_store.get_or_create(req.token)
        
        # 第一步：先處理 Agent 回覆（參數收集）
        reply = await manager.chat(req.message)
        
        # 轉 reply 格式
        reply = str(reply)
        
        # 圖文處理
        content = parser.convert_image_tags(reply)
        
        return {"content": content}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="❌ Agent 發生內部錯誤，請稍後再試。")

# 可以加上健查驗證 endpoint
@app.get("/v1/chat/ping")
def ping():
    return {"status": "ok"}