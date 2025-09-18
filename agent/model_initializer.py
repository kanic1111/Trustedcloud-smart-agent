from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_default_openai_client, set_tracing_disabled
from utils.parser import *

class VMModelInitializer:
    """
    用於初始化共用的語言模型，包括 base_url、model_name 設定。

    :param base_url: 模型 API 的位置（例如 Ollama）
    :param api_key: 模型存取金鑰
    :param model_name: 模型名稱，例如 llama3.3:70b-instruct-q5_K_M
    """
    # http://140.110.160.134:11434/v1
    # http://140.110.160.97:30002/v1 志謙的 LLM
    # llama3.3:70b-instruct-q5_K_M 
    # mistral-small3.1:24b-instruct-2503-q4_K_M
    # llama4-scout
    
    def __init__(self, ) :
            # base_url: str = "http://140.110.160.97:30002/v1", 
            # api_key: str = "ollama", 
            # model_name: str = "llama4-scout") :
         
        self.ParserInitializer()
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        self.model = OpenAIChatCompletionsModel(model=self.model_name, openai_client=self.client)

    def activate(self) :
        """
        啟用此模型設定並關閉 tracing。
        """
        set_default_openai_client(self.client)
        set_tracing_disabled(True)
        
    def ParserInitializer(self) :
        """
        讀取基本參數。
        """
        imageparser = ImageTagParser()
        self.parser = imageparser.config
        
        self.base_url = self.parser['openai_base_url']
        self.api_key = self.parser['api_key']
        self.model_name = self.parser['llm_model_name']
