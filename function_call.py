"""
Day 5: Function Calling
让 LLM 调用你的 Python 函数 —— 查天气、算数学、看时间
"""
import os, json, math
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 你的 Python 函数（LLM 可以调用的工具） ======

def get_weather(city: str) -> str:
    """查天气（模拟数据）"""
    data = {
        "北京": "晴，25°C，北风3级",
        "上海": "多云，28°C，东南风2级",
        "东京": "小雨，22°C，西风4级",
        "纽约": "阴，18°C，北风5级",
    }
    return data.get(city, f"{city}：晴天，20°C（模拟数据）")

def calculator(expression: str) -> str:
    """安全计算数学表达式"""
    try:
        # 只允许数字和基本运算符
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含不允许的字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算出错：{e}"

def current_time() -> str:
    """返回当前时间"""
    now = datetime.now()
    return f"现在是 {now.year}年{now.month}月{now.day}日 {now.hour}:{now.minute:02d}"

def search_web(query: str) -> str:
    """搜索网页（模拟）"""
    data = {
        "python": "Python 是目前最流行的编程语言之一，广泛用于 AI、数据分析。",
        "deepseek": "DeepSeek 是中国开发的 AI 大模型，性价比极高。",
        "水浒传": "《水浒传》是元末明初施耐庵所著，讲 108 位好汉被逼上梁山的故事。",
    }
    for k, v in data.items():
        if k in query.lower():
            return v
    return f"关于「{query}」没有找到相关信息（模拟搜索）。"

# ====== 工具清单（告诉 LLM 有哪些函数可用） ======

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
                "required": ["city"]
            }
        }
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
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}}
        }
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
                "required": ["query"]
            }
        }
    },
]

# 函数名 → Python 函数 的映射
FUNCTIONS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "current_time": current_time,
    "search_web": search_web,
}

# ====== 对话循环 ======
messages = [
    {"role": "system", "content": "你是一个有用的助手。你可以调用的工具有：查天气、计算器、看时间、搜索网页。当用户的问题需要你查信息或计算时，请主动调用工具。用中文回答。"}
]

print("🤖 工具助手（输入 quit 退出）\n")
print("问天气、算数学、查时间、搜资料——我会自动调工具。\n")

while True:
    user = input("你: ").strip()
    if user.lower() == "quit":
        print("👋 再见！")
        break

    messages.append({"role": "user", "content": user})

    # 发给 LLM，让它决定是否需要调工具
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,
    )

    msg = response.choices[0].message

    # 如果 LLM 决定要调工具
    if msg.tool_calls:
        # 先把 LLM 的 tool_call 请求加入对话
        messages.append(msg)

        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"  🔧 调用工具：{func_name}({args})")

            # 执行你的 Python 函数
            func = FUNCTIONS[func_name]
            result = func(**args)
            print(f"  📊 结果：{result}")

            # 把工具执行结果告诉 LLM
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        # 让 LLM 基于工具结果生成最终回复
        final = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
        )
        reply = final.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}\n")

    else:
        # LLM 不需要调工具，直接回复
        reply = msg.content
        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}\n")
