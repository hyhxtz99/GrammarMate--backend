import chromadb

client = chromadb.PersistentClient(path="./chroma_storage")
collection = client.get_or_create_collection("grammar_corrections")
results = collection.get()
print(results)

# 验证清空
print(client.list_collections())  # 应该为空
