import json
import os

from LocalLoader import JSONLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4

embedding = OllamaEmbeddings(
    model='bge-m3'
)

vector_store = Chroma(
    # collection_name="transformers",
    embedding_function=embedding,
    persist_directory='./db/transformer_db'
)

files_path = r'D:\Project\Text2Graph\output\transformer cause-effect'

for file in os.listdir(files_path):
    print(file)
    file_path = files_path + '\\' + file

    loader = JSONLoader(
        file_path=file_path
    )

    datas = loader.load()

    if len(datas) == 0:
        continue

    vector_store.add_documents(documents=datas)
#
# print(len(datas))

# uuids = [str(uuid4()) for _ in range(len(datas))]

# batch_size = 100
# for i in range(int(len(datas)/batch_size)):
#     vector_store.add_documents(documents=datas[i*batch_size:(i+1)*batch_size], ids=uuids[i*batch_size:(i+1)*batch_size])
#     print((batch_size*i))

# retriever = vector_store.as_retriever(search_type='mmr')
#
# result = retriever.invoke('冷却设备故障')
#
# print(result)

# with open('./transformer2.json', 'r', encoding='utf-8') as f:
#     origin_data = json.load(f)
# f.close()
#
# list = []
# for d in result:
#     obj = {}
#     id, source, content = d.metadata['seq_num'], d.metadata['source'], d.page_content
#     obj['id'] = id
#     obj['source'] = source
#     obj['content'] = content
#     obj['cause-effect'] = origin_data[int(id)-1]['cause_effect']
#     list.append(obj)
#
# print(list)
