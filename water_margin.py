"""
⚔️ 水浒 · 林冲传 — 开放式
你自己决定做什么。LLM 是裁判，判断结果。
结局由 AI 根据剧情走向合理生成。
"""
import os, json, readline
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

def ask(messages, max_tokens=300):
    r = client.chat.completions.create(
        model="deepseek-chat", messages=messages, max_tokens=max_tokens,
    )
    return r.choices[0].message.content.strip()

# ====== NPC 定义 ======
NPC_DEFS = {
    "gaoqiu": "高俅。宋朝太尉，从市井爬到权倾朝野。恨林冲入骨。阴狠，笑里藏刀。",
    "luqian": "陆谦。林冲的发小，已背叛投靠高俅。心虚但铁了心做狗。",
    "lushen": "鲁智深。林冲的结拜兄弟。粗中有细，武艺高强，最讲义气。",
    "chao":   "晁盖。托塔天王，义薄云天。劫生辰纲后被逼上梁山。欣赏林冲。",
    "wuyong": "吴用。智多星。城府极深，走一步看三步。",
}

# ====== 裁判 system prompt ======
MASTER_PROMPT = """你是水浒传模拟器的裁判。玩家扮演林冲，在宋朝。
你负责：
1. 根据玩家的行动描述判断结果（成功/失败/意外/死亡）
2. 描述场景变化
3. 控制 NPC 出场

规则：
- 玩家可能随时死——如果做出极度危险的举动，真的会死
- 死要死得有分量，让人扼腕
- NPC 各自有动机：高俅要林冲死，陆谦心虚，鲁智深忠诚，晁盖想拉拢，吴用在算计
- 每次回复控制在 3-5 句话。不必每次都出选项——描述场景后自然停顿，等玩家自己决定
- 保持水浒传的语言风格——半文半白，有江湖气

当前叙事阶段：风雪山神庙 → 被逼上梁山。"""

master_msg = [{"role": "system", "content": MASTER_PROMPT}]

# 游戏日志
game_log = []

def log(line):
    game_log.append(line)
    if len(game_log) > 40:
        del game_log[0]

def npc_reply(npc_key, situation):
    prompt = (f"你是{NPC_DEFS[npc_key]}\n"
              f"当前局势：{situation}\n"
              f"用 2-3 句话发表你的看法或行动。用白话，有人物性格。")
    reply = ask([{"role": "system", "content": prompt}], 150)
    name = NPC_DEFS[npc_key].split("。")[0]
    return f"👤 {name}：{reply}"

# ====== 结局判断 ======
ENDING_TYPES = {
    "death":     "林冲死亡",
    "liangshan": "林冲上了梁山，落草为寇",
    "escape":    "林冲逃出生天，流亡江湖",
    "revenge":   "林冲手刃仇人，完成复仇",
    "captured":  "林冲被官兵擒获",
    "surrender": "林冲选择归顺朝廷",
    "exile":     "林冲被发配远方，命运未卜",
    "none":      "故事尚未结束",
}

def check_ending(result_text):
    """让裁判判断当前结果是否触发结局，返回结局类型或 none"""
    log_snippet = "\n".join(game_log[-15:])
    prompt = f"""以下是当前水浒传模拟器的游戏日志和最新结果：

{log_snippet}

最新结果：{result_text}

请判断：这个结果是否已经构成一个自然的故事结局？
可选结局类型：{json.dumps(ENDING_TYPES, ensure_ascii=False)}

只返回一个 JSON，格式如下，不要其他内容：
{{"ending": "类型key", "reason": "一句话说明原因"}}

如果故事还在继续，返回 {{"ending": "none", "reason": "..."}}"""

    raw = ask([{"role": "user", "content": prompt}], 100)
    try:
        # 提取 JSON（防止模型多输出文字）
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"ending": "none", "reason": "解析失败"}

def generate_ending(ending_type):
    """根据结局类型和完整游戏日志，生成有分量的结局文本"""
    log_full = "\n".join(game_log)
    type_desc = ENDING_TYPES.get(ending_type, "未知结局")

    style_hints = {
        "death":     "要有悲壮感，让人扼腕。",
        "liangshan": "要有壮烈的江湖气，落草不是失败，是新生。",
        "escape":    "流亡的无奈与一丝生机并存。",
        "revenge":   "快意恩仇，但复仇之后空洞或解脱。",
        "captured":  "悲凉，命运弄人。",
        "surrender": "屈辱或无奈，有复杂的内心。",
        "exile":     "漫漫流放路，前途未卜。",
    }
    hint = style_hints.get(ending_type, "")

    prompt = f"""以下是林冲这段故事的完整经过：
{log_full}

结局类型：{type_desc}

请以水浒传说书人的口吻，写一段 200-300 字的结局。
要求：
- 开头用"话说"或"正是"
- 结尾用一首四句诗点题（"有诗为证"）
- 风格半文半白，有江湖气
- 内容要呼应玩家实际经历的剧情，不要泛泛而谈
- {hint}"""

    return ask([{"role": "user", "content": prompt}], 500)

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

lu = npc_reply("luqian", "你和两个差拨刚烧了草料场，站在山神庙外。你们以为林冲还在里面被烧死了。你正在得意地说话。")
print(f"{lu}\n")
log(lu)

print("⚡ 你的枪就在手边。要做什么，自己决定。")
print()

# ====== 主循环 ======
turn = 0
ending_reached = None

while turn < 15 and ending_reached is None:
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

    context = "游戏日志（最近事件）：\n" + "\n".join(game_log[-20:])
    judge_prompt = f"""{context}

玩家刚才的行动：{action}

请作为裁判，判断这个行动的结果。用一段话描述接下来发生了什么。
- 如果行动合理，描述结果
- 如果行动极度危险（比如正面挑战一支军队），让结果符合逻辑——可能受伤、被抓、甚至死
- 死要死得有分量
- 如果这个行动触发了某个 NPC 的反应，让那个 NPC 自然出场
- 3-5 句话。不要加选项，让玩家自己决定下一步。"""

    result = ask(master_msg + [{"role": "user", "content": judge_prompt}], 300)
    print(f"\n{result}\n")
    log(result)

    # 判断是否触发结局
    ending_info = check_ending(result)
    if ending_info["ending"] != "none":
        ending_reached = ending_info["ending"]

# ====== 结局生成 ======
if ending_reached:
    print("\n" + "=" * 50)
    ending_text = generate_ending(ending_reached)
    print(f"\n📖 {ending_text}\n")
elif turn >= 15:
    # 回合用完，强制结局
    print("\n" + "=" * 50)
    ending_text = generate_ending("escape")
    print(f"\n📖 {ending_text}\n")
