import os
import json
from dotenv import load_dotenv
import requests
from qdrant_client import QdrantClient

# ----------------------
# 讀取環境變數
# ----------------------
load_dotenv(dotenv_path="./.env")

VM_HOST = os.getenv("VM_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT") 
OLLAMA_PORT = os.getenv("OLLAMA_PORT")
COLLECTION_NAME = "trusted-cloud_20250701_512_10_bge-m3"

# ----------------------
# 1️⃣ 建立 Qdrant 連線
# ----------------------
qdrant_url = f"http://{VM_HOST}:{QDRANT_PORT}"
client = QdrantClient(url=qdrant_url)

try:
    info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Qdrant collection '{COLLECTION_NAME}' info:")
    print(info)
except Exception as e:
    print(f"連接 Qdrant 失敗: {e}")

# ----------------------
# 2️⃣ 取得 Ollama embedding
# ----------------------
query_text = "請簡單介紹平台概覽"
top_k = 3

embedding_url = f"http://{VM_HOST}:{OLLAMA_PORT}/v1/embeddings"
try:
    resp = requests.post(
        embedding_url,
        json={
            "model": "bge-m3",
            "input": query_text
        }
    )
    query_vector = resp.json()["data"][0]["embedding"]
except Exception as e:
    print(f"連接 Ollama 取得 embedding 失敗: {e}")
    query_vector = None

# ----------------------
# 3️⃣ 搜尋 Qdrant top-k
# ----------------------
if query_vector:
    try:
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )

        print("\nTop results:")
        for r in results:
            payload = r.payload
            file_name = payload.get('file', 'Unknown file')
            node_content_raw = payload.get('_node_content', '{}')

            try:
                node_content = json.loads(node_content_raw)
                metadata_file = node_content.get('metadata', {}).get('file', 'N/A')
                preview_list = node_content.get('excluded_embed_metadata_keys', [])
                preview_text = preview_list[0][:200] if preview_list else 'N/A'
            except json.JSONDecodeError:
                metadata_file = 'N/A'
                preview_text = 'N/A'

            print(f"- File: {file_name}")
            print(f"  Metadata file: {metadata_file}")
            print(f"  Preview: {preview_text}")
            print("-" * 50)
    except Exception as e:
        print(f"搜尋 Qdrant 發生錯誤: {e}")
