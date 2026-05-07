<template>
  <div class="chat-container">
    <el-card class="chat-card">
      <template #header>
        <div class="chat-header">
          <span>智能客服</span>
          <el-button text @click="resetSession">
            <el-icon><Refresh /></el-icon>
            新会话
          </el-button>
        </div>
      </template>
      
      <div class="chat-messages" ref="messagesRef">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><ChatDotRound /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.citations?.length" class="citations">
              <div class="citation-title">参考来源:</div>
              <div
                v-for="(cite, i) in msg.citations"
                :key="i"
                class="citation-item"
              >
                {{ cite.document_title }}
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="message assistant">
          <div class="message-avatar">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="请输入您的问题，按 Enter 发送..."
          @keyup.enter="sendMessage"
          :disabled="loading"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="sendMessage"
        >
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { chatQuery, resetChatSession } from '@/api/chat'
import { ElMessage } from 'element-plus'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: any[]
}

const messagesRef = ref<HTMLElement>()
const inputMessage = ref('')
const loading = ref(false)
const sessionId = ref('')
const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '您好！我是 TS_ERP 智能助手，可以帮您查询客户、订单、库存、财务等信息，也可以回答关于公司制度流程的问题。请问有什么可以帮您？'
  }
])

async function sendMessage() {
  const content = inputMessage.value.trim()
  if (!content || loading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content
  })
  
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  
  try {
    const res = await chatQuery({
      message: content,
      session_id: sessionId.value || undefined
    })
    
    messages.value.push({
      role: 'assistant',
      content: res.answer,
      citations: res.citations
    })
    
    sessionId.value = res.session_id
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后重试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function resetSession() {
  if (sessionId.value) {
    await resetChatSession(sessionId.value)
  }
  messages.value = [
    {
      role: 'assistant',
      content: '您好！我是 TS_ERP 智能助手，可以帮您查询客户、订单、库存、财务等信息，也可以回答关于公司制度流程的问题。请问有什么可以帮您？'
    }
  ]
  sessionId.value = ''
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function formatMessage(content: string) {
  // 简单的消息格式化
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style lang="scss" scoped>
.chat-container {
  height: calc(100vh - 140px);
  
  .chat-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    :deep(.el-card__body) {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 0;
      overflow: hidden;
    }
  }
  
  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    
    .message {
      display: flex;
      margin-bottom: 20px;
      
      &.user {
        flex-direction: row-reverse;
        
        .message-content {
          align-items: flex-end;
        }
        
        .message-text {
          background-color: #409EFF;
          color: #fff;
        }
      }
      
      .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #f0f2f5;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        margin: 0 10px;
      }
      
      .message-content {
        display: flex;
        flex-direction: column;
        max-width: 70%;
        
        .message-text {
          background-color: #f0f2f5;
          padding: 12px 16px;
          border-radius: 8px;
          line-height: 1.6;
        }
        
        .citations {
          margin-top: 8px;
          font-size: 12px;
          color: #909399;
          
          .citation-item {
            padding: 4px 8px;
            background-color: #f0f2f5;
            border-radius: 4px;
            margin-top: 4px;
          }
        }
      }
    }
    
    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 12px 16px;
      background-color: #f0f2f5;
      border-radius: 8px;
      
      span {
        width: 8px;
        height: 8px;
        background-color: #909399;
        border-radius: 50%;
        animation: typing 1.4s infinite;
        
        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
      }
    }
  }
  
  .chat-input {
    display: flex;
    gap: 12px;
    padding: 16px;
    border-top: 1px solid #e4e7ed;
    
    .el-textarea {
      flex: 1;
    }
  }
}

@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-4px); opacity: 1; }
}
</style>
