import json
import os
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import  StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import List, Dict
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], # 设置允许跨域的域名列表，* 代表所有域名
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# dashscope.api_key = 'sk-851e06a3453b4ea6ab720de65cc33fc0'

# 线程池用于处理同步的Qwen API调用
executor = ThreadPoolExecutor(max_workers=5)

# 用于存储对话会话
sessions = {}
messages = []
messages.append(SystemMessage(
    content='''
        你是故障诊断领域的专家，你需要根据用户输入以及参考文献一步一步地对故障根本原因进行推理。
        每一次完成分析之后，你需要结合分析的结论询问用户与故障诊断相关的问题，比如发现变压器发热可能是由于高温环境，冷却系统故障，散热不畅等因素导致，
        则需要询问用户1.环境温度是多少？2.检测冷却系统是否故障。3.检测散热是否通畅。根据用户的反馈进行下一步的推理，在推理2~3轮后找出根本原因。
    ''')
)

sessions['test'] = {
    "messages": messages,
    "model": 'llama3.2'
}

reference_list = []

chosen_model = 'deepseek-r1'
class ChatMessage(BaseModel):
    avatar: str
    name: str
    datetime: str
    content: str
    role: str

class ChatMessages(BaseModel):
    create_time: str
    messages: List[ChatMessage]

# 历史记录所在目录
history_chat_path = r'.\history'
files_path = r'..\output\transformer cause-effect'
UPLOAD_DIR = r'.\upload'

def clearMessage():
    while len(messages) != 0:
        messages.pop(0)
    print("clear success")

def clearReference():
    while len(reference_list) != 0:
        reference_list.pop(0)

def searchDB(prompt: str):
    embedding = OllamaEmbeddings(
        model='bge-m3'
    )

    vector_store = Chroma(
        embedding_function=embedding,
        persist_directory='../db/transformer_db'
    )

    # retriever = vector_store.as_retriever(search_type='mmr', search_kwargs={'k': 5})
    #
    # result = retriever.invoke(prompt)

    retriever = vector_store.as_retriever(
        search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10}
    )

    result = retriever.invoke(prompt)

    # result = vector_store.similarity_search(
    #     query=prompt,
    #     k=5,
    #     # filter={"source": "tweet"},
    # )

    print(result)

    return result

def generate_reference(prompt: str):
    refs = searchDB(prompt)
    ret_list = []

    for ref in refs:
        obj = ref.metadata
        print(obj['source'])
        name = obj['source'].split('\\')[5].split('.')[0]
        cause_effect = str(obj['cause_effect'])
        content = ref.page_content
        id = len(reference_list) + 1

        new_obj = {
            'id': id,
            'name': name,
            'cause_effect': cause_effect,
            'content': content
        }

        reference_list.append(new_obj)
        ret_list.append(new_obj)

    return ret_list

async def generate_response(prompt: str):
    print(messages)
    full_text = ''

    model = ChatOllama(
        model=chosen_model
    )

    async for chunk in model.astream(messages):
        full_text += chunk.content
        # print(chunk.content, end='|')
        yield chunk.content

    # convert = {
    #     'system': 'system',
    #     'ai': 'assistant',
    #     'human': 'user'
    # }
    #
    # loop = asyncio.get_event_loop()
    #
    # # 在线程池中执行同步的API调用
    # response = await loop.run_in_executor(
    #     executor,
    #     lambda: dashscope.Generation.call(
    #         model='qwen3-235b-a22b',  # 可替换为qwen-plus、qwen-turbo等
    #         messages=[{"role": convert[msg.type], "content": msg.content} for msg in messages],
    #         stream=True  # 关键：启用流式输出
    #     )
    # )
    #
    # # 逐块处理流式响应
    # for chunk in response:
    #     print(chunk)
    #     # 检查是否有文本内容
    #     if chunk.output.choices:
    #         text = chunk.output.choices[0].message.content
    #         if text:
    #             yield text

    messages.append(AIMessage(content=full_text))

@app.post("/getReferenceFile")
async def getReferenceFile(request: Request):
    data = await request.json()
    name = data.get("filename", "")
    file_path = files_path + '\\' + name + '.json'

    with open(file_path, 'r', encoding='utf-8') as f:
        ret = json.load(f)
    f.close()

    return {
        'data': ret
    }


async def event_generator():
    # count = 0
    # while True:
    #     await asyncio.sleep(1)
    #     count += 1
    #     data = {"count": count}
    #     yield json.dumps(data)
    model = ChatOllama(
        model='llama3.2'
    )

    async for chunk in model.astream('你是谁？'):
        # print(chunk.content, end='|', flush=True)
        yield json.dumps(chunk.content, ensure_ascii=False)
        # yield chunk.content

@app.get("/events")
async def get_events():
    return EventSourceResponse(event_generator())
@app.post("/events")
async def post_events():
      return EventSourceResponse(event_generator())

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
async def test():
    return event_generator()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/getReferenceList")
def getReferenceList():
    return {
        "data": reference_list,
        "num": len(reference_list),
        "status": "success"
    }
0
@app.post('/chat')
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    filename = data.get("filename", "")
    print(filename)

    if filename != "":
        if filename.split('.')[1] in ['doc', 'txt', 'docx', 'pdf']:
            print("sss")
            clearMessage()
            clearReference()
            # file_content = read_file(UPLOAD_DIR + '\\' + filename)
            # print(file_content)
            messages.append(HumanMessage(content=prompt + '文件内容如下：' + 'filecontent'))

    else:
        messages.append(HumanMessage(content=prompt))

        refs = generate_reference(prompt)
        def refsToPrompt(refs: List):
            content = '''
                以下是参考文献，其中:后面的是因果关系对，"A,B"代表A是因，B是果。
            '''
            for ref in refs:
                content += '[' + str(ref['id']) + ']' + ref['name'] + ':' + ref['cause_effect'] + ';'

            return content

        ref_prompt = refsToPrompt(refs)

        messages.append(HumanMessage(content=ref_prompt))

    return StreamingResponse(
        generate_response(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            'X-Accel-Buffering': 'no'
        }
    )

@app.get("/chatSSE/{prompt}")
async def chat_sse(prompt: str):

    async def event_stream(prompt: str):
        # client = openai.OpenAI(
        #     api_key='sk-851e06a3453b4ea6ab720de65cc33fc0',
        #     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        # )
        #
        # response = client.chat.completions.create(
        #     model="qwen3-235b-a22b",
        #     messages=[{"role": "user", "content": prompt}],
        #     stream=True
        # )
        model = ChatOllama(
            model='llama3.2'
        )
        async for chunk in model.astream(prompt):
            yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )

@app.get("/getHistory")
def getHisotry():
    file_list = os.listdir(history_chat_path)
    ret = []

    for file in file_list:
        obj = {}
        obj['name'] = file.split('.')[0]

        ret.append(obj)

    return {
        "status": "success",
        "data": ret
    }

@app.post("/getHistoryMessages")
async def showHistory(request: Request):
    data = await request.json()
    history_name = data.get('name', '')

    file_path = history_chat_path + '\\' + history_name + '.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data

@app.post("/createHistory")
def createHistory(chatmessages: ChatMessages):
    data = jsonable_encoder(chatmessages)

    file_name = data['messages'][-2]['content'] + '.json'

    file_path = history_chat_path + '\\' + file_name

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()

    # 重置
    clearMessage()
    clearReference()
    messages.append(SystemMessage(
        content='''
            你是故障诊断领域的专家，你需要根据用户输入以及参考文献一步一步地对故障根本原因进行推理，
            在必要时，你需要询问用户，用于下一步的推理。
        ''')
    )

    return {
        "status": "success"
    }

@app.post('/upload/files')
async def receiveFiles(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 返回文件访问URL（需要配置静态文件服务）
    return {
        "file_type": file.content_type,
        "file_size": f"{len(await file.read()) / 1024:.2f} KB"
    }

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)