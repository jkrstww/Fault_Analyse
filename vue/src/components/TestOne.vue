<template>
  <div class="main-container">
    <div class="history-panel">
      <div class="history-header">
        <h2>对话历史</h2>
        <button class="new-chat-btn" @click="createHistory">+ 新对话</button>
      </div>

      <div class="history-list" id="historyList" v-for="(item,index) in historyList"
           :key="index">
        <div class="history-item" @click="showHistory(item.name)">
          {{item.name}}
        </div>
      </div>
<!--      <el-table-->
<!--        :data="historyList"-->
<!--        style="width: 100%">-->
<!--        <el-table-column-->
<!--          prop="name">-->
<!--        </el-table-column>-->
<!--      </el-table>-->
    </div>

    <div class="chat-panel">
      <t-chat
        :clear-history="false"
        :reverse="true"
        :text-loading="loading"
        :data=chatMessages>
        <!-- eslint-disable vue/no-unused-vars -->
        <template #name="{ item, index }">
          {{ item.name }}
        </template>
        <template #avatar="{ item, index }">
          <t-avatar size="large" shape="circle" :image="item.avatar" />
        </template>
        <template #datetime="{ item, index }">
          {{ item.datetime }}
        </template>
        <template #content="{ item, index }">
          <t-chat-content :content="item.content" style="text-align: left"/>
        </template>
        <template #footer>
          <div style="display: flex;flex-direction: row;">
            <t-chat-input :stop-disabled="isStreamLoad" @send="inputEnter" @stop="handleStop"></t-chat-input>

            <el-upload
              class="upload-demo"
              action="http://localhost:8000/upload/files"
              :on-change="handleUploadFileChange"
              :on-success="handleUploadSuccess">
              <el-icon style="margin: 3vh 0vh 0vh 2vh" :size="30"><UploadFilled /></el-icon>
<!--              <el-button type="primary" round style="margin: 3vh 0vh 0vh 2vh">文件</el-button>-->
            </el-upload>
          </div>
        </template>
      </t-chat>
    </div>

    <div class="reference-panel">
      <div class="reference-title" v-show="referenceNum !== 0">
        参考文献 {{referenceNum}}
      </div>

      <div class="reference-list" v-for="(item,index) in referenceList"
           :key="index">
        <div class="reference-item" @click="showReferenceDialog(item.name)">
          <div class="reference-title">[{{item.id}}] {{ item.name }}</div>
          <div class="reference-content">{{item.content}}</div>
        </div>
      </div>
    </div>

    <div v-if="isShowReferenceDialog" class="modal-overlay" @click.self="closeReferenceDialog">
          <div class="modal-content">
            <div class="modal-header">
              <h2>{{ chosenReferenceName }}</h2>
              <button class="close-btn" @click="closeReferenceDialog">×</button>
            </div>
            <div class="chat-body">
              <div class="message-content" id="referenceFile">
                <vue-json-pretty
                  :data="referenceContent"
                  :show-line="true"
                  :show-double-quotes="true"
                  highlight-mouseover-node
                />
              </div>
            </div>
          </div>
        </div>
  </div>
</template>
<script setup lang="ts">
import {onMounted, ref} from 'vue';
import axios from "axios";
import VueJsonPretty from "vue-json-pretty";
interface MessageItem {
  avatar: string,
  name: string,
  datetime: string,
  content: string,
  role: string,
}

const isChat = ref(false)
const historyList = ref()
const baseurl = ref('http://127.0.0.1:8000')
const loading = ref(false);
const isStreamLoad = ref(false);
const chatMessages = ref<MessageItem[]>([
      {
        avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png',
        name: 'AI',
        datetime: '今天16:38',
        content: '我是故障分析小助手，有什么我可以帮助您的呢？',
        role: 'assistant',
      },
      // {
      //   avatar: 'https://tdesign.gtimg.com/site/avatar.jpg',
      //   name: '自己',
      //   datetime: '今天16:38',
      //   content: '南极的自动提款机叫什么名字？',
      //   role: 'user',
      // },
    ]);
const originChatMessages = ref<MessageItem[]>([
  {
      avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png',
      name: 'AI',
      datetime: '今天16:38',
      content: '我是故障分析小助手，有什么我可以帮助您的呢？',
      role: 'assistant',
  },
])
const referenceNum = ref(0)
interface ReferenceItem {
  id: string,
  content: string,
  name: string
}
const referenceList = ref<ReferenceItem[]>()

const handleStop = function () {
  isStreamLoad.value = false;
};
const createUserMessage = function (message: string) {
  let userMessage = {
    avatar: 'https://tdesign.gtimg.com/site/avatar.jpg',
    name: '用户',
    datetime: '今天16:38',
    content: message,
    role: 'user',
  }

  chatMessages.value.unshift(userMessage)
};
const createAIMessage = function() {
  let aiMessage = {
    avatar: 'https://tdesign.gtimg.com/site/chat-avatar.png',
    name: 'AI',
    datetime: '今天16:38',
    content: '',
    role: 'assistant',
  }

  chatMessages.value.unshift(aiMessage)
};

const clearMessages = function () {
  chatMessages.value = originChatMessages.value
}
const sendMessage = async function(message: string) {
  isChat.value = true
  createUserMessage(message)
  createAIMessage()
  try {
    // 3. 发起流式请求
    const response = await fetch(baseurl.value + '/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: message,
        filename: uploadFileName.value
      })
    });

    // 4. 检查响应是否为流式
    if (!response.body) {
      console.log('sss')
    } else {
      console.log('success')

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      let isDone = false;
      while (!isDone) {
        const { value, done } = await reader.read();
        isDone = done
        if (done) break

        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        console.log(fullText)
        chatMessages.value[0].content = fullText;
      }

      console.log('AI响应完成');
      const getReferenceList = function () {
        axios.get(baseurl.value + '/getReferenceList')
            .then(res => {
              referenceList.value = res.data.data
              referenceNum.value = res.data.num
            })
      }
      getReferenceList()

      isChosenFile.value = false
      uploadFileName.value = ''
    }
  } catch (error) {
    console.error('流式请求失败:', error);
  }
    // 创建EventSource连接
  // const eventSource = new EventSource(baseurl.value + `/chatSSE/prompt=${message}`);
  // let fullText = '';
  //
  // // 处理消息事件
  // eventSource.onmessage = (event) => {
  //   for (chunk in event.data) {
  //     console.log(event.data)
  //     const chunk = event.data.content;
  //     fullText += chunk;
  //     chatMessages.value[0].content = fullText
  //   }
  // };

  // // 处理错误
  // eventSource.onerror = (error) => {
  //   console.error('SSE连接错误:', error);
  //   eventSource.close();
  // };
  //
  // // 处理自定义事件（如果后端发送）
  // eventSource.addEventListener('complete', () => {
  //   console.log('AI响应完成');
  //   eventSource.close();
  // });
};
const inputEnter = function (inputValue: string) {
  sendMessage(inputValue)
};

const getHistory = function () {
  axios.get(baseurl.value + '/getHistory')
      .then(res => {
        console.log(res)
        historyList.value = res.data.data
      })
};

const showHistory = function (historyName: string) {
  console.log(historyName)
  axios.post(baseurl.value + '/getHistoryMessages', {
    name: historyName
  }).then(res => {
        chatMessages.value = res.data.messages
      })
};

const createHistory = function () {
  if (isChat.value) {
    isChat.value = false
    axios.post(baseurl.value + '/createHistory', {
      create_time: '',
      messages: chatMessages.value
    }).then(res => {
      console.log(res.data.status)
      referenceList.value = []
      referenceNum.value = 0
      clearMessages()
      getHistory()
    })
  }
};

const chosenReferenceName = ref('')
const referenceContent = ref()
const isShowReferenceDialog = ref(false)
const showReferenceDialog = function (filename: string) {
  console.log(filename)
  chosenReferenceName.value = filename
  axios.post(
      baseurl.value + '/getReferenceFile', {
        filename: chosenReferenceName.value
      }
  ).then(res => {
    referenceContent.value = res.data.data
  })
  isShowReferenceDialog.value = true
};
const closeReferenceDialog = function () {
  isShowReferenceDialog.value = false
};

const isChosenFile = ref(false)
const uploadFileName = ref('')
const handleUploadSuccess = function () {

};

const handleUploadFileChange = function (file: any) {
      isChosenFile.value = true
      uploadFileName.value = file.name
};

onMounted(() => {
  getHistory();
})
</script>

<style>
.main-container {
  display: flex;
  height: 98vh;
  margin-top: -4vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 左侧历史面板样式 */
.history-panel {
  width: 30vh;
  background-color: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.history-header {
  padding: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.history-header h2 {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.new-chat-btn {
  background-color: #0052d9;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  width: 100%;
  font-weight: 500;
  transition: background-color 0.2s;
  font-size: 14px;
}

.new-chat-btn:hover {
  background-color: #0046b8;
}

.history-list {
  overflow-y: auto;
  padding: 10px;
  text-align: left;
  padding-left: 2vh;
}

.history-item {
  overflow: hidden;         /* 隐藏溢出内容 */
  text-overflow: ellipsis;  /* 溢出部分显示省略号 */
}



.chat-panel {
  width: 80vh;
  margin-left: 15vh;
}

.reference-panel {
  width: 50vh;
  margin-left: 15vh;
  border-left: 1px solid #E5E7EB;
  border-right: 1px solid #E5E7EB;

  display: flex;
  flex-direction: column;
  overflow-y: auto;

  .reference-title {
    margin-top: 10px;
    font-size: 18px;
    font-weight: 600;
    color: #333;
    text-align: center;
  }

  .reference-list {
    margin-left: 4vh;
    .reference-item {
      .reference-title {
        height: 3vh;
        font-size: 24px;
        font-weight: 600;
        color: #333;
        text-align: left;
        overflow: hidden;         /* 隐藏溢出内容 */
        text-overflow: ellipsis;  /* 溢出部分显示省略号 */
      }
      .reference-content {
        height: 6vh;
        font-size: 16px;
        font-weight: 600;
        color: #E5E7EB;
        text-align: left;
        overflow: hidden;         /* 隐藏溢出内容 */
        text-overflow: ellipsis;  /* 溢出部分显示省略号 */
      }
    }
  }
}
</style>
