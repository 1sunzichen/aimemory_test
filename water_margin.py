"""
⚔️ 水浒 · 林冲传 — 开放式
你自己决定做什么。LLM 是裁判，判断结果。
可能随时死。
"""
import os, readline
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

def ask(messages, max_tokens=250):
    r = client.chat.completions.create(
        model="deepseek-chat", messages=messages, max_tokens=max_tokens,
    )
    return r.choices[0].message.content

# ====== NPC 定义 ======
NPC_DEFS = {
    "gaoqiu": "高俅。宋朝太尉，从市井爬到权倾朝野。恨林冲入骨。阴狠，笑里藏刀。",
    "luqian": "陆谦。林冲的发小，已背叛投靠高俅。心虚但铁了心做狗。",
    "lushen": "鲁智深。林冲的结拜兄弟。粗中有细，武艺高强，最讲义气。",
    "chao": "晁盖。托塔天王，义薄云天。劫生辰纲后被逼上梁山。欣赏林冲。",
    "wuyong": "吴用。智多星。城府极深，走一步看三步。",
}

# ====== 裁判 ======
master_prompt = """你是大明模拟器的裁判。玩家扮演林冲，在宋朝。
你负责：
1. 根据玩家的行动描述，判断结果（成功/失败/意外/死亡）
2. 描述场景变化
3. 控制 NPC 出场

规则：
- 玩家可能随时死——如果做出极度危险的举动，真的会死
- 死要死得有分量，让人扼腕
- NPC 各自有动机：高俅要林冲死，陆谦心虚，鲁智深忠诚，晁盖想拉拢，吴用在算计
- 每次回复控制在 3-5 句话。不必每次都出选项——描述场景后自然停顿，等玩家自己决定
- 保持水浒传的语言风格——半文半白，有江湖气

当前叙事阶段：风雪山神庙 → 被逼上梁山。"""

master_msg = [{"role": "system", "content": master_prompt}]

# 游戏日志（喂给裁判当记忆）
game_log = []

def log(line):
    game_log.append(line)
    # 只保留最近 30 条，避免上下文溢出
    if len(game_log) > 30:
        del game_log[0]

# ====== 工具函数 ======
def npc_reply(npc_key, situation):
    """让某个 NPC 对当前局势发表看法"""
    prompt = f"你是{NPC_DEFS[npc_key]}\n当前局势：{situation}\n用 2-3 句话发表你的看法或行动。用白话，有人物性格。"
    reply = ask([{"role":"system","content":prompt}], 150)
    name = NPC_DEFS[npc_key].split("。")[0]
    return f"👤 {name}：{reply}"

def scene(description, npcs_to_react=None):
    """输出场景描述，并让指定 NPC 回应"""
    print(f"\n{description}")
    log(description)
    if npcs_to_react:
        for n in npcs_to_react:
            r = npc_reply(n, description)
            print(r)
            log(r)
    print()

# ====== 开场 ======
print("""
╔══════════════════════════════════════════╗
║                                          ║
║      ⚔️  水 浒 · 林 冲 传               ║
║      🔥  风 雪 山 神 庙                  ║
║                                          ║
║   你说什么，AI 判什么。没有固定选项。    ║
║   每一步都可能改变命运。包括死。          ║
║                                          ║
║   输入 /help 看提示    /quit 退出         ║
╚══════════════════════════════════════════╝
""")

print("你是林冲，八十万禁军教头。")
print("妻子被调戏，你忍了。高俅陷害你，刺配沧州。")
print("此刻大雪纷飞，草料场被人放火烧了。")
print("你躲在山神庙里。庙外，有人在说话——")
print()

# 陆谦先开口
lu = npc_reply("luqian", "你和两个差拨刚烧了草料场，站在山神庙外。你们以为林冲还在里面被烧死了。你正在得意地说话。")
print(f"{lu}\n")
log(lu)

print("⚡ 你的枪就在手边。要做什么，自己决定。")
print()

# ====== 主循环 ======
turn = 0
death = False

while turn < 12 and not death:
    action = input("🗡️ 林冲: ").strip()
    if not action:
        continue
    if action == "/quit":
        print("游戏结束。")
        break
    if action == "/help":
        print("\n你可以输入任何行动，比如：")
        print("  提枪冲出去杀了陆谦")
        print("  继续躲在庙里听他们说什么")
        print("  等他们走了之后下山找鲁智深")
        print("  一把火烧了旁边的树林吸引注意")
        print("\n你可以跟 NPC 对话：")
        print("  对陆谦说：你这条狗，对得起我吗")
        print("  大喊：救命啊！草料场走水了！")
        print()
        continue

    log(f"林冲: {action}")
    turn += 1

    # 构建裁判上下文
    context = "游戏日志（最近事件）：\n" + "\n".join(game_log[-20:])
    judge_prompt = f"""{context}

玩家刚才的行动：{action}

请作为裁判，判断这个行动的结果。用一段话描述接下来发生了什么。
- 如果行动合理，描述结果
- 如果行动极度危险（比如正面挑战一支军队），让结果符合逻辑——可能受伤、被抓、甚至死
- 死要死得有分量
- 如果这个行动触发了某个 NPC 的反应，让那个 NPC 自然出场
- 3-5 句话。不要加选项，让玩家自己决定下一步。"""

    result = ask(master_msg + [{"role":"user","content": judge_prompt}], 300)
    print(f"\n{result}")
    log(result)

    # 检测死亡
    if any(w in result for w in ["你死了", "你倒下了", "闭上了眼睛", "最后一口气", "砍下了你的", "刺穿了你的"]):
        death = True
        print("\n💀 林冲，死于非命。")
        print()

if death:
    summary = ask(master_msg + [
        {"role":"user","content": f"林冲刚才死了。用 150 字，以水浒传说书人的口吻总结他的一生。要有诗意，让人感慨。"}
    ], 300)
    print(f"📖 {summary}")
else:
    summary = ask(master_msg + [
        {"role":"user","content": f"""游戏结束了。这是林冲的故事日志：\n{chr(10).join(game_log[-20:])}
用 200 字，以水浒传说书人的口吻给林冲写一段人生总结。有「话说」「正是」「后世有诗赞曰」等风格。要有悲壮感。"""}
    ], 400)
    print("=" * 50)
    print(f"📖 {summary}")
