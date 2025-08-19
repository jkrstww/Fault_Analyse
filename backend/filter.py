import os
from openai import OpenAI

path = './output/汽轮机'

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

with open(path + "/summary.txt", 'r', encoding='gbk') as f:
    lines = f.readlines()
f.close()

prompt = '''
请根据以下规则对输入的因果关系对进行过滤，并输出符合要求的关系对列表：

规则：

保留条件 ：
关系对的"原因"和"结果"必须均为具体设备、部件、系统或可明确的技术操作 （如"泵轴磨损""滤网堵塞""真空泵不出力"等）。
"原因"与"结果"之间需存在因果关系 （例如设备故障导致更换、参数异常引发保护动作等）。
过滤条件 ：
排除包含非具体事物 （如"原因""方法""经验提升""阅读手册"等抽象概念）的关系对。
排除无因果关系或逻辑模糊的关系对（如问题与回答、操作建议与目标等）。
输入格式：
每行一组关系对，用逗号分隔，格式为原因,结果。

输出要求：

仅输出过滤后保留的关系对，保持原格式与顺序。
无需解释或额外内容。
'''
answer = ''

for i in range(0, len(lines), 20):
    print(i)
    input = ''
    for j in range(20):
        input += lines[j]

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen3-235b-a22b",
        messages=[
            {"role": "system", "content": "现在你需要过滤因果信息。"},
            {"role": "user", "content": prompt + "\n" + input},
        ],
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        extra_body={"enable_thinking": False},
    )

    answer += completion.choices[0].message.content

with open (path + '/filtered.txt', 'w') as f:
    f.write(answer)
f.close()

