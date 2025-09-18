import asyncio
from agent.session import *
import asyncio
from agent.agent_vm import handle_vm_creation_flow

def main():
    print("👋 歡迎使用可信賴雲 VM 助理 CLI 版本")
    token = input("請輸入 token：").strip()
    manager = session_store.get_or_create(token)

    while True:
        user_input = input("你：").strip()
        if user_input.lower() in ["quit", "exit"]:
            print("👋 掰掰！")
            break

        response = asyncio.run(manager.chat(user_input))
        print(f"🤖 {response}")

        finished, message = handle_vm_creation_flow(manager, user_input, session_store)
        if message:
            print(message)
        if finished:
            break

if __name__ == "__main__":
    main()
