"""
🏯 大明模拟器 · 从七品到龙椅
3 个 NPC + 玩家 · 5 个回合 · 全由 LLM 驱动
"""
import os
import readline
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 世界状态 ======
state = {
    "year": "正德三年",
    "month": 1,
    "rank": "七品县令",
    "money": 50,
    "reputation": 15,
    "relation_emperor": 0,     # -10 到 10
    "relation_villain": 0,
}

# ====== NPC 角色 ======
NPC = {
    "emperor": {
        "name": "皇帝",
        "prompt": "你是明朝正德皇帝朱厚照，16岁登基。贪玩好动，不爱上朝，但人不坏。相信太监刘瑾。说话带点少年气，偶尔任性。用白话回复，每次 2-3 句话。",
    },
    "villain": {
        "name": "刘瑾",
        "prompt": "你是大太监刘瑾，权倾朝野。表面恭敬，内心阴狠。谁挡你的财路就除掉谁。说话阴阳怪气，话里藏刀。用白话回复，每次 2-3 句话。",
    },
    "mentor": {
        "name": "王守仁",
        "prompt": "你是王守仁（王阳明），心学大师，正在地方任职。正直但不迂腐，看人看事极准。说话温和有智慧，偶尔引用心学道理。用白话回复，每次 2-3 句话。",
    },
}
for npc in NPC.values():
    npc["messages"] = [{"role": "system", "content": npc["prompt"]}]

# ====== LLM 调用 ======
def ask_llm(messages, max_tokens=300):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

def npc_speak(name, msg):
    """NPC 说一句话"""
    npc = NPC[name]
    npc["messages"].append({"role": "user", "content": msg})
    reply = ask_llm(npc["messages"], max_tokens=150)
    npc["messages"].append({"role": "assistant", "content": reply})
    print(f"  👤 {npc['name']}: {reply}")

# ====== 主循环 ======
print("""
╔══════════════════════════════╗
║   🏯 大明模拟器              ║
║                              ║
║   你是七品县令，正德三年。   ║
║   朝中刘瑾当权，地方王守仁  ║
║   是你的同僚。               ║
║                              ║
║   你有一个目标——             ║
╚══════════════════════════════╝
""")

goal = input("你的毕生目标是？（如：入阁拜相 / 富甲一方 / 成为大儒）: ").strip()
print()

for turn in range(1, 6):
    print("=" * 50)
    print(f"📅 {state['year']} · 第 {state['month']} 个月")
    print(f"  官职: {state['rank']} | 银两: {state['money']} | 声望: {state['reputation']}")
    print(f"  皇帝态度: {state['relation_emperor']:+d} | 刘瑾态度: {state['relation_villain']:+d}")
    print()

    # 生成局势
    gm_prompt = f"""你是大明模拟器的导演。当前状态：
- 年份：{state['year']}第{state['month']}个月
- 玩家：{state['rank']}，银{state['money']}两，声望{state['reputation']}
- 皇帝态度{state['relation_emperor']:+d}，刘瑾态度{state['relation_villain']:+d}
- 玩家的毕生目标：{goal}

请生成一条简短的「本月要闻」（20字以内），描述朝堂上正在发生的一件大事。"""
    
    event = ask_llm([{"role": "user", "content": gm_prompt}], max_tokens=60)
    print(f"📨 本月要闻：{event}")
    print()

    # 生成 3 个选项
    choice_prompt = f"""局势：{event}
玩家是{state['rank']}，银{state['money']}两，声望{state['reputation']}，目标是{goal}。

请生成 3 个本月可选行动，每个一行，用简洁中文。格式：
1. xxx
2. xxx
3. xxx"""
    
    choices = ask_llm([{"role": "user", "content": choice_prompt}], max_tokens=120)
    print("🎯 你这个月要做什么？")
    for line in choices.strip().split("\n"):
        if line.strip():
            print(f"  {line.strip()}")
    print("  [4] 其他（自己写）")

    pick = input("选: ").strip()
    if pick == "4":
        action = input("你要做什么: ").strip()
    else:
        # Extract the text after the number
        for line in choices.strip().split("\n"):
            if line.strip().startswith(pick + "."):
                action = line.strip()[2:].strip()
                break
        else:
            action = "无所事事"

    print(f"\n▶ 你选择了：{action}\n")

    # NPC 反应
    print("📢 各方反应：")
    npc_speak("emperor", f"听说你{action}，朕想知道你怎么想的？")
    npc_speak("villain", f"你知道吗，有人跟咱家说你{action}。咱家很好奇啊。")
    npc_speak("mentor", f"我听说你{action}，想跟你聊聊此举的得失。")
    print()

    # 结算
    settle_prompt = f"""你是大明模拟器的结算系统。玩家本月行为：{action}。
当前：{state['rank']}，银{state['money']}两，声望{state['reputation']}。
皇帝态度{state['relation_emperor']:+d}，刘瑾态度{state['relation_villain']:+d}。
根据 NPC 的反应和玩家的行动，输出 JSON 格式的数值变化：
{{"money_change": 0, "rep_change": 0, "emperor_change": 0, "villain_change": 0, "summary": "一句话总结"}}
变化范围：-10 到 +10。"""
    
    import json
    result = ask_llm([{"role": "user", "content": settle_prompt}], max_tokens=150)
    try:
        # 提取 JSON
        start = result.find("{")
        end = result.rfind("}") + 1
        changes = json.loads(result[start:end])
        state["money"] += changes.get("money_change", 0)
        state["reputation"] += changes.get("rep_change", 0)
        state["relation_emperor"] += changes.get("emperor_change", 0)
        state["relation_villain"] += changes.get("villain_change", 0)
        print(f"📊 {changes.get('summary', '本月平平无奇。')}")
        print(f"   银两 {changes.get('money_change', 0):+d} | 声望 {changes.get('rep_change', 0):+d}")
        print(f"   皇帝态度 {changes.get('emperor_change', 0):+d} | 刘瑾态度 {changes.get('villain_change', 0):+d}")
    except:
        print("📊 本月平淡无奇，朝堂无事。")

    state["month"] += 1
    print()

# ====== 结局 ======
print("=" * 50)
print("🎬 五年之期已到")
print(f"  最终官职: {state['rank']}")
print(f"  银两: {state['money']} | 声望: {state['reputation']}")
print()

ending_prompt = f"""请根据以下结局数据，用明朝说书人的口吻写一段 150 字的人生总结：
玩家原本是{state['rank']}，目标是{goal}。
最终银{state['money']}两，声望{state['reputation']}。
皇帝态度{state['relation_emperor']:+d}，刘瑾态度{state['relation_villain']:+d}。"""

ending = ask_llm([{"role": "user", "content": ending_prompt}], max_tokens=250)
print(ending)
