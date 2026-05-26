"""
Day 4: System Prompt — 给 AI 套人设
选一个人设，持续聊天。输入 /persona 换人。
"""
import readline  # 修复终端退格问题
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

PERSONAS = {
    "2": {"name": "王阳明", "prompt": "你是王阳明，心学创始人。半文半白，温和有分量。每次不超过 4 句话。"},
    "6": {"name": "李白", "prompt": "你是李白，刚喝了三壶酒微醺。用诗的语言回答，飘逸豪放。"},
    "7": {"name": "庄子", "prompt": "你是庄子，中国的庄子"},
}

# ====== 选人设 ======
print("🎭 选一个人设：")
for key, p in PERSONAS.items():
    print(f"  [{key}] {p['name']}")
print("  [x] 自己写")

choice = input("选: ").strip()

if choice == "x":
    name = input("人设名: ").strip()
    prompt = input("描述: ").strip()
else:
    persona = PERSONAS.get(choice, PERSONAS["1"])
    name = persona["name"]
    prompt = persona["prompt"]

messages = [{"role": "system", "content": prompt}]
print(f"\n🤖 现在你是 {name}。聊天开始！")
print("   /persona = 换人设   /reset = 清记忆   /quit = 退出\n")

while True:
    user = input("你: ").strip()

    if user == "/quit":
        print(f"👋 {name} 下线了")
        break
    if user == "/persona":
        print("\n换谁？")
        for key, p in PERSONAS.items():
            print(f"  [{key}] {p['name']}")
        new = input("选: ").strip()
        if new in PERSONAS:
            name = PERSONAS[new]["name"]
            prompt = PERSONAS[new]["prompt"]
            messages = [{"role": "system", "content": prompt}]
            print(f"🤖 现在变身 {name}\n")
        continue
    if user == "/reset":
        messages = [{"role": "system", "content": prompt}]
        print("🔄 记忆已清空\n")
        continue

    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    reply = response.choices[0].message.content
    print(f"{name}: {reply}\n")
    messages.append({"role": "assistant", "content": reply})
