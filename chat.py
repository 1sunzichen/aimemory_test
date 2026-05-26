"""
Day 2: 命令行连续聊天
每次输入一句话，DeepSeek 回复。输入 quit 退出。
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# 对话历史（让 AI 记住之前聊了什么）
messages = [
    {"role": "system", "content": "你是一个友好的助手，用中文回答。"},
]

print("🤖 聊天开始（输入 quit 退出）\n")

while True:
    user_input = input("你: ")
    if user_input.lower() == "quit":
        print("👋 再见！")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )

    reply = response.choices[0].message.content
    print(f"AI: {reply}\n")
    messages.append({"role": "assistant", "content": reply})
