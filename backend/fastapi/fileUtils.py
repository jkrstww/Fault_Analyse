import os
import re
import chardet
from docx import Document
import win32com.client
from pdf2image import convert_from_path
import pytesseract
import json

pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'

def get_encoding(file_path):
    with open(file_path, 'rb') as f:
        tmp = chardet.detect(f.read())
        return tmp['encoding']

def read_file(file_path):
    if file_path.endswith('.docx'):
        docx = Document(file_path)
        text = ""
        for paragraph in docx.paragraphs:
            text += paragraph.text
        return text

    if file_path.endswith('.doc'):
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False  # 后台运行
        try:
            doc = word.Documents.Open(file_path)
            text = doc.Content.Text
            doc.Close()
            return text.strip()
        except Exception as e:
            return f"读取失败: {str(e)}"
        finally:
            word.Quit()

    if (file_path.endswith('.pdf')):
        # reader = PdfReader(file_path)
        # text = ""
        # for page in reader.pages:
        #     text += page.extract_text() + "\n"
        # return text

        pages = convert_from_path(file_path, dpi=200)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, lang="chi_sim") + "\n"
        return text

    encoding = get_encoding(file_path)
    """读取文本文件内容"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        print("文件未找到，请检查路径是否正确。")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return None

def split_paragraphs(content):
    """按换行符分割段落，并过滤空段落"""
    return [p.strip() for p in content.split('\n') if p.strip()]

def split_sentences(text):
    """按中文句末标点拆分句子（保留标点）"""
    # 使用正则表达式分割句子，保留句末标点
    parts = re.split(r'([。！？])', text)
    sentences = []
    # 配对句子和对应的标点
    for i in range(0, len(parts) - 1, 2):
        sentences.append(parts[i].strip() + parts[i + 1])
    # 处理最后一个部分，如果没有标点
    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences

def construct_graph():
    input_files = os.listdir("./output/锅炉1")
    output_file = '锅炉.json'

    graph = []
    cause_map = {}  # 记录 cause 在 graph 中的索引
    id_counter = 1  # 用于生成唯一的 id

    # 遍历每个文件
    for filename in input_files:
        try:
            with open("./output/锅炉1/" + filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 分割因和果
                    parts = line.split(',', 1)
                    if len(parts) < 2:
                        continue

                    cause = parts[0].strip()
                    effect = parts[1].strip()

                    # 如果 cause 已存在，追加 effect（去重）
                    if cause in cause_map:
                        index = cause_map[cause]
                        if effect not in graph[index]['effect']:
                            graph[index]['effect'].append(effect)
                    else:
                        # 创建新的 entry
                        new_entry = {
                            'id': id_counter,
                            'cause': cause,
                            'effect': [effect]
                        }
                        graph.append(new_entry)
                        cause_map[cause] = len(graph) - 1
                        id_counter += 1

        except FileNotFoundError:
            print(f"警告：文件 {filename} 不存在，已跳过。")
        except Exception as e:
            print(f"读取文件 {filename} 时出错：{e}")

    # 构建最终 JSON 结构
    result = {
        "graph": graph
    }

    # 写入 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def merge_output(file_path):
    list = ''
    for file in os.listdir(file_path):
        with open(file_path + '/' + file, 'r', encoding="UTF-8") as f:
            lines = f.readlines()
            for line in lines:
                list += line
        f.close()

    with open(file_path + '/summary.txt' , 'w') as f:
        f.write(list)
    f.close()

# construct_graph()
# merge_output('./output/汽轮机')

# text = read_file("D:\Project\Text2Graph\检修报告\锅炉\华电莱州2020年#1机组大修金属检验报告汽机部分_1-100.docx")
# sentences = split_sentences(text)
# print((len(sentences)))
# print()

    input_file = './output/汽轮机/filtered.txt'
    output_file = '汽轮机.json'

    graph = []
    cause_map = {}  # 用于记录 cause 对应的 graph 索引
    id_counter = 1  # 用于生成唯一的 id

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) < 2:
            continue

        cause = parts[0].strip()
        effect = parts[1].strip()

        if cause in cause_map:
            # 如果 cause 已存在，追加 effect 到数组中
            index = cause_map[cause]
            graph[index]['effect'].append(effect)
        else:
            # 如果是新 cause，创建新对象并加入 graph
            new_entry = {
                'id': id_counter,
                'cause': cause,
                'effect': [effect]
            }
            graph.append(new_entry)
            cause_map[cause] = len(graph) - 1
            id_counter += 1

    # 构造最终 JSON 结构
    result = {
        "graph": graph
    }

    # 写入 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
