"""
Day 1: 调通 DeepSeek API
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "你好，用一句话介绍一下你自己。"},
    ],
)

print(response.choices[0].message.content)
