import json
import re
from openai import OpenAI
import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

global_api_key = "sk-851e06a3453b4ea6ab720de65cc33fc0"
global_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

json_file_path = r'D:\Project\Text2Graph\output\transformer cause-effect'

def nameHistoryChatAgent(history_message):
    client = OpenAI(
        api_key=global_api_key,
        base_url=global_base_url
    )

    prompt = "你现在需要根据用户利用系统进行故障诊断的历史数据的具体内容为这些数据取一个文件名。直接输出文件名，文件为json格式，不能包含特殊字符和空白字符，使用中文，格式为'名字_时间_json'，文件名不能超过50字。具体数据如下：" + str(history_message)

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        # model="qwen3-235b-a22b",
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": prompt}
        ],
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        extra_body={"enable_thinking": False},
    )

    return completion.choices[0].message.content

# 根据关键词搜索相关文档
def searchReferenceAgent(behavior: str):
    client = OpenAI(
        api_key=global_api_key,
        base_url=global_base_url
    )

    # 文档库
    file_list = os.listdir(r'D:\Project\Text2Graph\output\transformer cause-effect')

    prompt = "你是故障诊断领域的专家，现在给出故障表现，你需要从文档库中找到相关的文献，不超过3个。故障表现为：" + behavior + '文档库为：' + str(file_list) + '直接输出文档名，如果涉及多个，以换行符分割。'

    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": prompt}
        ],
        # extra_body={"enable_thinking": False},
    )

    ret = completion.choices[0].message.content.split('\n')
    print(ret)
    return ret

# 在json文件中寻找最匹配的段落
def searchReferenceSentenceAgent(filePath: str, keyWord: str):
    with open(filePath, 'r', encoding='UTF-8') as f:
        sentences = json.load(f)
    f.close()

    client = OpenAI(
        api_key=global_api_key,
        base_url=global_base_url
    )

    prompt = "你是故障诊断领域的专家，现在给出故障表现的关键词，你需要根据故障描述按照从参考文献中提取对分析故障根本原因最具有帮助的部分。参考文献中'sentence'代表原始句子,'cause-effect'代表因果关系，用','隔开，代表前面的是后面的原因。参考文献为：" + str(sentences) + "直接输出选择后的内容。"
    prompt = '''
    你是故障诊断领域的专家，给出用户问题question与JSON内容请严格按照以下步骤处理任务：

    1.分析用户问题 ：识别问题中的核心关键词（如"动作原因"、"处理过程"等）和语义意图。
    2.扫描JSON内容 ：
        遍历输入JSON的每个对象，检查以下字段是否包含相关性：
        sentence 字段的主体描述
        cause-effect 列表中的因果关系对
    3.匹配逻辑 ：
        优先匹配问题与sentence字段的显式关键词
        次级匹配问题与cause-effect中的因果关系
        选择相关性最高的匹配项 （若多条匹配，返回最相关的一条）
    4.输出要求 ：
        严格保留原始JSON格式（包括id、sentence、cause-effect字段）
        仅返回匹配的完整对象，不要添加解释、总结或其他内容
        若无匹配项，返回空数组[]
    现在给出用户问题{question}。
    给出JSON内容：
    {json}
    
    请根据以下要求生成响应：
    1. 输出内容必须是有效的 JSON 格式；
    2. 不要使用任何 Markdown 格式（如 ```json）；
    3. 不要添加任何额外解释或说明；
    4. 直接输出 JSON 内容。
    '''
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": prompt.format(question=keyWord, json=sentences)}
        ],
        # extra_body={"enable_thinking": False},
    )

    ret = completion.choices[0].message.content
    print(ret)

    # print("-----------------------------------------")

    return json.loads(ret)

# 负责在对话过程中寻找参考文献
def referenceAgent(message: str):
    # reference_list = searchReferenceAgent(behavior)
    # ret_list = []
    #
    # for file in reference_list:
    #     sentences = searchReferenceSentenceAgent(json_file_path + '\\' + file, behavior)
    #
    #     obj = {}
    #     obj['filename'] = file
    #     obj['sentences'] = []
    #
    #     for sentence in sentences:
    #         obj['sentences'].append(sentence)
    #
    #     ret_list.append(obj)
    #
    # return ret_list
    embedding = OllamaEmbeddings(
        model='bge-m3'
    )

    vector_store = Chroma(
        # collection_name="transformers",
        embedding_function=embedding,
        persist_directory=r'D:\Project\Text2Graph\db\transformers_db'
    )

    retriever = vector_store.as_retriever(search_type='mmr')

    result = retriever.invoke(message)
    print(result)

    with open(r'D:\Project\Text2Graph\transformer2.json', 'r', encoding='utf-8') as f:
        origin_data = json.load(f)
    f.close()

    list = []
    for d in result:
        obj = {}
        id, source, content = d.metadata['seq_num'], d.metadata['source'], d.page_content
        obj['source'] = source
        obj['content'] = content
        obj['cause-effect'] = origin_data[int(id) - 1]['cause_effect']
        list.append(obj)

    return list

# 负责推荐文献
def recommendAgent(question: str):
    client = OpenAI(
        api_key=global_api_key,
        base_url=global_base_url
    )

    # 文档库
    file_list = os.listdir(r'D:\Project\Text2Graph\files')

    prompt = "你是故障诊断领域的专家，帮助用户解决问题。现在用户遇到了一些问题，你需要从文档库中找到能够帮助用户的文献。用户的问题是：" + question +  '文档库为：' + str(file_list) + '直接输出原始文档名，不要包含其他任何内容，如果涉及多个，以换行符分割，文献数量不超过3个。'

    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": prompt}
        ],
        extra_body={"enable_thinking": False},
    )

    ret = completion.choices[0].message.content.split('\n')
    return ret

def intentionAgent(message: str) -> bool:
    # client = OpenAI(
    #     api_key=global_api_key,
    #     base_url=global_base_url
    # )
    #
    # prompt = '根据用户输入的内容判断用户是否是想要让系统推荐一些资料，是的话输出true，否则输出false。以下是输入内容：'+message
    #
    # completion = client.chat.completions.create(
    #     model="qwen-plus",
    #     messages=[
    #         {"role": "system", "content": prompt}
    #     ],
    #     extra_body={"enable_thinking": False},
    # )
    #
    # ret = completion.choices[0].message.content

    if '推荐' in message:
        return True
    else:
        return False



if __name__ == "__main__":
    searchReferenceSentenceAgent(r"D:\Project\Text2Graph\output\transformer cause-effect\500kV主变差动保护跳闸的处理.json", "差动保护")