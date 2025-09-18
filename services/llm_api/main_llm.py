import asyncio
from agent.session_llm import *
import asyncio

def main():
    print("🧪 這是 CLI 測試工具，輸入 token 開始對話")
    token = input("請輸入 token：").strip()
    manager = session_store.get_or_create(token)

    while True:
        user_input = input("你：").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        response = asyncio.run(manager.chat(user_input))
        print(f"助理：{response}")


if __name__ == "__main__":
    main()
