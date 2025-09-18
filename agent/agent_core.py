from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, Agent, Runner, function_tool
from agents import set_default_openai_client, set_tracing_disabled
from api.trustedcloud_vm_creator import TrustedCloudVMBuilder

class VMModelInitializer:
    # llama3.3:70b-instruct-q5_K_M 
    # mistral-small3.1:24b-instruct-2503-q4_K_M
    def __init__(self, base_url: str = "http://140.110.160.134:11434/v1", api_key: str = "ollama", model_name: str = "llama3.3:70b-instruct-q5_K_M"):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = OpenAIChatCompletionsModel(model=model_name, openai_client=self.client)

    def activate(self):
        set_default_openai_client(self.client)
        set_tracing_disabled(True)

class VMResources:
    # def __init__(self, builder, token: str, project_id: str):
    def __init__(self, builder, token: str):
        self.builder = builder
        self.img_dict = self.builder.list_image()
        self.fla_list = self.builder.list_flavors()
        self.net_dict = self.builder.list_network()
        self.sec_dict = self.builder.list_security_groups()
        self.fla_dict = {f["name"]: f for f in self.fla_list}

    def get_available_options(self):
        return {
            "image": list(self.img_dict.keys()),
            "flavor": list(self.fla_dict.keys()),
            "network": list(self.net_dict.keys()),
            "security_group": list(self.sec_dict.keys()),
        }

def make_vm_param_setters(wrapper):
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
    def confirm_create_vm(confirm: bool):
        ctx = wrapper.context
        if not confirm:
            return "⛔ 已取消建立 VM。"
        if not all([ctx["image_id"], ctx["flavor_id"], ctx["network_id"], ctx["security_group_id"], ctx["password_plain"]]):
            return "⚠️ 建立失敗，仍有未設定參數。"

        result = wrapper.resources.builder.create_vm(
            wrapper.resources.img_dict[ctx["image_id"]],
            wrapper.resources.fla_dict[ctx["flavor_id"]]["id"],
            wrapper.resources.net_dict[ctx["network_id"]],
            wrapper.resources.sec_dict[ctx["security_group_id"]],
            ctx["password_plain"]
        )
        
        wrapper.reset_context()
        if result:
            return f"✅ 已成功建立 VM：{result.get('id')}，名稱為 {result.get('name', '未知')}"
        return "❌ 建立 VM 失敗。請檢查參數或稍後再試。"

    return [set_image, set_flavor, set_network, set_security_group, set_password, confirm_create_vm]

class VMAgentWrapper:
    def __init__(self, agent, resources):
        self.agent = agent
        self.resources = resources
        self.context = {
            "image_id": None,
            "flavor_id": None,
            "network_id": None,
            "security_group_id": None,
            "password_plain": None,
        }
        self.chat_history = []

        self.reset_context()

    def reset_context(self):
        for k in self.context:
            self.context[k] = None

    def get_context_text(self):
        return "\n".join(f"{k}: {v if v else '尚未提供'}" for k, v in self.context.items())

    async def chat_once_async(self, user_input: str) -> str:
        self.chat_history.append({"role": "user", "content": user_input})
        prompt = self.agent.instructions.replace("{current_params}", self.get_context_text())
        messages = [{"role": "system", "content": prompt}] + self.chat_history
        response = await Runner.run(self.agent, messages)
        self.chat_history.append({"role": "assistant", "content": response.final_output})
        return response.final_output

class VMAgentManager:
    # def __init__(self, token: str, project_id: str):
        # builder = TrustedCloudVMBuilder(token, project_id)
        # self.resources = VMResources(builder, token, project_id)
    def __init__(self, token: str):
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
    def build_instruction(self):
        lines = [f"{k} 可選：{'、'.join(v)}" for k, v in self.available_options.items()]
        option_text = "\n".join(lines)
        return f"""
                你是一位雲端 VM 助理，請依序協助使用者設定五個參數，包含：image、flavor、network、security_group、password。
                完成後請詢問使用者是否要建立 VM，需明確確認後才能呼叫 confirm_create_vm 函數。 \n\n

                禁止事項：
                - 🚫 你不能主動填入任何預設值（即使你覺得使用者最常用 rocky_9 也不行）\n
                - ✅ 任何參數都只能在使用者明確輸入、確認之後，才能執行對應的工具函數 \n
                - ❌ 不可主動幫使用者決定參數 \n
                - 不可在未確認前自動建立 VM \n
                - 不可自己填入參數 \n
                - 每次只能設定一個參數 \n
                - 回覆時不要提到任何函數名稱 \n
                - 回覆以繁體中文為主 \n\n

                目前已設定參數：
                {{current_params}}

                可選項目：
                {option_text}
                """

    async def chat(self, user_input: str):
        return await self.wrapper.chat_once_async(user_input)

# ✅ session 管理（多用戶支援）
class SessionStore:
    def __init__(self):
        self.store = {}

    #def get_or_create(self, token: str, project_id: str):
    def get_or_create(self, token: str):
        vm_manager = VMAgentManager(token)
        project_id = vm_manager.builder.project_id
        key = f"{token}_{project_id}"
        if key not in self.store:
            #self.store[key] = VMAgentManager(token, project_id)
            self.store[key] = vm_manager
        return self.store[key]

session_store = SessionStore()
