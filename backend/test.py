import os
from fileUtils import get_encoding
import json

input_path = r'.\transformer.json'
output_path = r'.\transformer2.json'

with open(input_path, 'r', encoding=get_encoding(input_path)) as f:
    this_data = json.load(f)
f.close()

id = 1
data = []
for obj in this_data:
    new_obj = {}
    new_obj['id'] = id
    new_obj['sentence'] = obj['sentence'].replace("\u00A0", " ").replace("\u200b", "").replace("\u3000", " ")
    new_obj['cause_effect'] = obj['cause-effect']

    data.append(new_obj)
    id += 1

with open(output_path, 'w', encoding='UTF-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
f.close()

