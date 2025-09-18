# from openai import AsyncOpenAI
from agents import Agent, function_tool
# from agents import set_default_openai_client, set_tracing_disabled
from api.trustedcloud_vm_creator import TrustedCloudVMBuilder
#from agent.session import AgentWrapper
from prompt.prompt_formatter import PromptFormatter
from agent.model_initializer import *
import time

class VMResources:
    """
    封裝與 Builder 互動的 VM 資源資訊，例如映像檔、規格、網路與安全群組等。

    :param builder: TrustedCloudVMBuilder 的實例
    :param token: 使用者的 access token
    :return: 包含各項資源 dict，可用於下拉選單或參數驗證
    """
    # def __init__(self, builder, token: str, project_id: str):
    def __init__(self, builder, token: str):
        self.builder = builder
        self.img_dict = self.builder.list_image()
        self.fla_dict = self.builder.list_flavors()
        self.net_dict = self.builder.list_network()
        self.sec_dict = self.builder.list_security_groups()

    def get_available_options(self):
        return {
            "image": list(self.img_dict.keys()),
            "flavor": list(self.fla_dict.keys()),
            "network": list(self.net_dict.keys()),
            "security_group": list(self.sec_dict.keys()),
        }

def make_vm_param_setters(wrapper):
    """
    建立一組工具函數，用來讓使用者逐步設定 VM 所需參數。
    :param wrapper: 封裝 VM Agent 的物件，內含 context
    :return: 各項參數設定的工具函數清單
    """
    
    @function_tool
    def set_pass():
        pass
        return "開始建立vm。"

    @function_tool
    def set_image(image_id: str):
        # 僅當 image_id 是明確由使用者輸入時才允許設定
        if not image_id.strip():
            return "⚠️ 請提供有效的映像檔名稱。"

        if image_id not in wrapper.resources.img_dict:
            return f"❌ 無效的映像檔名稱：{image_id}"

        # 確認這個是使用者自己明確指定的（非 LLM 自行預設呼叫）
        wrapper.context["image_id"] = image_id
        return f"✅ 映像檔已設定為：{image_id}"

    @function_tool
    def set_flavor(flavor_id: str):
        if flavor_id in wrapper.resources.fla_dict:
            wrapper.context["flavor_id"] = flavor_id
            return f"✅ 規格已設定為：{flavor_id}"
        return f"❌ 無效的規格名稱：{flavor_id}"

    @function_tool
    def set_network(network_id: str):
        if network_id in wrapper.resources.net_dict:
            wrapper.context["network_id"] = network_id
            return f"✅ 網路已設定為：{network_id}"
        return f"❌ 無效的網路名稱：{network_id}"

    @function_tool
    def set_security_group(security_group_id: str):
        if security_group_id in wrapper.resources.sec_dict:
            wrapper.context["security_group_id"] = security_group_id
            return f"✅ 安全群組已設定為：{security_group_id}"
        return f"❌ 無效的安全群組名稱：{security_group_id}"

    @function_tool
    def set_password(password_plain: str):
        wrapper.context["password_plain"] = password_plain
        return f"✅ 密碼已設定"

    @function_tool
    def show_parameters():
        ctx = wrapper.context
        if not all([ctx["image_id"], ctx["flavor_id"], ctx["network_id"], ctx["security_group_id"], ctx["password_plain"]]):
            return "⚠️ 尚有參數未設定完整，請繼續填寫。"
        return {
            "message": "🎯 所有參數已設定完成，請確認以下資訊：",
            "parameters": ctx
        }

    return [set_image, set_flavor, set_network, set_security_group, set_password, show_parameters]


from agent.session import AgentWrapper
class VMAgentWrapper(AgentWrapper):
    """
    VM 專用的 Agent 包裝器，繼承共用 AgentWrapper，加入 VM 所需的 context。
    
    :param agent: 初始化後的 Agent 實例
    :param resources: VM 資源資訊封裝類別
    """
    def __init__(self, agent, resources):
        super().__init__(agent, resources)
        self.context = {
            "image_id": None,
            "flavor_id": None,
            "network_id": None,
            "security_group_id": None,
            "password_plain": None,
        }



class VMAgentManager:
    """
    專責處理 VM 建立流程的 Agent 管理器。
    :param token: 使用者身份識別 token
    :return: 封裝好指令工具與 Agent 的 VM 管理器
    """
    # def __init__(self, token: str, project_id: str):
        # builder = TrustedCloudVMBuilder(token, project_id)
        # self.resources = VMResources(builder, token, project_id)
    def __init__(self, token: str):
        self.token = token
        self.builder = TrustedCloudVMBuilder(token)
        self.resources = VMResources(self.builder, token)
        self.available_options = self.resources.get_available_options()
        self.instructions_template = self.build_instruction()

        initializer = VMModelInitializer()
        initializer.activate()
        model = initializer.model

        self.wrapper = VMAgentWrapper(None, self.resources)
        
        tools = make_vm_param_setters(self.wrapper)

        self.agent = Agent(
            name="VM Assistant",
            instructions=self.instructions_template,
            tools=tools,
            model=model
        )
        self.wrapper.agent = self.agent

        self.wrapper.reset_context()
         
        self.last_access_time = time.time()

    def update_access_time(self):
        """
        更新此 manager 的最後存取時間，用於閒置檢查。
        """
        self.last_access_time = time.time()

    def build_instruction(self):
        """
        組合完整的指令提示詞，將 context 狀態與可選項目一起嵌入 prompt。
        :return: 格式化後的指令用 Prompt 字串
        """
        prompt_formatter = PromptFormatter()
        instruction = prompt_formatter.format_prompt(
            context='',
            query=self.available_options,
            style="vm_instruction"
        )
        return instruction


    async def chat(self, user_input: str):
        return await self.wrapper.chat_once_async(user_input)
        
    def get_final_parameters(self):
        """
        提取目前已設定的參數（給後端 API 使用）
        :return: Dict 包含所有 VM 建立參數
        """
        return self.wrapper.context.copy()
        
    def create_vm_from_context(self, confirmation: str = ""):
        """
        根據目前參數建立 VM，需明確輸入確認字串才會建立。
        
        :param confirmation: 用戶輸入的確認字串，必須是「確定建立」才會執行
        :return: dict 回傳建立結果或錯誤訊息
        """
        params = self.get_final_parameters()
        
        # 先檢查參數完整度
        if not all([
            params.get("image_id"),
            params.get("flavor_id"),
            params.get("network_id"),
            params.get("security_group_id"),
            params.get("password_plain")
        ]):
            return {"success": False, "message": "參數未完整，無法建立 VM。"}
        
        user_confirmation = confirmation.strip().lower()
        # 確認字串必須是「確定建立」
        if user_confirmation != "confirm create":
            return {"success": False, "message": "Please enter「confirm create」to proceed with VM creation."}
        
        # 執行建立
        result = self.builder.create_vm(
            self.resources.img_dict[params["image_id"]],
            self.resources.fla_dict[params["flavor_id"]],
            self.resources.net_dict[params["network_id"]],
            self.resources.sec_dict[params["security_group_id"]],
            params["password_plain"]
        )

        self.wrapper.reset_context()

        if result:
            return {"success": True, "message": f"✅ 已成功建立 VM：{result.get('id')}，名稱為 {result.get('name', '未知')}"}
        else:
            return {"success": False, "message": "❌ 建立 VM 失敗，請稍後再試。"}


def handle_vm_creation_flow(manager, user_input: str, session_store):
    """
    處理 VM 參數檢查及建立流程。

    :param manager: VMAgentManager 實例
    :param user_input: 使用者輸入字串
    :return: tuple (bool, str)
        bool: 是否結束流程（建立成功即 True）
        str: 回應訊息
    """
    ctx = manager.wrapper.context
    print('')
    print('params_complete')
    print(ctx)
    print('')
    params_complete = all([
        ctx.get("image_id"),
        ctx.get("flavor_id"),
        ctx.get("network_id"),
        ctx.get("security_group_id"),
        ctx.get("password_plain"),
    ])

    if params_complete:
        if "confirm create" in user_input:
            result = manager.create_vm_from_context(confirmation="confirm create")
            print('result')
            print(result)
            if result["success"]:
                manager.wrapper.reset_context()  # 建立成功清除狀態
                session_store.delete(manager.token)  # 標記流程結束
                return True, f"🤖 {result['message']}\n🎉 VM creation completed. Exiting the program."
            else:
                return False, f"⚠️ {result['message']}"
        else:
            return False, "⚠️ Please enter「confirm create」to proceed with VM creation."
    else:
        return False, None  # 參數尚未齊全，不做任何動作