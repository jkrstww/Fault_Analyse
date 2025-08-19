<template>
    <div class="chat">
      <div
        v-for = "(msg,index) in messages"
        :key="index"
        :class="{
          'user-message': msg.role === 'user',
          'system-message': msg.role === 'system'
        }">
        <div>{{msg.content}}</div>
        <div>{{msg.time}}</div>
      </div>
    </div>
</template>

<script>
import axios from 'axios'
export default {
  name: "HistoryRecord",
  data() {
    return {
      baseurl: "http://localhost:5000",
      filename: this.$route.params.filename,
      messages: []
    };
  },
  methods: {
    getHistoryRecord() {
      axios.get(this.baseurl+'/getHistoryRecord/'+this.filename)
          .then(res => {
            this.messages = res.data.messages
            console.log(this.messages)
          })
    }
  },
  mounted() {
    console.log("ss")
    this.filename = this.$route.query.filename
    this.getHistoryRecord()
  },
  watch: {
    // 当路由参数变化时，更新数据
    '$route.query.filename'(filename) {
      this.filename = filename;
      // 可以在这里调用API获取文件内容
      console.log("sss")
    }
  }
};
</script>

<style>
.chat {
  display: flex;
  flex-direction: column;
  height: 60vh;
  overflow-y: auto;

  .user-message {
    width: 50vh;
    margin-left: 38vh;
    margin-top: 4vh;
    background-color: bisque;
  }

  .system-message {
    width: 50vh;
    margin-top: 4vh;
    background-color: beige;
  }
}
</style>