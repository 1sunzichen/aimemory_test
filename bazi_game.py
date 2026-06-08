"""
🔮 八字命格 · 穿越中国五千年
输入生辰 → 精算八字 → 五行格局分析 → 有理有据匹配历史人物 → 沉浸剧情
"""
import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 天干地支 & 五行 ======

TIANGAN  = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DIZHI    = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
SHENGXIAO= ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]

# 天干五行
GAN_WUXING = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水"
}
# 地支五行
ZHI_WUXING = {
    "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
    "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"
}
# 天干阴阳
GAN_YINYANG = {
    "甲":"阳","乙":"阴","丙":"阳","丁":"阴","戊":"阳",
    "己":"阴","庚":"阳","辛":"阴","壬":"阳","癸":"阴"
}

# ====== 精确计算：儒略日 → 日柱 ======

def julian_day(year: int, month: int, day: int) -> int:
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + A // 4
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524

def day_pillar(year: int, month: int, day: int) -> tuple:
    """
    基准：1900年1月1日 = 甲戌日
    JDN(1900-01-01) = 2415021，甲=0，戌=10
    """
    jdn = julian_day(year, month, day)
    offset = (jdn - 2415021) % 60
    stem_idx   = (0 + offset) % 10   # 甲起
    branch_idx = (10 + offset) % 12  # 戌起
    return stem_idx, branch_idx

# ====== 月柱：年干决定月干起点 ======

MONTH_STEM_BASE = {
    "甲": 2, "己": 2,  # 丙寅起
    "乙": 4, "庚": 4,  # 戊寅起
    "丙": 6, "辛": 6,  # 庚寅起
    "丁": 8, "壬": 8,  # 壬寅起
    "戊": 0, "癸": 0,  # 甲寅起
}
# 公历月份对应的月支（节气近似，以公历月份代替）
MONTH_ZHI_BY_SOLAR = [11,0,1,2,3,4,5,6,7,8,9,10]  # 1月=丑(1), 2月=寅(2)...

def month_pillar(year_gan: str, month: int) -> tuple:
    zhi_idx  = MONTH_ZHI_BY_SOLAR[month - 1]
    # 月支从寅(index=2)开始为正月，寅=2在DIZHI里
    # month=2(二月)对应寅，月支序号从寅算起
    month_order = (zhi_idx - 2) % 12  # 距寅的偏移
    stem_base = MONTH_STEM_BASE[year_gan]
    stem_idx  = (stem_base + month_order) % 10
    return stem_idx, zhi_idx

# ====== 时柱：日干决定时干起点 ======

HOUR_STEM_BASE = {
    "甲": 0, "己": 0,  # 甲子时起
    "乙": 2, "庚": 2,  # 丙子时起
    "丙": 4, "辛": 4,  # 戊子时起
    "丁": 6, "壬": 6,  # 庚子时起
    "戊": 8, "癸": 8,  # 壬子时起
}

def hour_pillar(day_gan: str, hour: int) -> tuple:
    # 时支：子时=23-1时，丑时=1-3时...
    if hour == 23:
        zhi_idx = 0
    else:
        zhi_idx = ((hour + 1) // 2) % 12
    stem_base = HOUR_STEM_BASE[day_gan]
    stem_idx  = (stem_base + zhi_idx) % 10
    return stem_idx, zhi_idx

# ====== 四柱计算 ======

def calc_bazi(year: int, month: int, day: int, hour: int) -> dict:
    # 年柱
    y_stem_idx   = (year - 4) % 10
    y_branch_idx = (year - 4) % 12
    y_gan = TIANGAN[y_stem_idx]
    y_zhi = DIZHI[y_branch_idx]

    # 月柱
    m_stem_idx, m_branch_idx = month_pillar(y_gan, month)
    m_gan = TIANGAN[m_stem_idx]
    m_zhi = DIZHI[m_branch_idx]

    # 日柱（精确）
    d_stem_idx, d_branch_idx = day_pillar(year, month, day)
    d_gan = TIANGAN[d_stem_idx]
    d_zhi = DIZHI[d_branch_idx]

    # 时柱
    h_stem_idx, h_branch_idx = hour_pillar(d_gan, hour)
    h_gan = TIANGAN[h_stem_idx]
    h_zhi = DIZHI[h_branch_idx]

    shengxiao = SHENGXIAO[(year - 4) % 12]

    # 五行统计（8个字各贡献一个五行）
    all_chars = [y_gan, y_zhi, m_gan, m_zhi, d_gan, d_zhi, h_gan, h_zhi]
    wuxing_count = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for c in all_chars:
        wx = GAN_WUXING.get(c) or ZHI_WUXING.get(c)
        if wx:
            wuxing_count[wx] += 1

    return {
        "年柱": {"干": y_gan, "支": y_zhi, "柱": f"{y_gan}{y_zhi}"},
        "月柱": {"干": m_gan, "支": m_zhi, "柱": f"{m_gan}{m_zhi}"},
        "日柱": {"干": d_gan, "支": d_zhi, "柱": f"{d_gan}{d_zhi}"},
        "时柱": {"干": h_gan, "支": h_zhi, "柱": f"{h_gan}{h_zhi}"},
        "日主": d_gan,
        "日主五行": GAN_WUXING[d_gan],
        "日主阴阳": GAN_YINYANG[d_gan],
        "生肖": shengxiao,
        "五行统计": wuxing_count,
        "全字": f"{y_gan}{y_zhi} {m_gan}{m_zhi} {d_gan}{d_zhi} {h_gan}{h_zhi}",
    }

def wuxing_summary(count: dict) -> str:
    return " ".join(f"{k}{v}个" for k, v in count.items())

# ====== LLM 调用 ======

def ask_llm(prompt: str, max_tokens: int = 600) -> str:
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

def ask_json(prompt: str, max_tokens: int = 800) -> dict:
    raw = ask_llm(prompt, max_tokens)
    try:
        s = raw.find("{")
        e = raw.rfind("}") + 1
        return json.loads(raw[s:e])
    except:
        return {}

# ====== 主程序 ======

print("""
╔══════════════════════════════════════════╗
║   🔮 八字命格 · 穿越中国五千年          ║
║                                          ║
║   输入生辰 → 精算八字 → 推断命格        ║
║   有理有据 → 匹配历史人物 → 穿越体验    ║
╚══════════════════════════════════════════╝
""")

print("请输入你的生辰（公历）：")
try:
    year  = int(input("  出生年份（如 1998）：").strip())
    month = int(input("  出生月份（1-12）：").strip())
    day   = int(input("  出生日期（1-31）：").strip())
    hour  = int(input("  出生时辰（0-23整点，不知道填12）：").strip())
except ValueError:
    print("输入有误，使用示例：1998年6月18日 午时")
    year, month, day, hour = 1998, 6, 18, 12

bazi = calc_bazi(year, month, day, hour)
wx   = bazi["五行统计"]

print(f"""
╔══════════════════════════════════════════╗
║  八字：{bazi['全字']:<34}║
║  生肖：{bazi['生肖']}                                    ║
║  日主：{bazi['日主']}（{bazi['日主阴阳']}{bazi['日主五行']}）                          ║
║  五行：{wuxing_summary(wx):<32}║
╚══════════════════════════════════════════╝
""")

# ====== 第一步：AI 深度推算命格 ======

print("🔮 正在推算命格，请稍候...\n")

profile_prompt = f"""你是中国顶级命理学家，精通八字命理。请对以下八字做严谨推算：

【八字】{bazi['全字']}
【四柱详情】
  年柱：{bazi['年柱']['柱']}（{GAN_WUXING[bazi['年柱']['干']]}·{ZHI_WUXING[bazi['年柱']['支']]}）
  月柱：{bazi['月柱']['柱']}（{GAN_WUXING[bazi['月柱']['干']]}·{ZHI_WUXING[bazi['月柱']['支']]}）
  日柱：{bazi['日柱']['柱']}（日主：{bazi['日主']}，{bazi['日主阴阳']}{bazi['日主五行']}）
  时柱：{bazi['时柱']['柱']}（{GAN_WUXING[bazi['时柱']['干']]}·{ZHI_WUXING[bazi['时柱']['支']]}）
【五行统计】{wuxing_summary(wx)}
【生肖】{bazi['生肖']}

请按以下逻辑推理，输出 JSON：
{{
  "日主旺衰": "日主{bazi['日主']}属{bazi['日主五行']}，分析八字中{bazi['日主五行']}的势力强弱，判断日主是旺还是弱（30字内）",
  "用神": "根据日主旺衰，需要哪种五行来平衡（10字内）",
  "格局": "这八字属于什么格局（如：正官格、伤官格、食神格、七杀格、印绶格等，20字内）",
  "性格": "根据日主、格局、五行，推导出3-5个核心性格特质，必须引用具体的干支来佐证",
  "命格特征": "一句话概括此人命格（25字内）",
  "历史人物": "在整个中国历史（先秦到清末）中，找一位与此八字格局最相似的真实历史人物，只写名字",
  "人物朝代": "该历史人物所在朝代",
  "匹配依据": "从日主五行、格局、用神三个角度，说明为何此人命格与该历史人物相合（80字内，要有理有据）",
  "历史时刻": "选取该历史人物一生中最关键的一个决策时刻（20字描述场景）"
}}
"""

profile = ask_json(profile_prompt, max_tokens=1000)

if not profile:
    print("推算失败，请重试。")
    exit()

hero     = profile.get("历史人物", "张良")
dynasty  = profile.get("人物朝代", "汉代")
moment   = profile.get("历史时刻", "鸿门宴前夕，刘邦命悬一线")

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📜 命格推算报告

  【日主旺衰】{profile.get('日主旺衰', '')}
  【用    神】{profile.get('用神', '')}
  【格    局】{profile.get('格局', '')}
  【性格特质】{profile.get('性格', '')}
  【命格总结】{profile.get('命格特征', '')}

  ✨ 命中注定对应历史人物：【{hero}】·{dynasty}

  【匹配依据】
  {profile.get('匹配依据', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

input(f"按回车键，穿越成为【{dynasty}·{hero}】，直面你的命运时刻...")

# ====== 第二步：生成沉浸式场景 ======

print(f"\n🌀 时空穿越中...\n")

scene_prompt = f"""你是历史剧作家，为玩家创造沉浸式穿越体验。

玩家穿越成了【{dynasty}·{hero}】。
此人命格：{profile.get('命格特征', '')}
性格特质：{profile.get('性格', '')}
关键时刻：{moment}

请生成这一历史关键时刻的完整场景和选择，输出 JSON：
{{
  "场景描述": "用第一人称描写当前场景，必须有历史细节（时间/地点/在场人物），120字以内，有画面感和压迫感",
  "核心矛盾": "这一刻你必须面对的核心抉择是什么（20字内）",
  "选项A": "符合此人命格和性格的选择（15字内）",
  "选项A结果预示": "这个选择历史上会带来什么走向（20字内）",
  "选项B": "反其道而行之的选择（15字内）",
  "选项B结果预示": "这个选择会带来什么变数（20字内）",
  "选项C": "出乎所有人意料的第三条路（15字内）",
  "选项C结果预示": "这个选择带来的意外可能（20字内）"
}}
"""

scene = ask_json(scene_prompt, max_tokens=800)

if not scene:
    scene = {
        "场景描述": "你是" + hero + "，站在命运的十字路口。",
        "核心矛盾": "进退之间，如何抉择",
        "选项A": "按原本历史走",
        "选项A结果预示": "历史的轨迹延续",
        "选项B": "反其道而行",
        "选项B结果预示": "历史出现裂缝",
        "选项C": "走第三条路",
        "选项C结果预示": "未知的可能性"
    }

print(f"【{dynasty} · {hero}】\n")
print(f"{scene.get('场景描述', '')}\n")
print(f"⚔️  {scene.get('核心矛盾', '')}\n")
print("你的选择：")
print(f"  A. {scene.get('选项A', '')}  →  {scene.get('选项A结果预示', '')}")
print(f"  B. {scene.get('选项B', '')}  →  {scene.get('选项B结果预示', '')}")
print(f"  C. {scene.get('选项C', '')}  →  {scene.get('选项C结果预示', '')}")
print(f"  D. 我有自己的想法")

pick = input("\n你的选择（A/B/C/D）：").strip().upper()
if pick == "D":
    action = input("你要怎么做：").strip()
elif pick == "A":
    action = scene.get("选项A", "")
elif pick == "B":
    action = scene.get("选项B", "")
elif pick == "C":
    action = scene.get("选项C", "")
else:
    action = scene.get("选项A", "")

# ====== 第三步：AI 生成结局 ======

print(f"\n▶ 你选择了：{action}\n")
print("⏳ 历史正在改写...\n")

ending_prompt = f"""你是历史说书人，用古典叙事风格写一段穿越结局。

主角：{dynasty}·{hero}
命格：{profile.get('命格特征', '')}
关键场景：{scene.get('场景描述', '')}
玩家选择：{action}

要求：
1. 先写这个选择带来的直接后果（50字）
2. 再写这个选择对历史的影响（50字）
3. 最后一段：把玩家的八字（{bazi['全字']}）和{hero}的命格联系起来，
   说明为何拥有这样命格的人，会在此刻做出这样的选择（50字）
4. 结尾一句：「欲知后事如何，且听下回分解。」

风格：古典白话，有张力，不超过200字。
"""

ending = ask_llm(ending_prompt, max_tokens=400)
print(ending)

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  你的八字：{bazi['全字']}
  格    局：{profile.get('格局', '')}
  命定人物：{dynasty} · {hero}

  换个出生时辰，你将穿越到不同的历史。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
