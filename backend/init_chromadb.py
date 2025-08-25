import chromadb
from grammar_search import MyEmbeddingFunction
from sentence_transformers import SentenceTransformer # 如果embedding需要

model = SentenceTransformer('all-MiniLM-L6-v2')
# 连接到本地已有 chroma_storage
client = chromadb.PersistentClient(path="D:/internal project/chroma_storage")

# 保持 embedding function 一致
embed_fn = MyEmbeddingFunction(model)

# 获取同一个 collection
collection = client.get_or_create_collection(
    name="grammar_corrections",
    embedding_function=embed_fn
)
with open("./grammar_corrections.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

documents = []
metadatas = []
ids = []
existing_count = collection.count()
print(existing_count)
for idx, line in enumerate(lines):
    # 确保是四列
    

    parts = [s.strip() for s in line.split("|")]
    if len(parts) != 4:
      print(f"格式不对，跳过：{parts}")
      continue
    if len(parts) == 4:
        original, correction, error_type, explanation = parts
        documents.append(original)
        metadatas.append({
            "correction": correction,
            "error_type": error_type,
            "explanation": explanation
        })
        ids.append(f"correction_{existing_count + idx + 1}")

# 添加到 Chroma collection
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)
print("数据已导入 ChromaDB。")