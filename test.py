import chromadb

chroma_client = chromadb.PersistentClient(path="D:/internal project/chroma_storage")
# 新建一个collection并指定name且name唯一
collection = chroma_client.create_collection(name="chroma_local_db04")
# 添加document
collection.add(
    documents=["天坛", "月饼"],
    metadatas=[{"source": "d1"}, {"source": "d2"}],
    ids=["1", "2"],
)
# 检索
results = collection.query(
    query_texts=["哪个是景点"],
    n_results=1
)
print(f'运行结果为：{results}')


                          
