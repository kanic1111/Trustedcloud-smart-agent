# LLM 相關庫
from llama_index.llms.ollama import Ollama
from openai import OpenAI

# Qdrant 相關庫
from rag.qdrant_retriever import *
from rag.bm25_retriever import *

# 嵌入模型
from llama_index.embeddings.ollama import OllamaEmbedding

# 系統工具庫
import shutil
import os
# 自定義庫
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker
from utils.parser import *
# 時間
import time

    #---------------------------------------------------------------------
    # 處理Qd & llm連線
class ModelHandler:
    # ========================================
    # ✅ 1. 初始化基本變數
    # ========================================
    def __init__(
        self,
        Qdrant_vector_collection_name,
        temp:float,
        api_key,
        llm_model_name,  # 範例格式 ['llmam3.3']
        openai_base_url,
        embed_model_name='bge-m3',
        reranker_model="BAAI/bge-reranker-large",
        reranker_top=5,
        similarity_top_k=10,
        qdrant_manager=None,

        ) :
        """
        初始化 ModelHandler 類，設置 LLM 模型、Qdrant 向量集合、reranker 及其他參數。
        :param Qdrant_vector_collection_name: Qdrant 向量集合名稱
        :param temp: 模型的溫度參數
        :param api_key: 用於 OpenAI 或 Claude 的 API 密鑰
        :param embed_model_name: 預設嵌入模型名稱
        :param reranker_model: Reranker 模型名稱
        """

        self.Qdrant_vector_collection_name = Qdrant_vector_collection_name
        self.llm_model_name = llm_model_name
        self.reranker_top = reranker_top
        self.temp = temp
        self.api_key = api_key
        self.embed_model_name = embed_model_name


        # TODO 要改參數讀取
        self.base_url, _  = self.get_base_url()
        self.openai_base_url = openai_base_url


        self.embed_model = self.embed_model_settings()
        self.similarity_top_k = similarity_top_k

        # ✅ 初始化 Qdrant 向量庫管理器
        self.qdrant_manager = qdrant_manager if qdrant_manager else QdrantManager()
        print('✅ embed_model和Qdrant name', self.embed_model, self.Qdrant_vector_collection_name)
        self.index = self.qdrant_manager.qdrant_vector(self.embed_model, self.Qdrant_vector_collection_name)

        # ✅ 初始化 Reranker
        self.reranker = FlagEmbeddingReranker(top_n=self.reranker_top, model=reranker_model)

        # ✅ 初始化 LLM 和檢索引擎
        self.retriever_engine = self.initialize_retriever_core()  # ⚡️ 這裡不使用 Streamlit 變數
        self.bm25_retriever = self.initialize_bm25retriever_core()# ⚡️ 建立bm25用retriever

    # ========================================
    # ✅ 1. 檢索引擎初始化（核心函數）
    # ========================================
    def initialize_retriever_core(self):
        """
        初始化檢索引擎（不依賴 Streamlit）。
        :return: 檢索引擎物件
        """
        retriever_engine = self.index.as_retriever(
            retriever_mode='embeddings',
            similarity_top_k=self.similarity_top_k,
            # node_postprocessors=[self.reranker] if self.reranker else [],
            verbose=True
        )
        print("✅ Retriever Engine Initialized (Core)")
        return retriever_engine

    def initialize_bm25retriever_core(self):
        """
        初始化檢索引擎（不依賴 Streamlit）。
        :return: 檢索引擎物件
        """
        print('✅--==', self.similarity_top_k)
        bm25_retriever = ChineseBM25Retriever(
            nodes=self.index.vector_store.get_nodes(),
            similarity_top_k=self.similarity_top_k
        )
        print("✅ Retriever Engine Initialized (Core)")
        return bm25_retriever

    # ========================================
    # ✅ 1_1. 檢索引擎更新（核心函數）
    # ========================================
    def update_bm25_db(self, Qdrant_vector_collection_name) :
        """
        bm25 檢索引擎更新（不依賴 Streamlit）。
        :return: bm25 檢索引擎物件
        """
        self.qdrant_manager = QdrantManager()
        self.index = self.qdrant_manager.qdrant_vector(self.embed_model, Qdrant_vector_collection_name)

        self.bm25_retriever = ChineseBM25Retriever(
            nodes=self.index.vector_store.get_nodes(),
            similarity_top_k=self.similarity_top_k
        )


    # ========================================
    # ✅ 2. LLM 初始化
    # ========================================
    def initialize_llm_openai(self, api_key='sk-SpAIVtz3qqbTXoBOJ-7O9A'):
        """
        初始化 OpenAI 模型。
        :return: llm -> OpenAI 物件
        """
        llm = OpenAI(
            base_url=self.openai_base_url,
            api_key=api_key
            )
        return llm


    # ========================================
    # ✅ 3. 嵌入模型設定與 API 基礎 URL
    # ========================================
    @staticmethod
    def is_docker_environment():
        """
        檢查當前環境是否為 Docker 容器內。
        :return: True（在 Docker 環境）或 False（本機環境）
        """
        return shutil.which("docker") is not None

    def get_base_url(self):
        """
        根據環境動態設置 base_url。
        :return: Docker 環境回傳 "http://localhost:11434"，否則回傳 "http://ollama:11434"
        """
        base_url = "http://localhost:11434" if self.is_docker_environment() else "http://ollama:11435"

        # ollama用url
        # openai_base_url = "http://localhost:11434/v1" if self.is_docker_environment() else "http://ollama:11434/v1"

        # 梅杜莎用
        openai_base_url = 'https://inner-medusa.genai.nchc.org.tw/v1'
        return (base_url, openai_base_url)

    def embed_model_settings(self):
        """
        初始化嵌入模型。
        :return: OllamaEmbedding 物件
        """
        embed_model = OllamaEmbedding(
            model_name=self.embed_model_name,
            base_url=self.base_url,
            ollama_additional_kwargs={"mirostat": 0}
            )
        return embed_model


    # ========================================
    # ✅ 5. 問 OpenAI 的問題
    # ========================================
    def ask_openai(self, llm, question, stream: bool = False):
        """
        使用已初始化的 OpenAI LLM 來問問題
        :param question: 使用者的問題 (str)
        :return: OpenAI 回應的內容 (str)
        """
        try:
            # 測試llm時間用
            parser = ImageTagParser()
            llm_start_time = time.time()

            response_stream = llm.chat.completions.create(
                model=self.llm_model_name[0],
                messages=question,
                temperature=self.temp,
                stream=stream,
            )

            print(f"🔹 LLM 時間: {time.time() - llm_start_time:.2f} 秒")
            print(response_stream)
            if stream:
            # async generator that yields chunks
                async def generate():
                    buffer = ""
                    for event in response_stream:
                        delta = event.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            buffer += delta.content + " "
                            print(buffer)
                            content = parser.convert_image_tags(buffer)
                            for parsed in content:
                                yield json.dumps(parsed, ensure_ascii=False) + "\n"
                            #yield content
                        buffer = ""
                return generate()
            else:
                return response_stream

        except Exception as e:
            print(f"❌ OpenAI 回應錯誤: {e}")
            return "發生錯誤，請稍後再試"


if __name__ == "__main__":
    # 設定相關參數
    QDRANT_COLLECTION_NAME = "20250121_ly_256"
    TEMPERATURE = 0.7
    API_KEY = ""  # 如果使用 OpenAI 或 Claude，請提供 API Key
    MODEL_NAME = "chatfire/bge-m3:q8_0"
    RERANKER_MODEL = "BAAI/bge-reranker-large"
    RERANKER_TOP_N = 5
    SIMILARITY_TOP_K = 10

    # 初始化 ModelHandler
    model_handler = ModelHandler(
        Qdrant_vector_collection_name=QDRANT_COLLECTION_NAME,
        temp=TEMPERATURE,
        api_key=API_KEY,
        model_name=MODEL_NAME,
        reranker_model=RERANKER_MODEL,
        reranker_top=RERANKER_TOP_N,
        similarity_top_k=SIMILARITY_TOP_K,
        llm_model_name='llama3.3:latest'
    )

    # 初始化 LLM


    # 初始化檢索引擎
    retriever_engine = model_handler.initialize_retriever_core()
    print("✅ 向量檢索引擎初始化完成")

    bm25_retriever = model_handler.initialize_bm25retriever_core()
    print("✅ BM25 檢索引擎初始化完成")

    # 測試提問與回答
    query = "請問量子計算與傳統計算的區別是什麼？"
    print(f"🔍 測試問題: {query}")

    # 釋放資源
    model_handler.release_resources()
    print("✅ 資源釋放完成")