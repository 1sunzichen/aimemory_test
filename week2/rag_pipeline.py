"""
Day 11: RAG 串联
Embed → 搜 → Prompt → 生成
把知识库 + LLM 串成一条完整的问答流水线
依赖：pip install chromadb sentence-transformers modelscope openai
"""
import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from modelscope.hub.snapshot_download import snapshot_download
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ====== 第一步：Embed —— 加载模型 ======

print("加载 Embedding 模型...")
model_dir = snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
embed_model = SentenceTransformer(model_dir)
print("模型加载完成\n")

class LocalEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return embed_model.encode(input).tolist()

# ====== 知识库文档 ======

DOCS = [
    {"id": "1",  "text": "RAG（检索增强生成）是一种将向量检索与大语言模型结合的技术，先检索相关文档，再生成答案。", "topic": "RAG"},
    {"id": "2",  "text": "向量数据库将文本转换为高维向量存储，支持语义相似度搜索，常用于 RAG 系统。", "topic": "RAG"},
    {"id": "3",  "text": "Embedding 是将文本映射到向量空间的过程，语义相近的文本向量方向接近。", "topic": "RAG"},
    {"id": "4",  "text": "Chroma 是一个轻量级向量数据库，支持本地运行，适合学习和小型项目。", "topic": "RAG"},
    {"id": "5",  "text": "余弦相似度通过计算两个向量夹角的余弦值来衡量语义相似程度，结果在 -1 到 1 之间。", "topic": "RAG"},
    {"id": "6",  "text": "Python 是目前最流行的编程语言，广泛用于 AI、数据分析和 Web 开发。", "topic": "编程"},
    {"id": "7",  "text": "Go 语言以高并发和简洁语法著称，适合构建高性能后端服务。", "topic": "编程"},
    {"id": "8",  "text": "深度学习通过多层神经网络自动提取特征，在图像、语音、文本任务上表现出色。", "topic": "AI"},
    {"id": "9",  "text": "Transformer 架构引入自注意力机制，允许模型同时关注序列中所有位置的信息。", "topic": "AI"},
    {"id": "10", "text": "大语言模型（LLM）通过在海量文本上预训练，学会了语言规律和世界知识。", "topic": "AI"},
    {"id": "11", "text": "微调（Fine-tuning）是在预训练模型基础上，用少量特定领域数据继续训练，使模型适应特定任务。", "topic": "AI"},
    {"id": "12", "text": "LoRA 是一种参数高效的微调方法，只训练少量额外参数，大幅降低显存需求。", "topic": "AI"},
    {"id": "13", "text": "Function Calling 让 LLM 能够调用外部函数和工具，扩展了模型的能力边界。", "topic": "AI"},
    {"id": "14", "text": "Prompt 工程是设计和优化输入提示词的技术，直接影响 LLM 的输出质量。", "topic": "AI"},
    {"id": "15", "text": "Agent 是能够自主规划、调用工具、执行多步骤任务的 AI 系统。", "topic": "AI"},
]

# ====== 第二步：建库，存入文档 ======

db = chromadb.Client()
collection = db.create_collection(
    name="knowledge",
    embedding_function=LocalEmbeddingFunction(),
    metadata={"hnsw:space": "cosine"},
)
collection.add(
    ids=[d["id"] for d in DOCS],
    documents=[d["text"] for d in DOCS],
    metadatas=[{"topic": d["topic"]} for d in DOCS],
)
print(f"知识库已建好，共 {collection.count()} 条文档\n")

# ====== 第三步：搜 —— 检索相关文档 ======

def retrieve(query: str, n: int = 3) -> list[str]:
    results = collection.query(query_texts=[query], n_results=n)
    return results["documents"][0]

# ====== 第四步：Prompt —— 拼装上下文 ======

def build_prompt(question: str, context_docs: list[str]) -> str:
    context = "\n".join(f"- {doc}" for doc in context_docs)
    return f"""你是一个知识问答助手。请根据以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请直接说"我的知识库里没有这方面的信息"。

参考资料：
{context}

用户问题：{question}

请简洁准确地回答："""

# ====== 第五步：生成 —— 调 LLM 生成答案 ======

def generate(prompt: str) -> str:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# ====== 完整 RAG 流水线 ======

def rag(question: str):
    print(f"问题：{question}")
    print("-" * 50)

    # Step 1: 检索
    docs = retrieve(question, n=3)
    print("检索到的相关文档：")
    for i, doc in enumerate(docs, 1):
        print(f"  {i}. {doc[:50]}...")

    # Step 2: 拼 Prompt
    prompt = build_prompt(question, docs)

    # Step 3: 生成
    answer = generate(prompt)
    print(f"\n回答：{answer}\n")

# ====== 演示 ======

questions = [
    "RAG 是什么，它是怎么工作的？",
    "LoRA 微调有什么优点？",
    "向量数据库和普通数据库有什么区别？",
    "今天北京天气怎么样？",  # 知识库里没有，测试边界情况
]

print("=" * 50)
print("RAG 问答系统演示")
print("=" * 50 + "\n")

for q in questions:
    rag(q)
    print()

# ====== 交互模式 ======

print("=" * 50)
print("进入交互模式（输入 quit 退出）")
print("=" * 50 + "\n")

while True:
    question = input("你的问题：").strip()
    if not question:
        continue
    if question.lower() == "quit":
        print("再见！")
        break
    rag(question)
