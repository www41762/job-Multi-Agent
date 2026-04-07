<template>
  <div class="home-layout">
    <!-- 左侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>🤖 智能求职助手</h2>
        <p class="subtitle">多Agent协作系统</p>
      </div>
      
      <!-- 新建会话 -->
      <el-button type="primary" class="new-session-btn" @click="handleNewSession">
        <el-icon><Plus /></el-icon> 新建会话
      </el-button>

      <!-- 会话列表 -->
      <div class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.session_id"
          :class="['session-item', { active: s.session_id === store.sessionId }]"
          @click="store.switchSession(s.session_id)"
        >
          <div class="session-info">
            <span class="session-id">💬 {{ s.session_id }}</span>
            <span v-if="s.has_analysis" class="badge analysis">已分析</span>
          </div>
          <span class="chat-count">{{ s.chat_count }}条消息</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <p>基于 LangGraph + Vue3</p>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <main class="main-area">
      <!-- 顶部输入区 -->
      <div class="input-panel" v-show="showInputPanel">
        <div class="input-panel-header">
          <h3>📋 求职分析</h3>
          <el-button text @click="showInputPanel = false">
            <el-icon><ArrowUp /></el-icon> 收起
          </el-button>
        </div>

        <div class="input-grid">
          <!-- JD输入 -->
          <div class="input-block">
            <label>📄 粘贴招聘JD文本</label>
            <el-input
              v-model="jdText"
              type="textarea"
              :rows="6"
              placeholder="请粘贴完整的招聘JD文本，包含岗位名称、职责、要求等..."
              resize="vertical"
            />
          </div>

          <!-- 简历上传 -->
          <div class="input-block">
            <label>📎 上传简历</label>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".pdf"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              drag
              class="resume-upload"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽PDF简历到这里，或<em>点击上传</em></div>
            </el-upload>
            <p class="or-text">或者直接粘贴简历文本：</p>
            <el-input
              v-model="resumeText"
              type="textarea"
              :rows="4"
              placeholder="粘贴简历文本内容..."
              resize="vertical"
            />
          </div>
        </div>

        <div class="input-actions">
          <el-button
            type="primary"
            size="large"
            :loading="store.isAnalyzing"
            @click="handleAnalyze"
            :disabled="!jdText || (!resumeFile && !resumeText)"
          >
            <el-icon><MagicStick /></el-icon>
            {{ store.isAnalyzing ? '分析中...' : '🚀 开始全流程分析' }}
          </el-button>
        </div>
      </div>

      <!-- 展开按钮 -->
      <div v-show="!showInputPanel" class="expand-bar" @click="showInputPanel = true">
        <el-icon><ArrowDown /></el-icon> 展开分析面板
      </div>

      <!-- 聊天区域 -->
      <div class="chat-area" ref="chatAreaRef">
        <div class="chat-messages" ref="messagesRef">
          <!-- 欢迎消息 -->
          <div v-if="store.chatHistory.length === 0 && !streamContent" class="welcome-msg">
            <div class="welcome-icon">🤖</div>
            <h3>欢迎使用多Agent智能求职助手！</h3>
            <p>我可以帮你：</p>
            <div class="feature-grid">
              <div class="feature-card" @click="quickAction('分析JD')">
                <span class="emoji">📋</span>
                <span>解析职位描述</span>
              </div>
              <div class="feature-card" @click="quickAction('优化简历')">
                <span class="emoji">✍️</span>
                <span>优化简历内容</span>
              </div>
              <div class="feature-card" @click="quickAction('匹配分析')">
                <span class="emoji">🔗</span>
                <span>简历JD匹配</span>
              </div>
              <div class="feature-card" @click="quickAction('面试准备')">
                <span class="emoji">🎯</span>
                <span>面试题准备</span>
              </div>
            </div>
            <p class="hint">👆 在上方上传简历+粘贴JD进行全流程分析，或直接在下方聊天框提问</p>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, idx) in store.chatHistory"
            :key="idx"
            :class="['message', msg.role]"
          >
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMd(msg.content)"></div>
              <div v-else class="user-text">{{ msg.content }}</div>
            </div>
          </div>

          <!-- 流式输出中 -->
          <div v-if="streamContent" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
              <div class="markdown-body" v-html="renderMd(streamContent)"></div>
              <span class="typing-cursor" v-if="isStreaming">▊</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入框 -->
      <div class="chat-input-area">
        <div class="chat-input-wrapper">
          <el-input
            v-model="chatInput"
            placeholder="输入消息，与AI助手对话...（支持追问分析结果）"
            @keydown.enter.prevent="handleSendChat"
            :disabled="isStreaming"
            size="large"
          >
            <template #append>
              <el-button
                type="primary"
                @click="handleSendChat"
                :disabled="!chatInput.trim() || isStreaming"
                :loading="isStreaming"
              >
                发送
              </el-button>
            </template>
          </el-input>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useSessionStore } from '../stores/session'
import { renderMarkdown } from '../utils/markdown'
import api from '../utils/api'
import { ElMessage } from 'element-plus'

const store = useSessionStore()
const chatAreaRef = ref(null)
const messagesRef = ref(null)
const uploadRef = ref(null)

// 表单数据
const jdText = ref('')
const resumeFile = ref(null)
const resumeText = ref('')
const chatInput = ref('')
const showInputPanel = ref(true)

// 流式输出
const streamContent = ref('')
const isStreaming = ref(false)
let currentController = null

// 渲染markdown
function renderMd(text) {
  return renderMarkdown(text)
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 监听消息变化自动滚动
watch(() => store.chatHistory.length, scrollToBottom)
watch(streamContent, scrollToBottom)

// 初始化
onMounted(async () => {
  await store.loadSessions()
  if (!store.sessionId) {
    await store.createSession()
  }
  await store.loadHistory()
  await store.loadSessions()
})

// 新建会话
async function handleNewSession() {
  await store.createSession()
  await store.loadSessions()
  jdText.value = ''
  resumeFile.value = null
  resumeText.value = ''
  showInputPanel.value = true
  ElMessage.success('新会话已创建')
}

// 文件选择
function handleFileChange(file) {
  resumeFile.value = file.raw
}
function handleFileRemove() {
  resumeFile.value = null
}

// 开始全流程分析
async function handleAnalyze() {
  if (!store.sessionId) {
    await store.createSession()
  }

  store.isAnalyzing = true
  isStreaming.value = true
  streamContent.value = ''
  showInputPanel.value = false

  const formData = new FormData()
  formData.append('session_id', store.sessionId)
  formData.append('jd_text', jdText.value)
  
  if (resumeFile.value) {
    formData.append('resume_file', resumeFile.value)
  } else if (resumeText.value) {
    formData.append('resume_text', resumeText.value)
  }

  currentController = api.analyzeStream(
    formData,
    // onChunk
    (data) => {
      streamContent.value += data
    },
    // onDone
    () => {
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
      store.isAnalyzing = false
      ElMessage.success('分析完成！')
      store.loadSessions()
    },
    // onError
    (err) => {
      streamContent.value += `\n\n❌ 错误: ${err}`
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
      store.isAnalyzing = false
      ElMessage.error('分析过程出错')
    }
  )
}

// 发送聊天消息
async function handleSendChat() {
  const msg = chatInput.value.trim()
  if (!msg || isStreaming.value) return

  if (!store.sessionId) {
    await store.createSession()
  }

  store.addMessage('user', msg)
  chatInput.value = ''
  isStreaming.value = true
  streamContent.value = ''

  currentController = api.chatStream(
    store.sessionId,
    msg,
    // onChunk
    (data) => {
      streamContent.value += data
    },
    // onDone
    () => {
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
    },
    // onError
    (err) => {
      streamContent.value += `\n\n❌ 错误: ${err}`
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
    }
  )
}

// 快捷操作
function quickAction(action) {
  chatInput.value = `请帮我${action}`
  showInputPanel.value = true
}
</script>

<style lang="scss" scoped>
.home-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ==================== 左侧边栏 ==================== */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #16213e;

  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    
    h2 {
      font-size: 18px;
      margin-bottom: 4px;
    }
    .subtitle {
      font-size: 12px;
      color: rgba(255,255,255,0.5);
    }
  }

  .new-session-btn {
    margin: 16px;
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 12px;

    .session-item {
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 4px;
      cursor: pointer;
      transition: background 0.2s;

      &:hover {
        background: rgba(255,255,255,0.08);
      }
      &.active {
        background: rgba(64, 158, 255, 0.2);
        border: 1px solid rgba(64, 158, 255, 0.4);
      }

      .session-info {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;

        .session-id {
          font-size: 14px;
        }
        .badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 10px;
          background: #67c23a;
          color: #fff;
        }
      }
      .chat-count {
        font-size: 12px;
        color: rgba(255,255,255,0.4);
      }
    }
  }

  .sidebar-footer {
    padding: 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
    font-size: 12px;
    color: rgba(255,255,255,0.3);
    text-align: center;
  }
}

/* ==================== 右侧主区域 ==================== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f7f8fa;
}

/* 输入面板 */
.input-panel {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
  flex-shrink: 0;
  max-height: 50vh;
  overflow-y: auto;

  .input-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    h3 { font-size: 16px; }
  }

  .input-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .input-block {
    label {
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
      font-size: 14px;
    }
    .or-text {
      font-size: 12px;
      color: #999;
      margin: 8px 0;
    }
  }

  .resume-upload {
    width: 100%;
    .upload-icon {
      font-size: 40px;
      color: #c0c4cc;
    }
  }

  .input-actions {
    margin-top: 16px;
    text-align: center;
  }
}

.expand-bar {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 8px;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
  color: #409eff;
  flex-shrink: 0;

  &:hover {
    background: #f0f7ff;
  }
}

/* 聊天区域 */
.chat-area {
  flex: 1;
  overflow: hidden;

  .chat-messages {
    height: 100%;
    overflow-y: auto;
    padding: 16px 24px;
  }
}

/* 欢迎消息 */
.welcome-msg {
  text-align: center;
  padding: 40px 20px;

  .welcome-icon {
    font-size: 64px;
    margin-bottom: 16px;
  }
  h3 {
    font-size: 20px;
    margin-bottom: 8px;
    color: #333;
  }
  p {
    color: #666;
    margin-bottom: 16px;
  }
  .hint {
    font-size: 13px;
    color: #999;
    margin-top: 24px;
  }

  .feature-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    max-width: 600px;
    margin: 0 auto;

    .feature-card {
      background: #fff;
      border: 1px solid #e8e8e8;
      border-radius: 12px;
      padding: 16px 12px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;

      &:hover {
        border-color: #409eff;
        box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
        transform: translateY(-2px);
      }

      .emoji {
        font-size: 28px;
      }
      span:last-child {
        font-size: 13px;
        color: #333;
      }
    }
  }
}

/* 消息气泡 */
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;

  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
    background: #f0f0f0;
  }

  .message-content {
    flex: 1;
    min-width: 0;
    max-width: 80%;

    .user-text {
      background: #409eff;
      color: #fff;
      padding: 10px 16px;
      border-radius: 12px 12px 2px 12px;
      font-size: 14px;
      line-height: 1.6;
      display: inline-block;
    }

    .markdown-body {
      background: #fff;
      padding: 12px 16px;
      border-radius: 2px 12px 12px 12px;
      border: 1px solid #e8e8e8;
    }
  }

  &.user {
    flex-direction: row-reverse;

    .message-content {
      display: flex;
      justify-content: flex-end;
    }
  }
}

.typing-cursor {
  animation: blink 1s infinite;
  color: #409eff;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 底部输入框 */
.chat-input-area {
  background: #fff;
  border-top: 1px solid #e8e8e8;
  padding: 12px 24px;
  flex-shrink: 0;

  .chat-input-wrapper {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>
