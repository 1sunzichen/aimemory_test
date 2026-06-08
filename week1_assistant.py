"""
Week 1 Project: 命令行 AI 助手
聊天 + 工具调用 + 结构化输出
"""
import os, json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 工具函数 ======

def get_weather(city: str) -> str:
    data = {
        "北京": "晴，25°C，北风3级",
        "上海": "多云，28°C，东南风2级",
        "东京": "小雨，22°C，西风4级",
        "纽约": "阴，18°C，北风5级",
        "广州": "晴，32°C，微风",
        "深圳": "多云，30°C，南风2级",
    }
    return data.get(city, f"{city}：晴天，20°C（模拟数据）")

def calculator(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含不允许的字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错：{e}"

def current_time() -> str:
    now = datetime.now()
    return f"现在是 {now.year}年{now.month}月{now.day}日 {now.hour}:{now.minute:02d}"

def search_web(query: str) -> str:
    data = {
        "python": "Python 是目前最流行的编程语言之一，广泛用于 AI、数据分析、Web 开发。",
        "deepseek": "DeepSeek 是中国深度求索公司开发的 AI 大模型，性价比极高，开源免费。",
        "水浒传": "《水浒传》是元末明初施耐庵所著，讲 108 位好汉被逼上梁山的故事。",
        "openai": "OpenAI 是 GPT 系列模型的开发公司，旗下有 ChatGPT 等产品。",
        "人工智能": "人工智能（AI）是让计算机模拟人类智能的技术，当前以大语言模型为代表。",
    }
    for k, v in data.items():
        if k in query.lower():
            return v
    return f"关于「{query}」没有找到相关信息（模拟搜索）。"

def set_reminder(content: str, minutes: int) -> str:
    remind_time = datetime.now()
    return f"已设置提醒：{minutes} 分钟后提醒你「{content}」（模拟，实际不会弹出通知）"

# ====== 工具清单 ======

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如 北京、上海"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式，如 '(3+5)*2'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索网页获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "设置一个定时提醒",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "提醒内容"},
                    "minutes": {"type": "integer", "description": "多少分钟后提醒"},
                },
                "required": ["content", "minutes"],
            },
        },
    },
]

FUNCTIONS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "current_time": current_time,
    "search_web": search_web,
    "set_reminder": set_reminder,
}

# ====== 处理一轮对话（含工具调用） ======

def chat_once(messages: list) -> str:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,
    )
    msg = response.choices[0].message

    # LLM 不需要调工具，直接返回回复
    if not msg.tool_calls:
        messages.append({"role": "assistant", "content": msg.content})
        return msg.content

    # LLM 决定调工具
    messages.append(msg)

    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"  [工具] {func_name}({args})")

        result = FUNCTIONS[func_name](**args)
        print(f"  [结果] {result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    # 把工具结果交回 LLM，生成最终回复
    final = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )
    reply = final.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply

# ====== 主程序 ======

SYSTEM_PROMPT = """你是一个全能命令行助手，名字叫支离奇。
你拥有以下工具：查天气、数学计算、查看时间、搜索网页、设置提醒。
遇到需要查询或计算的问题时，主动调用工具而不是猜测。
回答简洁，用中文。"""

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("=" * 45)
print("   支离奇  |  聊天 + 工具调用")
print("=" * 45)
print("可以问我：天气 / 计算 / 时间 / 搜索 / 提醒")
print("输入 history 查看对话记录，quit 退出\n")

while True:
    try:
        user = input("你: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 再见！")
        break

    if not user:
        continue

    if user.lower() == "quit":
        print("👋 再见！")
        break

    if user.lower() == "history":
        print("\n--- 对话记录 ---")
        for m in messages[1:]:  # 跳过 system
            role = "你" if m["role"] == "user" else ("AI" if m["role"] == "assistant" else "工具")
            content = m["content"] if isinstance(m["content"], str) else str(m["content"])
            if content:
                print(f"{role}: {content[:80]}{'...' if len(content) > 80 else ''}")
        print("----------------\n")
        continue

    messages.append({"role": "user", "content": user})

    reply = chat_once(messages)
    print(f"支离奇: {reply}\n")
