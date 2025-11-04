# from openai import AsyncOpenAI
from agents import Agent, function_tool
from api.trustedcloud_vm_creator import TrustedCloudVMBuilder
from agent.session_jupyter import AgentWrapper
from prompt.prompt_formatter import PromptFormatter
from agent.model_initializer import *
import time

class VMResources:
    """
    封裝與 Builder 互動的 jupyter 資源資訊，例如映像檔、規格、網路與安全群組等。

    :param builder: TrustedCloudVMBuilder 的實例
    :param token: 使用者的 access token
    :return: 包含各項資源 dict，可用於下拉選單或參數驗證
    """
    # def __init__(self, builder, token: str, project_id: str):
    def __init__(self, builder, token: str):
        self.builder = builder
        # self.img_dict = self.builder.list_image()
        self.module_dict = self.builder.list_applications_projects()
        self.fla_dict = self.builder.list_flavors()
        self.net_dict = self.builder.list_network()
        self.sec_dict = self.builder.list_security_groups()
        self.key_dict = self.builder.list_keypairs()

    def get_available_options(self):
        return {
            "module_id": list(self.module_dict.keys()),
            "flavor_id": list(self.fla_dict.keys()),
            "network_id": list(self.net_dict.keys()),
            "security_group_ids": list(self.sec_dict.keys()),
            "ssh_key_pair": list(self.key_dict.keys()),
        }

def make_jupyter_param_setters(wrapper):
    """
    建立一組工具函數，用來讓使用者逐步設定 jupyter 所需參數。
    :param wrapper: 封裝 jupyter Agent 的物件，內含 context
    :return: 各項參數設定的工具函數清單
    """

    @function_tool
    def set_pass():
        pass
        return "開始建立jupyter。"

    @function_tool
    def set_name(name: str):
        wrapper.context["name"] = name
        return f"✅ name 已設定"

    @function_tool
    def set_module_id(module_id: str):
        if module_id in wrapper.resources.module_dict:
            wrapper.context["module_id"] = module_id
            return f"✅ 規格已設定為：{module_id}"
        return f"❌ 無效的規格名稱：{module_id}"


    @function_tool
    def set_flavor_id(flavor_id: str):
        if flavor_id in wrapper.resources.fla_dict:
            wrapper.context["flavor_id"] = flavor_id
            return f"✅ 規格已設定為：{flavor_id}"
        return f"❌ 無效的規格名稱：{flavor_id}"

    @function_tool
    def set_network_id(network_id: str):
        if network_id in wrapper.resources.net_dict:
            wrapper.context["network_id"] = network_id
            return f"✅ 網路已設定為：{network_id}"
        return f"❌ 無效的網路名稱：{network_id}"

    @function_tool
    def set_security_group_ids(security_group_ids: str):
        if security_group_ids in wrapper.resources.sec_dict:
            wrapper.context["security_group_ids"] = security_group_ids
            return f"✅ 安全群組已設定為：{security_group_ids}"
        return f"❌ 無效的安全群組名稱：{security_group_ids}"

    @function_tool
    def set_ssh_key_pair(ssh_key_pair: str):
        if ssh_key_pair in wrapper.resources.key_dict:
            wrapper.context["ssh_key_pair"] = ssh_key_pair
            return f"✅ SSH 金鑰已設定為：{ssh_key_pair}"
        return f"❌ 無效的 SSH 金鑰名稱：{ssh_key_pair}"

    @function_tool
    def set_service_port(service_port: str):
        wrapper.context["service_port"] = service_port
        return f"✅ service_port 已設定"

    @function_tool
    def set_password(password: str):
        wrapper.context["password"] = password
        return f"✅ 密碼已設定"


    @function_tool
    def show_parameters():
        ctx = wrapper.context
        if not all([ctx.get("name"),
                    ctx.get("module_id"),
                    ctx.get("flavor_id"),
                    ctx.get("network_id"),
                    ctx.get("security_group_ids"),
                    ctx.get("password"),
                    ctx.get("service_port"),
                    ctx.get("ssh_key_pair")]):
            return "⚠️ 尚有參數未設定完整，請繼續填寫。"
        return {
            "message": "🎯 所有參數已設定完成，請確認以下資訊：",
            "parameters": ctx
        }
        
    return [set_name, 
            set_module_id,
            set_flavor_id, 
            set_network_id, 
            set_security_group_ids, 
            set_ssh_key_pair, 
            set_service_port,
            set_password,
            show_parameters]



class VMAgentWrapper(AgentWrapper):
    """
    VM 專用的 Agent 包裝器，繼承共用 AgentWrapper，加入 VM 所需的 context。
    
    :param agent: 初始化後的 Agent 實例
    :param resources: VM 資源資訊封裝類別
    """
    def __init__(self, agent, resources):
        super().__init__(agent, resources)
        self.context = {
            "name": None,
            "module_id": None,
            "flavor_id": None,
            "network_id": None,
            "password": None,
            "security_group_ids": None,
            "service_port": None,
            "ssh_key_pair": None,
            # "ssh_port": None,
            # "namespace": None,
            # "description": None,
            
        }



class VMAgentManager:
    """
    專責處理 jupyter 建立流程的 Agent 管理器。
    :param token: 使用者身份識別 token
    :return: 封裝好指令工具與 Agent 的 VM 管理器
    """

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
        
        tools = make_jupyter_param_setters(self.wrapper)

        self.agent = Agent(
            name="jupyter Assistant",
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
            style="jupyter_instruction"
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
        
    def create_jupyter_from_context(self, confirmation: str = ""):
        """
        根據目前參數建立 jupyter，需明確輸入確認字串才會建立。
        
        :param confirmation: 用戶輸入的確認字串，必須是「確定建立」才會執行
        :return: dict 回傳建立結果或錯誤訊息
        """
        params = self.get_final_parameters()
        
        # 先檢查參數完整度
        if not all([
            params.get("name"),
            params.get("module_id"),
            params.get("flavor_id"),
            params.get("network_id"),
            params.get("password"),
            params.get("security_group_ids"),
            params.get("service_port"),
            params.get("ssh_key_pair"),
        ]):
            return {"success": False, "message": "Please enter「confirm create」to proceed with jupyter creation."}
        
        #user_confirmation = confirmation.strip().lower()
        user_confirmation = confirmation
        # 確認字串必須是「confirm create」
        if user_confirmation != "confirm create":
            return {"success": False, "message": "請輸入「確定建立」以確認建立 VM。"}
        
        print('params')
        print(params)
        print(params["name"])
        print(self.resources.module_dict[params["module_id"]])
        print(self.resources.fla_dict[params["flavor_id"]])
        print(self.resources.net_dict[params["network_id"]])
        print(params["password"])
        print(self.resources.sec_dict[params["security_group_ids"]])
        print(params["service_port"])
        print(self.resources.key_dict[params["ssh_key_pair"]])
        
        print('self.builder.list_module')
        print(self.builder.list_module('module_id', self.resources.module_dict[params["module_id"]]))
        print(self.builder.list_module('module_id', self.resources.module_dict[params["module_id"]])['module_id'])
        module_id = self.builder.list_module('module_id', self.resources.module_dict[params["module_id"]])['module_id']
        
        # 執行建立
        result = self.builder.create_application(
            params["name"],
            # self.resources.module_dict[params["module_id"]],
            module_id,
            self.resources.fla_dict[params["flavor_id"]],
            self.resources.net_dict[params["network_id"]],
            params["password"],
            [self.resources.sec_dict[params["security_group_ids"]]],
            params["service_port"],
            self.resources.key_dict[params["ssh_key_pair"]],
            
        )
        self.wrapper.reset_context()

        if result:
            return {"success": True, "message": f"✅ Successfully created VM: {result.get('id')}, with name {result.get('name', 'Unknown')}"}
        else:
            return {"success": False, "message": "❌ Failed to create VM. Please try again later."}
    
    
def handle_jupyter_creation_flow(manager, user_input: str, session_store):
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
        ctx.get("name"),
        ctx.get("module_id"),
        ctx.get("flavor_id"),
        ctx.get("network_id"),
        ctx.get("password"),
        ctx.get("security_group_ids"),
        ctx.get("service_port"),
        ctx.get("ssh_key_pair"),
        
    ])
    print('params_complete')
    print(params_complete)

    if params_complete:
        # 轉為小寫，並去頭尾空白
        user_input = user_input.strip().lower()

        if "confirm create" in user_input:
            result = manager.create_jupyter_from_context(confirmation="confirm create")
            if result["success"]:
                manager.wrapper.reset_context()  # 建立成功清除狀態
                session_store.delete(manager.token)  # 標記流程結束
                return True, f"🤖 {result['message']}\n🎉 creation completed. Exiting the program."
            else:
                return False, f"⚠️ {result['message']}"
        else:
            return False, "⚠️ Please enter「confirm create」to proceed with jupyter creation."
    else:
        return False, None  # 參數尚未齊全，不做任何動作


