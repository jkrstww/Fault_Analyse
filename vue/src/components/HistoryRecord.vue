<template>
  <div class="chat-container">
    <!-- 主按钮 -->
    <button
      class="chat-button"
      @click="showModal = true"
    >
      查看分析对话
    </button>

    <!-- 弹窗遮罩 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <!-- 弹窗主体 -->
      <div class="modal-content">
        <!-- 弹窗头部 -->
        <div class="modal-header">
          <h2 class="modal-title">故障分析对话</h2>
          <button class="close-btn" @click="showModal = false">×</button>
        </div>

        <!-- 对话内容区域 -->
        <div class="chat-body">
          <div
            v-for="(msg, index) in chatData"
            :key="index"
            :class="['message', msg.role === 'user' ? 'user-message' : 'system-message']"
          >
            <!-- 消息内容 -->
            <div class="message-content">{{ msg.content }}</div>
            <!-- 时间戳 -->
            <div class="message-time">{{ formatTime(msg.time) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const showModal = ref(false);

// 原始对话数据
const chatData = [
  {
    role: "user",
    content: "变压器绕组变形",
    time: "2025-7-17 17:8:40"
  },
  {
    role: "system",
    content: "好的，我是你的变压器故障分析助手。我们先从你提供的信息“变压器绕组变形”开始分析。接下来我会根据参考文献中的因果关系逐步推理，并通过几轮提问帮助你找到根本原因。\n\n---\n\n### 第一步：分析初始现象\n\n**用户描述的故障现象：** 变压器绕组变形\n\n我们首先查看参考文献中与“绕组变形”相关的因果关系：\n\n#### 相关因果关系（来自参考文献）：\n1. **短路电流冲击 → 绕组变形**\n2. **机械外力撞击 → 绕组变形**\n3. **绕组绝缘老化、松动 → 机械强度下降 → 绕组变形**\n4. **运输或安装不当 → 绕组位移或变形**\n\n---\n\n### 初步因果链：\n\n```\n短路电流冲击\n│\n└→ 绕组受到电磁力作用 → 绕组变形\n\n机械外力撞击\n│\n└→ 外部力量作用于绕组结构 → 绕组变形\n\n绕组绝缘老化、松动\n│\n└→ 支撑结构失效 → 机械强度下降 → 绕组变形\n\n运输或安装不当\n│\n└→ 外部震动或错位 → 绕组位移或变形\n```\n\n---\n\n### 我的第一个问题是：\n\n**问题1：该变压器近期是否发生过外部短路故障？例如线路短路、雷击等？**\n\n请回答是 / 否 / 不确定，或者提供更多信息。",
    time: "2025-07-17 17:08:56"
  }
];

// 时间格式化函数
function formatTime(timeStr) {
  const [date, time] = timeStr.split(' ');
  const [year, month, day] = date.split('-');
  const [hour, minute, second] = time.split(':');
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')} ${hour}:${minute}:${second}`;
}
</script>

<style scoped>
/* 主按钮样式 */
.chat-button {
  padding: 12px 24px;
  background-color: #3B82F6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background-color 0.2s ease;
}

.chat-button:hover {
  background-color: #2563EB;
}

/* 遮罩层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

/* 弹窗主体 */
.modal-content {
  background: white;
  border-radius: 12px;
  width: 60%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

/* 弹窗头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #E5E7EB;
  background: #F9FAFB;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #6B7280;
  cursor: pointer;
}

/* 对话内容区域 */
.chat-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 消息基础样式 */
.message {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  position: relative;
  word-wrap: break-word;
}

/* 用户消息样式 */
.user-message {
  align-self: flex-end;
  background-color: #3B82F6;
  color: white;
}

/* 系统消息样式 */
.system-message {
  align-self: flex-start;
  background-color: #F3F4F6;
  color: #111827;
}

/* 时间戳样式 */
.message-time {
  font-size: 12px;
  margin-top: 8px;
  text-align: right;
  color: #9CA3AF;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-content {
    width: 90%;
  }
}
</style>