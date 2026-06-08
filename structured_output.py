"""
结构化输出
让 LLM 返回 JSON，用代码解析和使用
"""
import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 示例1：解析用户信息 ======

def extract_person_info(text: str) -> dict:
    """从自然语言中提取人物信息，返回结构化 JSON"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "从用户输入中提取人物信息，只返回 JSON，不要有任何其他文字。\n"
                    "格式：{\"name\": \"姓名\", \"age\": 年龄数字或null, \"city\": \"城市或null\", \"job\": \"职业或null\"}"
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


# ====== 示例2：商品信息提取 ======

def extract_product_info(text: str) -> dict:
    """从商品描述中提取结构化信息"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "从商品描述中提取关键信息，只返回 JSON，不要有任何其他文字。\n"
                    "格式：{\"name\": \"商品名\", \"price\": 价格数字或null, \"category\": \"分类\", \"features\": [\"特点1\", \"特点2\"]}"
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


# ====== 示例3：情感分析 ======

def analyze_sentiment(text: str) -> dict:
    """分析文本情感，返回结构化结果"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "分析文本的情感，只返回 JSON，不要有任何其他文字。\n"
                    "格式：{\"sentiment\": \"positive/negative/neutral\", \"score\": 0到1的小数, \"reason\": \"简短理由\"}"
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


# ====== 主程序：交互演示 ======

DEMOS = {
    "1": ("人物信息提取", extract_person_info),
    "2": ("商品信息提取", extract_product_info),
    "3": ("情感分析", analyze_sentiment),
}

EXAMPLES = {
    "1": "我叫张伟，今年28岁，在北京做软件工程师",
    "2": "全新苹果 iPhone 16 Pro，售价9999元，支持5G，搭载A18芯片，钛金属边框",
    "3": "这家餐厅真的太棒了！菜品新鲜，服务热情，价格也很合理，下次还会来",
}

print("📦 结构化输出演示\n")
print("选择功能：")
for k, (name, _) in DEMOS.items():
    print(f"  {k}. {name}（示例：{EXAMPLES[k][:20]}...）")
print()

choice = input("输入序号（1/2/3）：").strip()
if choice not in DEMOS:
    print("无效选项")
    exit()

name, func = DEMOS[choice]
print(f"\n示例输入：{EXAMPLES[choice]}")
use_example = input("直接用示例？(y/n): ").strip().lower()

if use_example == "y":
    text = EXAMPLES[choice]
else:
    text = input("输入文本：").strip()

print(f"\n⏳ 正在解析...")
result = func(text)

print(f"\n✅ 结构化结果：")
print(json.dumps(result, ensure_ascii=False, indent=2))

# 演示如何在代码中使用解析出的字段
print("\n📌 代码中访问各字段：")
for key, value in result.items():
    print(f"  result['{key}'] = {repr(value)}")
