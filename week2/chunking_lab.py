"""
Day 10: 切块策略对比
固定切块 / 重叠切块 / 语义切块 —— 3 种方式对比效果
依赖：pip install sentence-transformers modelscope
"""
from modelscope.hub.snapshot_download import snapshot_download
from sentence_transformers import SentenceTransformer
import numpy as np

print("加载模型中...")
model_dir = snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model = SentenceTransformer(model_dir)
print("模型加载完成\n")

# ====== 测试文章 ======

TEXT = """
人工智能的发展历程可以追溯到20世纪50年代。1956年，达特茅斯会议首次提出"人工智能"这一概念，
标志着这一领域的正式诞生。早期的AI研究主要集中在符号推理和专家系统上，试图用规则来模拟人类思维。

进入90年代，机器学习逐渐成为主流方向。与传统AI不同，机器学习让计算机从数据中自动学习规律，
而不是依赖人工编写的规则。支持向量机、决策树等算法在这一时期得到广泛应用。

2006年，深度学习迎来突破。Geoffrey Hinton提出了深度神经网络的训练方法，解决了多层网络难以
训练的问题。此后，卷积神经网络在图像识别领域取得突破性进展，循环神经网络则在语音和文本处理
方面展现出强大能力。

2017年，Transformer架构横空出世。论文《Attention is All You Need》提出了自注意力机制，
彻底改变了自然语言处理的格局。Transformer不依赖循环结构，可以并行计算，训练效率大幅提升。

2020年后，大语言模型时代到来。GPT-3、ChatGPT、GPT-4相继发布，参数规模从亿级增长到千亿级。
这些模型展现出惊人的语言理解和生成能力，能够写代码、做翻译、回答问题，几乎无所不能。

中国在AI领域也取得了重要进展。百度的文心一言、阿里的通义千问、DeepSeek等大模型相继推出，
在中文理解和生成方面表现出色。尤其是DeepSeek，以极低的训练成本达到了顶尖水平，引发全球关注。
""".strip()

# ====== 策略一：固定切块 ======

def fixed_chunking(text: str, chunk_size: int = 100) -> list[str]:
    """每隔 chunk_size 个字符切一刀，不管语义"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks

# ====== 策略二：重叠切块 ======

def overlap_chunking(text: str, chunk_size: int = 100, overlap: int = 30) -> list[str]:
    """每块之间保留 overlap 个字符的重叠，避免信息在边界被切断"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# ====== 策略三：语义切块 ======

def semantic_chunking(text: str, threshold: float = 0.3) -> list[str]:
    """
    按句子切分，计算相邻句子的相似度。
    相似度低于阈值说明话题切换了，在此处断开。
    """
    # 按句号/换行切成句子
    import re
    sentences = [s.strip() for s in re.split(r'[。\n]', text) if s.strip()]

    if len(sentences) <= 1:
        return sentences

    # 计算相邻句子的余弦相似度
    vecs = model.encode(sentences)

    def cosine_sim(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # 在相似度低的地方切块
    chunks = []
    current = sentences[0]

    for i in range(1, len(sentences)):
        sim = cosine_sim(vecs[i - 1], vecs[i])
        if sim < threshold:
            # 话题切换，断开
            chunks.append(current)
            current = sentences[i]
        else:
            # 话题连续，合并
            current += "。" + sentences[i]

    chunks.append(current)
    return chunks

# ====== 对比展示 ======

def show_chunks(name: str, chunks: list[str]):
    print(f"\n{'=' * 55}")
    print(f"【{name}】共 {len(chunks)} 块")
    print('=' * 55)
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  块 {i}（{len(chunk)} 字）：")
        print(f"  {chunk[:80]}{'...' if len(chunk) > 80 else ''}")

# ====== 搜索对比：同一个问题，3 种切法谁找得准 ======

def search_compare(query: str, chunks_dict: dict):
    print(f"\n{'=' * 55}")
    print(f"搜索：「{query}」")
    print('=' * 55)

    q_vec = model.encode(query)

    for name, chunks in chunks_dict.items():
        vecs = model.encode(chunks)
        scores = [(float(np.dot(q_vec, v) / (np.linalg.norm(q_vec) * np.linalg.norm(v))), c)
                  for v, c in zip(vecs, chunks)]
        scores.sort(reverse=True)
        best_score, best_chunk = scores[0]
        bar = "█" * int(best_score * 15)
        print(f"\n  {name}：[{bar:<15}] {best_score:.3f}")
        print(f"  最相关块：{best_chunk[:60]}{'...' if len(best_chunk) > 60 else ''}")

# ====== 主程序 ======

fixed   = fixed_chunking(TEXT, chunk_size=100)
overlap = overlap_chunking(TEXT, chunk_size=100, overlap=30)
semantic = semantic_chunking(TEXT, threshold=0.3)

show_chunks("固定切块（每100字）", fixed)
show_chunks("重叠切块（100字，重叠30字）", overlap)
show_chunks("语义切块（相似度<0.3处断开）", semantic)

print("\n\n" + "=" * 55)
print("搜索效果对比")
print("=" * 55)

chunks_dict = {
    "固定切块": fixed,
    "重叠切块": overlap,
    "语义切块": semantic,
}

search_compare("深度学习的突破是什么时候", chunks_dict)
search_compare("Transformer 的核心创新", chunks_dict)
search_compare("中国有哪些大模型", chunks_dict)

print("\n\n" + "=" * 55)
print("三种切法总结")
print("=" * 55)
print(f"""
  固定切块：最简单，{len(fixed)} 块，可能把一句话切断
  重叠切块：{len(overlap)} 块，边界处信息重复保留，不易遗漏
  语义切块：{len(semantic)} 块，按话题自然分段，块的大小不均匀但语义最完整
""")
