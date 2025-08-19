from sentence_transformers import SentenceTransformer, util

# 加载预训练模型（如 'all-MiniLM-L6-v2' 是轻量且效果不错的模型）
model = SentenceTransformer('all-MiniLM-L6-v2')

# 目标词
target_word = "happy"

# 候选词列表
words = ["joyful", "sad", "glad", "angry", "content"]

# 编码所有词
word_embeddings = model.encode(words)
target_embedding = model.encode([target_word])

# 计算余弦相似度
cos_sim = util.cos_sim(target_embedding, word_embeddings)

# 找出最相似的词
most_similar_index = cos_sim.argmax()
most_similar_word = words[most_similar_index]

print(f"最相似的词是: {most_similar_word}")