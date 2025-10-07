from fastapi import FastAPI
from llm_api import router as llm_router
from jupyter_agent_api import router as jupyter_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from vm_api import router as vm_router
import os 
app = FastAPI()
# 提供靜態圖片資料夾服務（預設圖片放在 static/images/）
app.mount("/images", StaticFiles(directory="data_image/trusted-cloud/image"), name="images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 依實際有無 https 調整
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vm_router, prefix="/agent")
app.include_router(llm_router, prefix="/agent")
app.include_router(jupyter_router, prefix="/agent")
# Optional root check
@app.get("/")
async def list_routes():
    route_list = []
    for route in app.routes:
        if hasattr(route, "methods"):  # normal routes
            route_list.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
        elif hasattr(route, "app"):  # mounted apps
            route_list.append({
                "path": route.path,
                "mounted_app": str(type(route.app).__name__)
            })
    return {"routes": route_list}
