<template>
  <div class="container">
    <div class="header">
      <el-button>登录</el-button>
      <el-button>帮助</el-button>
    </div>

    <div class="main">
      <div class="lside">
        <div class="title">历史诊断记录</div>
        <div class="history-messages">
          <div v-for="(filename,index) in historyRecordList"
               :key="index"
               class="message">
<!--            <router-link :to="`/historyRecord/${filename}`">{{ filename }}</router-link>-->
            <el-button
                @click="showRecordDialog(filename)">{{filename}}</el-button>
          </div>
        </div>

        <!-- 弹窗 -->
        <div v-if="isShowRecordDialog" class="modal-overlay" @click.self="closeRecordDialog">
          <div class="modal-content">
            <div class="modal-header">
              <h2>对话记录 - {{ chosenRecordName }}</h2>
              <button class="close-btn" @click="closeRecordDialog">×</button>
            </div>
            <div class="chat-body">
              <div
                v-for="(msg, index) in historyRecord"
                :key="index"
                :class="['message', msg.role === 'user' ? 'user-message' : 'system-message']"
              >
                <div class="message-content">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="midside">
        <div class="chat">
          <div
            v-for = "(msg,index) in messages"
            :key="index"
            :class="{
              'user_message': msg.role === 'user',
              'system_message': msg.role === 'system'
            }">
            <div>{{msg.content}}</div>
            <div>{{msg.time}}</div>
          </div>
        </div>

        <div class="userinput">
          <div class="augmentChat">
            <el-upload
              class="upload-demo"
              action="http://localhost:5000/upload/images"
              :on-change="handleUploadImgChange"
              :on-success="handleUploadSuccess">
              <el-button type="primary" round>图片</el-button>
            </el-upload>

            <el-upload
              class="upload-demo"
              action="http://localhost:5000/upload/files"
              :on-change="handleUploadFileChange"
              :on-success="handleUploadSuccess">
              <el-button type="primary" round>文件</el-button>
            </el-upload>

            <el-button type="primary" round>联网搜索</el-button>
          </div>

          <div class="inputBox">
            <el-input
              v-model="userinput"
              type="textarea"
              placeholder="输入您的问题..."
            />
            <el-button @click="sendMessages">发送</el-button>
            <el-button @click="finishChat">开始新的对话</el-button>
          </div>
        </div>
      </div>

      <div class="rside">
        <div class="graph">

        </div>

        <div class="references">
          <div class="title">参考文献</div>
          <div
              v-for="(filename, index) in referenceList"
              :key="index">
            <div @click="showReferenceDialog(filename)">[{{index+1}}] {{filename}}</div>
          </div>
        </div>

        <div class="recommend">
          <div class="title">推荐文献</div>
          <div
              v-for="(filename, index) in recommendList"
              :key="index">
            <div @click="showRecommendDialog(filename)">[{{index+1}}] {{filename}}</div>
          </div>
        </div>

        <!-- 弹窗 -->
        <div v-if="isShowRecommendDialog" class="modal-overlay" @click.self="closeRecommendDialog">
          <div class="modal-content">
            <div class="modal-header">
              <h2>{{ chosenRecommendName }}</h2>
              <button class="close-btn" @click="closeRecommendDialog">×</button>
            </div>
            <div class="chat-body">
              <div class="message-content">{{ recommendContent }}</div>
            </div>
          </div>
        </div>

        <!-- 弹窗 -->
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
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';

export default {
  name: "MainPart",
  components: {
    VueJsonPretty,
  },
  data () {
    return {
      baseurl: 'http://localhost:5000',
      userinput: "",
      messages: [
        // {
        //   "role": "user",
        //   "content": "你是谁",
        //   "time": 1112
        // },
        // {
        //   "role": "system",
        //   "content": "不知道",
        //   "time": 222
        // }
      ],
      historyRecordList: [],
      historyRecord: [],
      referenceList: [],
      referenceFile: '',
      recommendList: [],
      referenceContent: '',
      recommendContent: '',
      chosenRecordName: '',
      chosenReferenceName: '',
      chosenRecommendName: '',
      isShowRecordDialog: false,
      isShowReferenceDialog: false,
      isShowRecommendDialog: false,
      isChosenFile: false,
      isChosenImg: false,
      uploadFileName: '',
      uploadImgName: ''
    }
  },
  methods: {
    sendMessages() {
      const now = new Date()

      const year = now.getFullYear(); // 年份，如 2024
      const month = now.getMonth() + 1; // 月份，注意：0-11，所以需要 +1
      const day = now.getDate(); // 日期，如 28
      const hours = now.getHours(); // 小时，0-23
      const minutes = now.getMinutes(); // 分钟，0-59
      const seconds = now.getSeconds(); // 秒，0-59

      const now_time = year+'-'+month+'-'+day+' '+hours+':'+minutes+':'+seconds

      this.messages.push(
          {
            "role": "user",
            "content": this.userinput,
            "time": now_time
          }
      )

      const message = this.userinput
      this.userinput = ''

      axios.post(this.baseurl + '/chat',{
        message: message,
        time: now_time,
        isChosenFile: this.isChosenFile,
        isChosenImg: this.isChosenImg,
        filename: this.uploadFileName,
        imagename: this.uploadImgName,
      }).then(res => {
        // this.getRecommendList()
        // this.getReferenceList()
        this.messages.push(
            {
              "role": "system",
              "content": res.data.reply,
              "time": res.data.time
            }
        )
        this.recommendList = res.data.recommend_list
        this.referenceList = res.data.reference_list
        this.isChosenFile = false
        this.isChosenImg = false
      })
    },
    getRecommendList() {
      axios.get(
          this.baseurl + '/getRecommendList'
      ).then(res => {
        this.recommendList = res.data.recommendList
      })
    },
    getReferenceList() {
      axios.get(
          this.baseurl + '/getReferenceList'
      ).then(res => {
        this.referenceList = res.data.referenceList
      })
    },
    // getRecommendFile(filename) {
    //   axios.get(
    //       this.baseurl + '/getRecommendFile/' + filename
    //   ).then(res => {
    //     this.recommendFile = res.data.fileContent
    //   })
    // },
    // getReferenceFile(filename) {
    //   axios.get(
    //       this.baseurl + '/getReferenceFile/' + filename
    //   ).then(res => {
    //     this.referenceFile = res.data.fileContent
    //   })
    // },
    finishChat() {
      this.messages = []

      axios.get(this.baseurl + '/finishChat').then(res => {
        console.log(res.data.status)
      })
    },
    getHistoryRecordList() {
      axios.get(this.baseurl+'/getHistoryRecordList')
          .then(res => {
            this.historyRecordList = res.data.historyRecordList
          })
    },
    getHistoryRecord(filename) {
      axios.get(this.baseurl+'/getHistoryRecord/'+filename)
          .then(res => {
            this.historyRecord = res.data.messages
          })
    },
    goToRecordDetails(filename) {
      console.log(filename)
      this.$router.push({
        path: '/historyRecord',
        query: {
          filename: filename
        }
      })
    },
    showRecordDialog(filename) {
      this.chosenRecordName = filename
      this.getHistoryRecord(filename)
      this.isShowRecordDialog = true
      console.log(this.historyRecord)
    },
    closeRecordDialog() {
      this.isShowRecordDialog = false
    },
    showReferenceDialog(filename) {
      this.chosenReferenceName = filename
      axios.get(
          this.baseurl + '/getReferenceFile/' + this.chosenReferenceName
      ).then(res => {
        this.referenceContent = res.data.fileContent
      })
      this.isShowReferenceDialog = true
    },
    closeReferenceDialog() {
      this.isShowReferenceDialog = false
    },
    showRecommendDialog(filename) {
      this.chosenRecommendName = filename
      axios.get(
          this.baseurl + '/getRecommendFile/' + this.chosenRecommendName
      ).then(res => {
        this.recommendContent = res.data.fileContent
      })
      this.isShowRecommendDialog = true
    },
    closeRecommendDialog() {
      this.isShowRecommendDialog = false
    },
    handleUploadSuccess() {
      this.$message({
        message: '上传成功',
        type: 'success'
      })
    },
    handleUploadFileChange(file) {
      this.isChosenFile = true
      this.uploadFileName = file.name
    },
    handleUploadImgChange(file) {
      this.isChosenImg = true
      this.uploadImgName = file.name
    },
  },
  mounted() {
    this.getHistoryRecordList()
  }
}
</script>

<style>
  .container {
    display: flex;
    flex-direction: column;
    height: 100%;

    .header {
      height: 6vh;
      border-bottom: 1px solid black;
    }
  }
  .main {
    display: flex;
    flex-direction: row;
    height: 90vh;
  }
  .lside {
    width: 40vh;
    border-right: 1px solid black;

    .title {
      text-align: center;
      color: #111827;
      height: 3vh;
    }
  }
  .history-messages {
    overflow-y: auto;
    height: 88vh;

    .message {
      margin-top: 1vh;
      margin-left: 1vh;

      button {
        width: 32vh;
        height: 3vh;
        text-align: left;
        font-size: 12px;
      }
    }
  }
  .midside {
    width: 90vh;
    border-right: 1px solid black;
  }
  .chat {
    display: flex;
    flex-direction: column;
    height: 60vh;
    overflow-y: auto;

    .user_message {
      width: 50vh;
      margin-left: 37vh;
      margin-top: 4vh;
      border: 2px solid black;
      border-radius: 10px;
      padding-left: 2vh;
      padding-top: 1vh;
    }

    .system_message {
      width: 50vh;
      margin-top: 4vh;
      background-color: #F9FAFB;
      border: 2px solid black;
      border-radius: 10px;
      padding-left: 2vh;
      padding-top: 1vh;
    }
  }
  .userinput {
    display: flex;
    flex-direction: column;
    margin-top: 5vh;
    border-top: 1px solid black;

    .augmentChat {
      display: flex;
      flex-direction: row;
      margin-top: 2vh;
      margin-left: 2vh;
    }

    .inputBox {
      display: flex;
      flex-direction: row;
      margin-top: 2vh;
      margin-left: 2vh;
    }
  }
  .rside {
    display: flex;
    flex-direction: column;
    width: 50vh;
  }
  .graph {
    height: 30vh;

    img {
      width: 100%;
      height: auto;
    }
  }
  .references {
    height: 30vh;
    border-top: 1px solid black;
    overflow-y: auto;

    .title {
      text-align: center;
      margin-top: 1vh;
    }
  }
  .recommend {
    height: 30vh;
    border-top: 1px solid black;
    overflow-y: auto;

    .title {
      text-align: center;
      margin-top: 1vh;
    }
  }






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