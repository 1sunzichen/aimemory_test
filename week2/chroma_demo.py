"""
Chroma 向量数据库 Demo
存入 20 篇文档，语义搜索
依赖：pip install chromadb sentence-transformers modelscope
"""
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from modelscope.hub.snapshot_download import snapshot_download
from sentence_transformers import SentenceTransformer

# ====== 加载模型（从 ModelScope 下载，国内可用）======

print("加载模型中...")
model_dir = snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model = SentenceTransformer(model_dir)
print("模型加载完成\n")

# ====== 自定义 Embedding 函数（接入 Chroma）======

class LocalEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return model.encode(input).tolist()

# ====== 20 篇文档 ======

DOCS = [
    # 科技
    {"id": "1",  "text": "Python 是最流行的编程语言之一，广泛用于人工智能和数据分析。",       "category": "科技"},
    {"id": "2",  "text": "深度学习通过多层神经网络自动提取数据特征，效果远超传统方法。",       "category": "科技"},
    {"id": "3",  "text": "Transformer 架构引入注意力机制，彻底改变了自然语言处理领域。",      "category": "科技"},
    {"id": "4",  "text": "向量数据库专门存储和检索高维向量，是 RAG 系统的核心组件。",         "category": "科技"},
    {"id": "5",  "text": "大语言模型通过海量文本预训练，能够理解和生成自然语言。",             "category": "科技"},
    # 历史
    {"id": "6",  "text": "秦始皇统一六国，建立了中国历史上第一个中央集权封建王朝。",          "category": "历史"},
    {"id": "7",  "text": "丝绸之路连接了中国与中亚、欧洲，促进了贸易和文化交流。",            "category": "历史"},
    {"id": "8",  "text": "唐朝是中国历史上最繁荣的朝代之一，文化艺术达到顶峰。",              "category": "历史"},
    {"id": "9",  "text": "郑和七下西洋，最远到达非洲东海岸，展示了明朝的航海实力。",          "category": "历史"},
    {"id": "10", "text": "故宫是明清两代的皇家宫殿，现为世界上保存最完整的古建筑群之一。",    "category": "历史"},
    # 健康
    {"id": "11", "text": "每天坚持30分钟有氧运动，可以显著降低心血管疾病风险。",              "category": "健康"},
    {"id": "12", "text": "充足的睡眠对大脑记忆巩固和免疫系统修复至关重要。",                  "category": "健康"},
    {"id": "13", "text": "地中海饮食富含橄榄油、蔬菜和鱼类，被认为是最健康的饮食方式之一。", "category": "健康"},
    {"id": "14", "text": "长期久坐会导致腰椎损伤，建议每隔一小时起身活动几分钟。",            "category": "健康"},
    {"id": "15", "text": "冥想和正念练习可以有效缓解焦虑，改善心理健康状态。",                "category": "健康"},
    # 经济
    {"id": "16", "text": "通货膨胀是指货币购买力下降，商品和服务价格持续上涨的现象。",        "category": "经济"},
    {"id": "17", "text": "股票市场的短期波动难以预测，长期持有指数基金是常见的投资策略。",    "category": "经济"},
    {"id": "18", "text": "区块链技术通过去中心化账本保证数据不可篡改，比特币是其典型应用。", "category": "经济"},
    {"id": "19", "text": "全球化使各国经济深度互联，一国的金融危机可能迅速蔓延至全球。",     "category": "经济"},
    {"id": "20", "text": "碳交易市场通过给碳排放定价，用市场机制推动企业减少温室气体排放。","category": "经济"},
]

# ====== 初始化 Chroma ======

client = chromadb.Client()
collection = client.create_collection(
    name="docs",
    embedding_function=LocalEmbeddingFunction(),
    metadata={"hnsw:space": "cosine"},  # 用余弦距离，结果更准
)

# 批量存入
collection.add(
    ids=[d["id"] for d in DOCS],
    documents=[d["text"] for d in DOCS],
    metadatas=[{"category": d["category"]} for d in DOCS],
)
print(f"已存入 {collection.count()} 篇文档\n")

# ====== 语义搜索 ======

def search(query: str, n: int = 3, category: str = None):
    where = {"category": category} if category else None
    results = collection.query(
        query_texts=[query],
        n_results=n,
        where=where,
    )
    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    print(f"查询：「{query}」" + (f"  [筛选分类: {category}]" if category else ""))
    print("-" * 55)
    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas), 1):
        similarity = 1 - dist  # 余弦距离：0=完全相同，2=完全相反，转成相似度范围 -1~1
        bar = "█" * int(similarity * 20)
        print(f"  {i}. [{bar:<20}] {similarity:.3f}  [{meta['category']}]")
        print(f"     {doc}")
    print()

# ====== 演示 ======

print("=" * 55)
print("Demo 1：跨类别语义搜索")
print("=" * 55 + "\n")
search("注意力机制")
search("古代中国的对外交流")
search("如何保持身体健康")

print("=" * 55)
print("Demo 2：限定分类搜索")
print("=" * 55 + "\n")
search("数据和算法", category="科技")
search("钱和市场", category="经济")

print("=" * 55)
print("Demo 3：跨语言搜索（英文查中文）")
print("=" * 55 + "\n")
search("how does deep learning work")
search("ancient Chinese history")
search("healthy lifestyle tips")
