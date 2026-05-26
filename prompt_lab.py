"""
Day 3: 4 种 Prompt 策略对比
同一个任务，4 种写法，看 AI 回复有什么不同。
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

def ask(system_prompt, user_input):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
    )
    return response.choices[0].message.content

task = "把下面这句话翻译成英文：'昨晚的月亮特别圆，像一个大银盘挂在天空。'"

print("=" * 60)
print("📝 任务：翻译一句中文 → 英文")
print("=" * 60)

# ① 零样本
print("\n--- ① 零样本（直接问）---")
r1 = ask("", task)
print(r1)

# ② 少样本
few_shot_prompt = """你是一个翻译助手。参考以下示例的风格来翻译：

示例1：
输入：'今天天气真好'
输出：'The weather is really nice today'

示例2：
输入：'他跑得比兔子还快'
输出：'He runs faster than a rabbit'

示例3：
输入：'山上的樱花全开了'
输出：'The cherry blossoms on the mountain are in full bloom'

现在翻译新的句子："""
print("\n--- ② 少样本（给 3 个例子）---")
r2 = ask(few_shot_prompt, task)
print(r2)

# ③ 思维链
cot_prompt = "你是一个翻译专家。在给出翻译之前，先分析：1）这句话用了什么修辞手法 2）关键意象是什么 3）然后给出流畅的英文翻译。一步步来。"
print("\n--- ③ 思维链（先分析再翻译）---")
r3 = ask(cot_prompt, task)
print(r3)

# ④ 角色扮演
role_prompt = "你是一位资深文学翻译家，曾在纽约客上发表过翻译作品。你追求'信达雅'，既要忠实原文，又要让英文读者感受到中文的美感。"
print("\n--- ④ 角色扮演（文学翻译家）---")
r4 = ask(role_prompt, task)
print(r4)

print("\n" + "=" * 60)
print("📊 4 种策略对比总结")
print("=" * 60)
print("""
策略          特点                    适合场景
────────────────────────────────────────────
零样本        快，但质量不稳定        简单任务
少样本        给例子，风格可控        格式要求严格的任务
思维链        逼 AI 一步步推理        复杂推理/数学题
角色扮演      设定人设，影响语气      需要特定风格或语境
""")
