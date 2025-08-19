from openai import OpenAI

with open(r'D:\Project\Text2Graph\output\transformer cause-effect\500kV主变差动保护跳闸的处理.json', 'r',
          encoding='UTF-8') as f:
    information = f.read()
f.close()

message = request.get_json()['message']
client = OpenAI(
    api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    model="qwen3-235b-a22b",
    messages=[
        {"role": "system",
         "content": "你是变压器故障分析专家。你需要根据变压器故障描述按照寻找参考文献中对应内容，指出对应内容包含的因果关系，根据因果关系确定下一步思考的方向的顺序一步一步地给出思考的过程。参考文献中'sentence'代表原始句子,'cause-effect'代表因果关系，用','隔开，代表前面的是后面的原因。参考文献如下：" + information + "然后你需要根据这些内容向用户提问，根据用户的回答继续进行深入思考。在2~3轮询问后，停止继续询问，给出根本原因。"},
        {"role": "user", "content": message},
    ],
    # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
    # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
    extra_body={"enable_thinking": False},
)