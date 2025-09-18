from agents import Agent, Runner
import time
import threading

class AgentWrapper:
    """
    Agent 對話封裝基底類別，提供對話歷史管理與 context 狀態。
    :param agent: Agent 實例
    :param resources: 可用資源（如 images, networks 等）
    """
    def __init__(self, agent, resources):
        """
        初始化對話封裝器，綁定 Agent 與資源並初始化 context 與歷史紀錄。
        :param agent: 指定的 Agent 實例
        :param resources: 傳入可用的資源字典物件
        """
        
        self.agent = agent
        self.resources = resources
        self.context = {}
        self.chat_history = []
        self.reset_context()

    def reset_context(self):
        """
        重設 context 內所有參數為 None。
        :return: 無回傳值
        """
        
        for k in self.context:
            self.context[k] = None

    def get_context_text(self):
        """
        取得目前 context 的文字表示（用於 prompt 中顯示）。
        :return: 字串格式的 context 狀態，尚未設定的欄位會顯示「尚未提供」
        """
        return "\n".join(f"{k}: {v if v else '尚未提供'}" for k, v in self.context.items())

    async def chat_once_async_old(self, user_input: str) -> str:
        """
        執行一次與 Agent 的對話，加入對話歷史並取得回應。
        :param user_input: 使用者輸入的文字
        :return: 模型回應的文字內容
        """
        
        self.chat_history.append({"role": "user", "content": user_input})
        prompt = self.agent.instructions.replace("{current_params}", self.get_context_text())
        messages = [{"role": "system", "content": prompt}] + self.chat_history
        response = await Runner.run(self.agent, messages)
        self.chat_history.append({"role": "assistant", "content": response.final_output})
        return response.final_output
        
    async def chat_once_async(self, user_input: str) -> str:
        """
        執行一次與 Agent 的對話，加入對話歷史並取得回應。
        :param user_input: 使用者輸入的文字
        :return: 模型回應的文字內容
        """
        try :
            
            # 新增使用者訊息
            
            self.chat_history.append({"role": "user", "content": user_input})

            # 系統 prompt 固定用 agent.instructions，不再動態替換
            # system_prompt = self.agent.instructions

            # 組成完整的 messages
            # messages = [{"role": "system", "content": system_prompt}] + self.chat_history
            
            messages = self.chat_history.copy()
            
            # 呼叫 Runner 執行 Agent 回應
            response = await Runner.run(self.agent, messages)
            
            # 將回應加入歷史
            self.chat_history.append({"role": "assistant", "content": response.final_output})
            
        except Exception as e:
            
            # 若出現錯誤，也記錄到對話歷史中（可選）
            self.chat_history.append({"role": "assistant", "content": f"⚠️ 發生錯誤：{str(e)}"})
            # 或單純記錄 log，避免前端看到技術細節
            print(f"[Agent Error] {str(e)}")
            return "⚠️ 發生內部錯誤，請稍後再試或聯繫開發人員。"
        
        return response.final_output




from agent.agent_jupyter import VMAgentManager
class SessionStore:
    """
    管理所有使用者的 Agent Session 實例，並自動移除超過閒置時間的 Session。
    :param token: 使用者的身份識別 token
    :return: 對應的 Agent 管理器實例
    """
    
    def __init__(self, timeout: int = 1800, cleanup_interval: int = 60):
        """
        初始化 SessionStore。

        :param timeout: session 閒置多久會被清除（秒）
        :param cleanup_interval: 多久檢查一次（秒）
        """
        self.store = {}
        self.timeout = timeout
        self.cleanup_interval = cleanup_interval
        self.lock = threading.Lock()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """
        啟動背景執行緒，定期清理過期 session。
        """
        thread = threading.Thread(target=self.cleanup_expired_sessions, daemon=True)
        thread.start()
        print("🧼 Session Cleanup Thread 啟動完成")

    def get_or_create(self, token: str) -> VMAgentManager:
        
        """
        取得或創建一個對應使用者的 VMAgentManager。

        :param token: 使用者的識別 token
        :return: 對應的 VMAgentManager
        """
        with self.lock:
            if token in self.store:
                manager = self.store[token]
                manager.update_access_time()
            else:
                manager = VMAgentManager(token)
                self.store[token] = manager
                print(f"✅ 新增 session：{token}")
        return manager

    def cleanup_expired_sessions(self):
        """
        清理所有過期的 session，並顯示目前所有 session 剩餘時間。
        """
        while True:
            time.sleep(self.cleanup_interval)
            now = time.time()
            with self.lock:
                to_delete = []
                print(f"\n🧹 [Session Cleanup] {time.strftime('%X')} 開始檢查所有 session：")
                for token, manager in self.store.items():
                    idle_time = now - manager.last_access_time
                    remaining_time = self.timeout - idle_time
                    if remaining_time <= 0:
                        print(f"❌ Token: {token} - 已閒置 {int(idle_time)} 秒，將刪除")
                        to_delete.append(token)
                    else:
                        print(f"✅ Token: {token} - 尚有 {int(remaining_time)} 秒可以使用")

                for token in to_delete:
                    del self.store[token]
                    print(f"🗑️ 已刪除過期 session：{token}")

    def delete(self, token: str):
        """
        手動移除某個 session。
        :param token: 使用者 token
        :param project_id: 專案 ID
        """
        vm_manager = VMAgentManager(token)
        project_id = vm_manager.builder.project_id
        key = f"{token}_{project_id}"
        if key in self.store:
            del self.store[key]

session_store = SessionStore()


