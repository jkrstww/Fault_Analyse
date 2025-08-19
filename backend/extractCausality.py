import json
import os
from openai import OpenAI
from fileUtils import read_file, split_sentences
import re
from pathlib import Path

input_path = './规程'
output_path = './output/steam turbine cause-effect'

prompt = '''
请从以下文本中提取所有明确表达的直接因果关系，以<Answer>标签输出结果。每个因果关系以二元组形式呈现，格式为"原因,结果"，使用中文逗号分隔，每对因果关系单独成行：

识别标准：
原因和结果必须存在直接的逻辑因果关系
优先提取包含因果关联词（因为、导致、由于、因此等）的明确表述
保持原因和结果的简洁性（不超过20字）
输出规范：
严格使用"原因,结果"的二元结构
多个因果关系用换行分隔
保持原始文本中的关键词表达
忽略未形成明确因果链的并列关系
文本内容：
"{用户输入}"

示例1
输入："因为台风登陆，导致沿海地区停电，随后救援队伍紧急出动"
输出：
<Answer>
台风登陆,沿海地区停电
沿海地区停电,救援队伍紧急出动
</Answer>

示例2
输入："暴雨引发山体滑坡，而滑坡阻断了道路"
输出：
<Answer>
暴雨,山体滑坡
山体滑坡,道路阻断
</Answer>

示例3
输入："他连续三个月健身后，体检指标恢复正常"
输出：
<Answer>
连续健身,体检指标正常
</Answer>

示例4
输入："材料缺陷和工艺不当共同导致产品批量报废"
输出：
<Answer>
材料缺陷,产品报废
工艺不当,产品报废
</Answer>

示例5
输入："过度砍伐造成水土流失，最终导致河流淤塞"
输出：
<Answer>
过度砍伐,水土流失
水土流失,河流淤塞
</Answer>

示例6
输入："尽管采取防护措施，疫情仍因变异毒株扩散"
输出：
<Answer>
变异毒株扩散,疫情扩散
</Answer>

示例7
输入："地震发生在凌晨3点，次日早晨才恢复供电"
输出：
<Answer>
地震,供电中断
</Answer>

示例8
输入："央行加息导致股市下跌，进而引发消费市场萎缩"
输出：
<Answer>
央行加息,股市下跌
股市下跌,消费市场萎缩
</Answer>

示例9
输入："咖啡和茶都是常见的提神饮品"
输出：<Answer></Answer>

示例10
输入："火灾发生后消防队抵达现场，但建筑已完全坍塌"
输出：
<Answer>
火灾,建筑坍塌
</Answer>

示例11
输入："营养不良削弱免疫力，从而增加患病风险"
输出：
<Answer>
营养不良,免疫力削弱
免疫力削弱,患病风险增加
</Answer>

示例12
输入："交通事故被查明是刹车失灵造成的"
输出：
<Answer>
刹车失灵,交通事故
</Answer>

示例13
输入："用户粘性下降反映出产品体验存在问题"
输出：
<Answer>
产品体验问题,用户粘性下降
</Answer>

示例14
输入："促销活动提升了销量，但物流延迟导致投诉增加"
输出：
<Answer>
促销活动,销量提升
物流延迟,投诉增加
</Answer>

示例15
输入："实验员未按规范操作，三天后设备出现不可逆损坏"
输出：
<Answer>
未按规范操作,设备损坏
</Answer>

特殊情况处理：

当文本无因果关系时返回<Answer></Answer>
对潜在多重因果链需展开为独立二元组</Answer>
<工作流程>

先定位所有因果关联词标记
根据语义边界划分独立因果单元
提取核心原因和对应直接结果
按原文顺序排列因果关系
</工作流程>
请确保输出仅包含<Answer>标签内的结构化内容，不添加任何解释性文字。</Answer>

文本输入如下：
'''

def use_sentence(input_path):
    client = OpenAI(
        api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    file_num = len(os.listdir(input_path))

    finished_files = os.listdir(output_path)

    i = 1
    for file in os.listdir(input_path):
        print("{}/{} {}".format(i, file_num, file))

        if file.split('.')[0] + '.json' in finished_files:
            i += 1
            continue

        text = read_file(input_path + '/' + file)
        if text == "next":
            continue
        sentences = split_sentences(text)
        print(sentences)

        output = []
        for j in range(0, len(sentences), 4):
            sentence = ""
            rightWidth = len(sentences)
            if j+4<len(sentences):
                rightWidth = j+4
            for k in range(j, rightWidth):
                sentence += sentences[k]

            print(sentence)
            data_json = {}
            data_json['id'] = int(j/4 + 1)
            data_json['sentence'] = sentence
            data_json['cause-effect'] = []
            # print(sentence)
            try:
                completion = client.chat.completions.create(
                    # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
                    model="qwen3-235b-a22b",
                    messages=[
                        {"role": "system", "content": "现在你需要从文本中提取因果信息。"},
                        {"role": "user", "content": prompt+"\n"+sentence},
                    ],
                    # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
                    # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
                    extra_body={"enable_thinking": False},
                )

                answer = completion.choices[0].message.content

                # print(answer)

                if answer == "<Answer></Answer>":
                    continue
                else:
                    matches = re.findall(r"<Answer>(.*?)</Answer>", answer, re.DOTALL)

                    for match in matches:
                        if match.strip().replace('\n', '') == "":
                            continue
                        else:
                            match_list = match.split('\n')
                            # print(match_list)
                            for match in match_list:
                                if match == '\n' or match == '' or match == ' ':
                                    continue
                                else:
                                    data_json['cause-effect'].append(match)

                if len(data_json['cause-effect']) != 0:
                    output.append(data_json)
            except:
                print("error")

        if len(output) != 0:
            with open(output_path + '/' +file.split('.')[0]+'.json', 'w', encoding="UTF-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            f.close()

        i += 1

def use_file(input_path):
    root_path = input_path
    for dir in os.listdir(root_path):
        print(dir)
        dir_path = root_path + '/' + dir

        for file in os.listdir(dir_path):
            print('    -' + file)
            file_path = dir_path + '/' + file

            client = OpenAI(
                # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
                api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            file_object = client.files.create(file=Path(file_path), purpose="file-extract")

            # 初始化messages列表
            completion = client.chat.completions.create(
                model="qwen-long",
                messages=[
                    {'role': 'system', 'content': '现在你需要从文本中提取因果信息。'},
                    # 请将 'file-fe-xxx'替换为您实际对话场景所使用的 fileid。
                    {'role': 'system', 'content': 'fileid://{}'.format(file_object.id)},
                    {'role': 'user', 'content': prompt}
                ],
                # 所有代码示例均采用流式输出，以清晰和直观地展示模型输出过程。如果您希望查看非流式输出的案例，请参见https://help.aliyun.com/zh/model-studio/text-generation
                stream=True,
                stream_options={"include_usage": True}
            )

            full_content = ""
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    # 拼接输出内容
                    full_content += chunk.choices[0].delta.content

            matches = re.findall(r"<Answer>(.*?)</Answer>", full_content, re.DOTALL)

            output = ''
            for match in matches:
                if match.strip().replace('\n', '') == "":
                    continue
                else:
                    match_list = match.split('\n')
                    # print(match_list)
                    for match in match_list:
                        if match == '\n' or match == '' or match == ' ':
                            continue
                        else:
                            output = output + match + '\n'

            with open(dir_path + '/' + file.split('.')[0]+'.txt', 'w', encoding="UTF-8") as f:
                f.write(output)
            f.close()

use_sentence(input_path)
# use_file()