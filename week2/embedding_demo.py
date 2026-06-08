"""
Embedding Demo
把句子变向量，比相似度——语义搜索 / 相似矩阵 / 找异类
依赖：pip install sentence-transformers modelscope
"""
from modelscope.hub.snapshot_download import snapshot_download
from sentence_transformers import SentenceTransformer
import numpy as np

# 从 ModelScope（阿里云）下载，国内速度快，首次运行自动下载（~120MB）
model_dir = snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model = SentenceTransformer(model_dir)

# ====== 工具函数 ======

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def similarity_matrix(sentences: list[str]) -> np.ndarray:
    vecs = model.encode(sentences)
    n = len(vecs)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mat[i][j] = cosine_similarity(vecs[i], vecs[j])
    return mat

def print_heatmap(sentences: list[str], mat: np.ndarray):
    """ASCII 热力图"""
    labels = [s[:8] for s in sentences]
    col_w = 10
    header = " " * 10 + "".join(f"{l:>{col_w}}" for l in labels)
    print(header)
    for i, row_label in enumerate(labels):
        row = f"{row_label:>10}"
        for j in range(len(labels)):
            score = mat[i][j]
            if i == j:
                cell = "  ████"
            elif score >= 0.85:
                cell = f"  ▓▓▓▓"
            elif score >= 0.65:
                cell = f"  ▒▒▒▒"
            elif score >= 0.45:
                cell = f"  ░░░░"
            else:
                cell = f"  ····"
            row += f"{cell:>{col_w}}"
        print(row + f"   {labels[i]}")
    print()
    print("图例: ████=自身  ▓▓▓▓≥0.85  ▒▒▒▒≥0.65  ░░░░≥0.45  ····<0.45")

# ====== Demo 1：两句话的相似度 ======

def demo_basic():
    print("\n" + "=" * 50)
    print("Demo 1：两句话的相似度")
    print("=" * 50)

    pairs = [
        ("今天天气真好", "阳光明媚，适合出门"),
        ("今天天气真好", "股市今天大涨"),
        ("我喜欢吃苹果", "I love eating apples"),
        ("机器学习很有趣", "深度学习改变了AI领域"),
        ("这部电影太无聊了", "这部电影非常精彩"),
    ]

    for a, b in pairs:
        va, vb = model.encode([a, b])
        score = cosine_similarity(va, vb)
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"\n  句A：{a}")
        print(f"  句B：{b}")
        print(f"  相似度：[{bar}] {score:.3f}")

# ====== Demo 2：语义搜索 ======

def demo_search():
    print("\n" + "=" * 50)
    print("Demo 2：语义搜索（在知识库里找最相关的句子）")
    print("=" * 50)

    knowledge_base = [
        "Python 是一种简单易学的编程语言",
        "深度学习需要大量的训练数据",
        "北京是中国的首都，有很多历史景点",
        "苹果公司发布了新款 iPhone 手机",
        "机器学习是人工智能的一个子领域",
        "今天的天气非常适合爬山",
        "神经网络由多层节点组成",
        "上海是中国最大的经济中心",
        "自然语言处理让计算机理解人类语言",
        "故宫是明清两代的皇家宫殿",
    ]

    queries = [
        "AI 和神经网络是什么关系？",
        "中国有哪些著名城市？",
        "编程语言哪个好学？",
    ]

    kb_vecs = model.encode(knowledge_base)

    for query in queries:
        q_vec = model.encode(query)
        scores = [(cosine_similarity(q_vec, kv), kb) for kv, kb in zip(kb_vecs, knowledge_base)]
        scores.sort(reverse=True)

        print(f"\n  查询：「{query}」")
        print("  最相关的 3 条：")
        for rank, (score, text) in enumerate(scores[:3], 1):
            bar = "█" * int(score * 15)
            print(f"    {rank}. [{bar:<15}] {score:.3f}  {text}")

# ====== Demo 3：相似度热力图 ======

def demo_heatmap():
    print("\n" + "=" * 50)
    print("Demo 3：句子相似度热力图")
    print("=" * 50)

    sentences = [
        "我爱北京天安门",
        "北京是中国首都",
        "上海是金融中心",
        "深度学习很强大",
        "神经网络效果好",
        "今天吃了火锅",
        "晚饭吃了麻辣烫",
    ]

    print("\n  句子列表：")
    for i, s in enumerate(sentences):
        print(f"    {i+1}. {s}")
    print()

    mat = similarity_matrix(sentences)
    print_heatmap(sentences, mat)

# ====== Demo 4：找异类 ======

def demo_odd_one_out():
    print("\n" + "=" * 50)
    print("Demo 4：找出「格格不入」的句子")
    print("=" * 50)

    groups = [
        [
            "猫是可爱的动物",
            "狗喜欢追球玩",
            "兔子耳朵很长",
            "比特币今天暴涨了",
            "鹦鹉会学人说话",
        ],
        [
            "梯度下降用于优化模型",
            "反向传播计算梯度",
            "今天中午吃了炒饭",
            "Transformer 是注意力机制",
            "损失函数衡量预测误差",
        ],
    ]

    for group in groups:
        vecs = model.encode(group)
        # 每个句子的"平均相似度"（越低越异类）
        scores = []
        for i, v in enumerate(vecs):
            others = [vecs[j] for j in range(len(vecs)) if j != i]
            avg = np.mean([cosine_similarity(v, o) for o in others])
            scores.append((avg, group[i]))

        scores.sort()
        print("\n  句子组：")
        for s in group:
            print(f"    · {s}")
        odd = scores[0][1]
        print(f"\n  → 异类：「{odd}」（与其他句子平均相似度最低：{scores[0][0]:.3f}）")

# ====== Demo 5：向量本身长什么样 ======

def demo_vector_peek():
    print("\n" + "=" * 50)
    print("Demo 5：向量长什么样？")
    print("=" * 50)

    sentence = "机器学习改变了世界"
    vec = model.encode(sentence)
    print(f"\n  句子：「{sentence}」")
    print(f"  向量维度：{vec.shape[0]}")
    print(f"  前 10 个值：{np.round(vec[:10], 4).tolist()}")
    print(f"  向量模长：{np.linalg.norm(vec):.4f}")
    print(f"  值域：[{vec.min():.4f}, {vec.max():.4f}]")

    print("\n  同一语义，不同表达的向量距离：")
    pairs = [
        ("机器学习改变了世界", "ML has changed the world"),
        ("机器学习改变了世界", "今天股市下跌"),
    ]
    for a, b in pairs:
        va, vb = model.encode([a, b])
        sim = cosine_similarity(va, vb)
        dist = np.linalg.norm(va - vb)
        print(f"    「{a[:10]}」vs「{b[:10]}」  余弦相似度={sim:.3f}  欧氏距离={dist:.3f}")

# ====== 主程序 ======

if __name__ == "__main__":
    print("正在加载模型（首次运行需下载）...")
    # 预热，触发模型加载
    model.encode("warmup")
    print("模型加载完成！\n")

    demo_vector_peek()
    demo_basic()
    demo_heatmap()
    demo_search()
    demo_odd_one_out()

    print("\n" + "=" * 50)
    print("全部演示完成！")
