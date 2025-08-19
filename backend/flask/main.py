from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import ollama
from PIL import Image
import io
import base64

import fileUtils
from fileUtils import get_encoding
from flask_cors import CORS
from datetime import datetime
import json
from openai import OpenAI
import time
from agents import nameHistoryChatAgent, searchReferenceAgent, recommendAgent, referenceAgent, intentionAgent
from fileUtils import read_file
import uuid

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'doc', 'docx', 'txt', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 允许最大 10MB

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

history_message = []
chat_message = []

recommend_list = []
reference_list = []

# 历史记录所在目录
history_chat_path = r'D:\Project\Text2Graph\flask\uploads\history\chatMessages'
reference = r"D:\Project\Text2Graph\output\steam turbine cause-effect\#2机2022年小修冷态验收报告（汽机专业）汇报版.json"

# 原始数据所在目录
original_file_path = r'D:\Project\Text2Graph\files'

json_file_path = r'D:\Project\Text2Graph'

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/causeExtract', methods=['POST'])
def upload_file():
    """处理文件上传"""
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file_size = request.files['file'].content_length
    file = request.files['file']

    # 检查是否选择了文件
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 验证文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        # # 安全处理文件名并保存
        # filename = secure_filename(file.filename)
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print(file.content_length)
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'filename': filename,
            'file_size': file_size,
            'upload_time': datetime.now()
        }), 200
    except Exception as e:
        return jsonify({'error': f'File save failed: {str(e)}'}), 500

@app.route('/extractFromText', methods=['POST'])
def extract():
    filename = request.form.get('filename')
    print(filename)

    data = {}
    with open(reference, 'r', encoding='UTF-8') as f:
        data = json.load(f)
    f.close()

    pairs = []
    for perdata in data:
        for d in perdata['cause-effect']:
            pair = {}
            pair['cause'] = d.split(',')[0]
            pair['effect'] = d.split(',')[1]
            pairs.append(pair)

    return jsonify({
        'header': 'Access-Control-Allow-Origin:*',
        'status': 'success',
        'data': pairs
    }), 200

@app.route('/chat', methods=['POST'])
def chat():
    system_answer_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    if request.get_json()['isChosenFile']:
        message = request.get_json()['message']
        file_name = request.get_json()['filename']
        file_path = app.config['UPLOAD_FOLDER'] + r'\files' + '\\' + file_name

        content = fileUtils.read_file(file_path)

        print(content)

        client = OpenAI(
            api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen3-235b-a22b",
            # model="qwen-plus",
            messages=[
                {'role': 'system', 'content': '你是变压器故障领域的专家，现在根据文档内容以及用户提问，做出回答。'},
                {'role': 'system', 'content': '文档内容如下：' + content},
                {'role': 'user', 'content': message}
            ],
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            extra_body={"enable_thinking": False},
        )

        answer = completion.choices[0].message.content

        return jsonify({
            'header': 'Access-Control-Allow-Origin:*',
            'reply': answer,
            'reference_list': [],
            'recommend_list': [],
            'time': system_answer_time
        }), 200

    if request.get_json()['isChosenImg']:
        message = request.get_json()['message']

        image_name = request.get_json()['imagename']
        image_path = app.config['UPLOAD_FOLDER'] + r'\images' + '\\' + image_name
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        answer = ollama.chat(
            model="qwen2.5vl:3b",
            messages=[{
                "role": "user",
                "content": message,
                "images": [img_base64]
            }],
        )

        print(answer)

        return jsonify({
            'header': 'Access-Control-Allow-Origin:*',
            'reply': answer.message['content'],
            'reference_list': [],
            'recommend_list': [],
            'time': system_answer_time
        }), 200

    if len(history_message) == 0:
        # with open(reference, 'r', encoding='UTF-8') as f:
        #     information = f.read()
        # f.close()
        history_message.append({
            "role": "system",
            "content": '''
            你是变压器故障分析专家。你需要根据变压器故障描述按照寻找参考文献中对应内容，指出对应内容包含的因果关系，根据因果关系确定下一步思考的方向的顺序一步一步地给出思考的过程。
            参考文献以reference按照顺序以[1],[2]的格式进行标注，其中filename代表参考文献文件名，'sentence'代表其中的原始句子,'cause-effect'代表因果关系，用','隔开，代表前面的是后面的原因。
            然后你需要根据这些内容向用户提问，根据用户的回答继续进行深入思考。在2~3轮询问后，停止继续询问，给出根本原因。
            '''
        })

    message = request.get_json()['message']
    user_upload_time = request.get_json()['time']

    chat_message.append({"role": "user", "content": message, "time": user_upload_time})
    history_message.append({"role": "user", "content": message})

    # 参考文献
    # reference_files = referenceAgent(message)
    # for file in reference_files:
    #     if file not in reference_list:
    #         reference_list.append(file)
    # history_message.append({
    #     "role": "assistant",
    #     "content": str(reference_files)
    # })

    # 推荐文献
    # recommend_files = recommendAgent(message)
    # for file in recommend_files:
    #     if file not in recommend_list:
    #         recommend_list.append(file)

    intention = intentionAgent(message)
    print(intention)

    if intention == True:
        recommends = recommendAgent(message)
        for r in recommends:
            recommend_list.append(r)

        answer = str('以下是推荐的资料：'+str(recommends))

    else:
        references = referenceAgent(message)
        for r in references:
            if r not in reference_list:
                reference_list.append(r['source'].split('\\')[3])

        history_message.append({"role": "user", "content": '以下是参考文献的具体内容：'+str(references)})

        client = OpenAI(
            api_key="sk-851e06a3453b4ea6ab720de65cc33fc0",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

        completion = client.chat.completions.create(
            # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="qwen3-235b-a22b",
            # model="qwen-plus",
            messages=history_message,
            # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
            # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
            extra_body={"enable_thinking": False},
        )

        answer = completion.choices[0].message.content

    history_message.append({"role": "system", "content": answer, "time": system_answer_time})
    chat_message.append({"role": "system", "content": answer, "time": system_answer_time})

    # 生成历史记录
    # history_record_name = nameHistoryChatAgent(history_message)
    # with open(history_chat_path + '\\' + history_record_name , 'w', encoding='UTF-8') as f:
    #     json.dump(history_message, f, ensure_ascii=False, indent=2)
    # f.close()

    return jsonify({
        'header': 'Access-Control-Allow-Origin:*',
        'reply': answer,
        'reference_list': reference_list,
        'recommend_list': recommend_list,
        'time': system_answer_time
    })

# 结束对话并保存对话记录
@app.route('/finishChat', methods=['GET'])
def finisheChat():
    file_name = nameHistoryChatAgent(chat_message)

    with open(history_chat_path + '\\' + file_name, 'w', encoding='UTF-8') as f:
        json.dump(chat_message, f, ensure_ascii=False, indent=2)
    f.close()

    return jsonify({
        "status": "success"
    }), 200

@app.route('/getHistoryRecordList', methods=['GET'])
def getHistoryRecordList():
    history_record_list = os.listdir(history_chat_path)

    return jsonify({
        "status": "success",
        "historyRecordList": history_record_list
    }), 200

@app.route('/getHistoryRecord/<filename>', methods=['GET'])
def getHistoryRecord(filename):
    print(filename)

    with open(history_chat_path + '\\' + filename, 'r', encoding='UTF-8') as f:
        messages = json.load(f)
    f.close()

    return jsonify({
        "status": "success",
        "messages": messages
    }), 200

@app.route('/getRecommendList', methods=['GET'])
def getRecommendList():
    return jsonify({
        "status": "success",
        "recommendList": recommend_list
    }), 200

@app.route('/getRecommendFile/<filename>', methods=['GET'])
def getRecommendFile(filename):
    text = read_file(original_file_path + '\\' + filename)

    return jsonify({
        "status": "success",
        "fileContent": text
    }), 200

@app.route('/getReferenceList', methods=['GET'])
def getReferenceList():
    return jsonify({
        "status": "success",
        "referenceList": reference_list
    }), 200

@app.route('/getReferenceFile/<filename>', methods=['GET'])
def getReferenceFile(filename):
    data = []
    file_path = json_file_path + '\\' + filename.replace('.docx', '.json')
    with open(file_path, 'r', encoding=get_encoding(file_path)) as f:
        data = json.load(f)
    f.close()

    return jsonify({
        "status": "success",
        "fileContent": data
    }), 200

@app.route('/upload/files', methods=['POST'])
def receiveFiles():
    file = request.files['file']
    try:
        # 生成唯一文件名防止覆盖
        # ext = file.filename.rsplit('.', 1)[1].lower()
        # unique_filename = f"{uuid.uuid4()}.{ext}"
        file_name = file.filename

        # 保存文件
        file_path = app.config['UPLOAD_FOLDER'] + r'\files' + '\\' + file_name
        file.save(file_path)

        # 可以返回文件信息
        return jsonify({
            'filename': file.filename,
            # 'saved_name': unique_filename,
            'file_path': file_path,
            'message': '文件上传成功'
        }), 200

    except Exception as e:
        return jsonify({'error': f'保存文件时出错: {str(e)}'}), 500

@app.route('/upload/images', methods=['POST'])
def receiveImages():
    file = request.files['file']
    try:
        # 生成唯一文件名防止覆盖
        # ext = file.filename.rsplit('.', 1)[1].lower()
        # unique_filename = f"{uuid.uuid4()}.{ext}"
        file_name = file.filename

        # 保存文件
        file_path = app.config['UPLOAD_FOLDER'] + r'\images' + '\\' + file_name
        file.save(file_path)

        # 可以返回文件信息
        return jsonify({
            'filename': file.filename,
            # 'saved_name': unique_filename,
            'file_path': file_path,
            'message': '图片上传成功'
        }), 200

    except Exception as e:
        return jsonify({'error': f'保存图片时出错: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)