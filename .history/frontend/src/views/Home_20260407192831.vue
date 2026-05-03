<template>
  <div class="app-shell">
    <!-- ==================== 左侧边栏 ==================== -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4Z"/><circle cx="12" cy="15" r="2"/></svg>
        </div>
        <div class="brand-text">
          <h1>JobMind AI</h1>
          <span class="brand-tag">Multi-Agent · LangGraph</span>
        </div>
      </div>

      <button class="btn-new-session" @click="handleNewSession">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建会话
      </button>

      <div class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.session_id"
          :class="['session-card', { active: s.session_id === store.sessionId }]"
          @click="store.switchSession(s.session_id)"
        >
          <div class="session-card-icon">💬</div>
          <div class="session-card-body">
            <span class="session-card-title">会话 {{ s.session_id }}</span>
            <span class="session-card-meta">
              {{ s.chat_count }} 条消息
              <em v-if="s.has_analysis" class="tag-done">✓ 已分析</em>
            </span>
          </div>
        </div>
        <div v-if="store.sessions.length === 0" class="session-empty">
          暂无历史会话
        </div>
      </div>

      <!-- 用户长期画像 -->
      <div class="profile-panel" v-if="userProfile.weaknesses.length || userProfile.strong_skills.length">
        <div class="profile-title">🧠 长期记忆画像</div>
        <div class="profile-section" v-if="userProfile.strong_skills.length">
          <span class="profile-label">💪 优势</span>
          <div class="profile-tags">
            <span class="tag-strength" v-for="s in userProfile.strong_skills.slice(0, 5)" :key="s">{{ s }}</span>
          </div>
        </div>
        <div class="profile-section" v-if="userProfile.weaknesses.length">
          <span class="profile-label">⚠️ 弱项</span>
          <div class="profile-tags">
            <span class="tag-weakness" v-for="w in userProfile.weaknesses.slice(0, 5)" :key="w">{{ w }}</span>
          </div>
        </div>
      </div>

      <div class="sidebar-bottom">
        <div class="tech-badge">⚡ Powered by LangGraph + Vue 3</div>
      </div>
    </aside>

    <!-- ==================== 右侧主区域 ==================== -->
    <main class="main-content">

      <!-- 顶部 Toolbar -->
      <header class="toolbar">
        <div class="toolbar-left">
          <span class="toolbar-title">🎯 智能求职分析</span>
          <span class="toolbar-session" v-if="store.sessionId">ID: {{ store.sessionId }}</span>
        </div>
        <div class="toolbar-right">
          <button class="btn-icon" @click="showInputPanel = !showInputPanel" :title="showInputPanel ? '收起面板' : '展开面板'">
            <svg v-if="showInputPanel" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
        </div>
      </header>

      <!-- 输入面板（可折叠） -->
      <transition name="slide">
        <section class="input-panel" v-show="showInputPanel">
          <div class="input-panel-grid">
            <!-- JD 输入卡片 -->
            <div class="input-card">
              <div class="input-card-header">
                <span class="input-card-icon">📄</span>
                <span class="input-card-label">招聘JD文本</span>
              </div>
              <textarea
                v-model="jdText"
                class="input-textarea"
                rows="5"
                placeholder="粘贴完整的招聘JD，包含岗位名称、职责、要求..."
              ></textarea>
            </div>

            <!-- 简历输入卡片 -->
            <div class="input-card">
              <div class="input-card-header">
                <span class="input-card-icon">📎</span>
                <span class="input-card-label">上传简历</span>
              </div>
              <div
                class="upload-zone"
                @dragover.prevent
                @drop.prevent="handleDrop"
                @click="triggerFileInput"
              >
                <input ref="fileInputRef" type="file" accept=".pdf" hidden @change="handleFileSelect" />
                <div v-if="!resumeFile" class="upload-placeholder">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  <span>拖拽PDF简历到此处，或<em>点击上传</em></span>
                </div>
                <div v-else class="upload-file-info">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  <span>{{ resumeFileName }}</span>
                  <button class="btn-remove" @click.stop="removeFile">✕</button>
                </div>
              </div>
              <div class="input-divider"><span>或 粘贴文本</span></div>
              <textarea
                v-model="resumeText"
                class="input-textarea small"
                rows="3"
                placeholder="直接粘贴简历文本..."
              ></textarea>
            </div>
          </div>

          <div class="input-actions">
            <button
              class="btn-analyze"
              :class="{ loading: store.isAnalyzing }"
              @click="handleAnalyze"
              :disabled="!jdText || (!resumeFile && !resumeText) || store.isAnalyzing"
            >
              <svg v-if="!store.isAnalyzing" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <span class="spinner" v-if="store.isAnalyzing"></span>
              {{ store.isAnalyzing ? '多Agent协同分析中...' : '🚀 启动全流程分析' }}
            </button>
            <div class="input-hint">系统将自动进行 JD解析 → 简历分析 → 匹配评估 → 简历优化 → 面试题生成</div>
          </div>
        </section>
      </transition>

      <!-- 聊天区域 -->
      <section class="chat-area" ref="chatAreaRef">
        <div class="chat-scroll" ref="messagesRef">

          <!-- 空状态欢迎 -->
          <div v-if="store.chatHistory.length === 0 && !streamContent" class="welcome-hero">
            <div class="welcome-glow"></div>
            <div class="welcome-avatar">🤖</div>
            <h2>Hi，我是你的 AI 求职顾问</h2>
            <p class="welcome-desc">我搭载了 5 个专业 Agent，可以帮你从 JD 解析到面试模拟全覆盖</p>
            <div class="quick-actions">
              <button class="quick-btn" @click="quickAction('帮我解析这个JD的核心要求')">
                <span class="qa-icon">📋</span>解析JD
              </button>
              <button class="quick-btn" @click="quickAction('帮我优化简历，突出技术亮点')">
                <span class="qa-icon">✍️</span>优化简历
              </button>
              <button class="quick-btn" @click="quickAction('分析我的简历和JD匹配度')">
                <span class="qa-icon">🔗</span>匹配分析
              </button>
              <button class="quick-btn" @click="quickAction('针对这个岗位生成面试题')">
                <span class="qa-icon">🎯</span>模拟面试
              </button>
            </div>
            <p class="welcome-tip">💡 在上方上传简历+粘贴JD可进行一键全流程分析</p>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, idx) in store.chatHistory"
            :key="idx"
            :class="['msg-row', msg.role]"
          >
            <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="msg-bubble">
              <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMd(msg.content)"></div>
              <div v-else class="msg-user-text">{{ msg.content }}</div>
            </div>
          </div>

          <!-- 流式输出 -->
          <div v-if="streamContent" class="msg-row assistant">
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble">
              <div class="markdown-body" v-html="renderMd(streamContent)"></div>
              <span class="cursor-blink" v-if="isStreaming">▌</span>
            </div>
          </div>

        </div>
      </section>

      <!-- 底部输入框 -->
      <footer class="chat-footer">
        <div class="chat-input-box">
          <input
            v-model="chatInput"
            type="text"
            class="chat-input"
            placeholder="输入消息，与 AI 助手对话…（支持追问分析结果）"
            @keydown.enter.prevent="handleSendChat"
            :disabled="isStreaming"
          />
          <button
            class="btn-send"
            @click="handleSendChat"
            :disabled="!chatInput.trim() || isStreaming"
          >
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
        <div class="chat-footer-hint">基于 LangGraph 多Agent架构 · 支持 SSE 流式输出 · 长期记忆</div>
      </footer>

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
const fileInputRef = ref(null)

// 表单数据
const jdText = ref('')
const resumeFile = ref(null)
const resumeFileName = ref('')
const resumeText = ref('')
const chatInput = ref('')
const showInputPanel = ref(true)

// 流式输出
const streamContent = ref('')
const isStreaming = ref(false)
let currentController = null

// 用户长期画像
const userProfile = ref({ weaknesses: [], strong_skills: [] })

async function loadUserProfile() {
  try {
    userProfile.value = await api.getUserProfile()
  } catch (e) {
    console.error('加载用户画像失败:', e)
  }
}

function renderMd(text) {
  return renderMarkdown(text)
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(() => store.chatHistory.length, scrollToBottom)
watch(streamContent, scrollToBottom)

onMounted(async () => {
  await store.loadSessions()
  if (!store.sessionId) {
    await store.createSession()
  }
  await store.loadHistory()
  await store.loadSessions()
  await loadUserProfile()
})

// ==================== 会话 ====================
async function handleNewSession() {
  await store.createSession()
  await store.loadSessions()
  jdText.value = ''
  resumeFile.value = null
  resumeFileName.value = ''
  resumeText.value = ''
  showInputPanel.value = true
  ElMessage.success('新会话已创建')
}

// ==================== 文件上传 ====================
function triggerFileInput() {
  fileInputRef.value?.click()
}
function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) {
    resumeFile.value = file
    resumeFileName.value = file.name
  }
}
function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  if (file && file.name.endsWith('.pdf')) {
    resumeFile.value = file
    resumeFileName.value = file.name
  }
}
function removeFile() {
  resumeFile.value = null
  resumeFileName.value = ''
}

// ==================== 分析 ====================
async function handleAnalyze() {
  if (!store.sessionId) await store.createSession()

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
    (data) => { streamContent.value += data },
    () => {
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
      store.isAnalyzing = false
      ElMessage.success('分析完成！')
      store.loadSessions()
      loadUserProfile()  // 刷新长期画像（匹配后自动提取了弱项/优势）
    },
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

// ==================== 聊天 ====================
async function handleSendChat() {
  const msg = chatInput.value.trim()
  if (!msg || isStreaming.value) return
  if (!store.sessionId) await store.createSession()

  store.addMessage('user', msg)
  chatInput.value = ''
  isStreaming.value = true
  streamContent.value = ''

  currentController = api.chatStream(
    store.sessionId,
    msg,
    (data) => { streamContent.value += data },
    () => {
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
    },
    (err) => {
      streamContent.value += `\n\n❌ 错误: ${err}`
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
    }
  )
}

function quickAction(text) {
  chatInput.value = text
  showInputPanel.value = true
}
</script>

<style lang="scss" scoped>
/* ==================== 颜色变量 ==================== */
$sidebar-bg: #0f172a;
$sidebar-hover: #1e293b;
$sidebar-active: #334155;
$primary: #6366f1;
$primary-light: #818cf8;
$primary-glow: rgba(99, 102, 241, 0.25);
$bg-main: #f8fafc;
$bg-card: #ffffff;
$border: #e2e8f0;
$text-primary: #1e293b;
$text-secondary: #64748b;
$text-muted: #94a3b8;
$radius-sm: 8px;
$radius-md: 12px;
$radius-lg: 16px;

/* ==================== 壳 ==================== */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ==================== 侧边栏 ==================== */
.sidebar {
  width: 272px;
  min-width: 272px;
  background: $sidebar-bg;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  user-select: none;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px 18px;
  border-bottom: 1px solid rgba(255,255,255,.06);

  .brand-icon {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: linear-gradient(135deg, $primary, #a78bfa);
    display: flex;
    align-items: center;
    justify-content: center;
    svg { width: 20px; height: 20px; color: #fff; }
  }
  .brand-text {
    h1 { font-size: 17px; font-weight: 700; letter-spacing: -.3px; line-height: 1.2; }
    .brand-tag {
      font-size: 11px;
      color: $text-muted;
      letter-spacing: .2px;
    }
  }
}

.btn-new-session {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 14px 16px 6px;
  padding: 10px 0;
  border: 1.5px dashed rgba(255,255,255,.15);
  border-radius: $radius-sm;
  background: transparent;
  color: #cbd5e1;
  font-size: 13.5px;
  cursor: pointer;
  transition: all .2s;
  svg { width: 16px; height: 16px; }
  &:hover {
    border-color: $primary-light;
    color: $primary-light;
    background: rgba(99,102,241,.08);
  }
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px;
}
.session-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: $radius-sm;
  cursor: pointer;
  margin-bottom: 2px;
  transition: background .15s;

  &:hover { background: $sidebar-hover; }
  &.active {
    background: $sidebar-active;
    box-shadow: inset 3px 0 0 $primary;
  }

  .session-card-icon { font-size: 18px; flex-shrink: 0; }
  .session-card-body {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .session-card-title {
    font-size: 13.5px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .session-card-meta {
    font-size: 11.5px;
    color: $text-muted;
    display: flex;
    align-items: center;
    gap: 6px;
    .tag-done {
      font-style: normal;
      font-size: 10px;
      background: rgba(52, 211, 153, .15);
      color: #34d399;
      padding: 1px 6px;
      border-radius: 20px;
    }
  }
}
.session-empty {
  text-align: center;
  color: $text-muted;
  font-size: 12.5px;
  padding: 32px 0;
}

/* 用户画像面板 */
.profile-panel {
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,.06);
  flex-shrink: 0;

  .profile-title {
    font-size: 12px;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 10px;
  }
  .profile-section {
    margin-bottom: 8px;
  }
  .profile-label {
    font-size: 11px;
    color: $text-muted;
    display: block;
    margin-bottom: 5px;
  }
  .profile-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .tag-strength {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(52, 211, 153, .12);
    color: #34d399;
    white-space: nowrap;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .tag-weakness {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(251, 146, 60, .12);
    color: #fb923c;
    white-space: nowrap;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.sidebar-bottom {
  padding: 14px 16px;
  border-top: 1px solid rgba(255,255,255,.06);
  .tech-badge {
    font-size: 11px;
    color: rgba(255,255,255,.25);
    text-align: center;
  }
}

/* ==================== 主区域 ==================== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: $bg-main;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 52px;
  min-height: 52px;
  background: $bg-card;
  border-bottom: 1px solid $border;

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    .toolbar-title { font-size: 15px; font-weight: 600; color: $text-primary; }
    .toolbar-session {
      font-size: 11.5px;
      color: $text-muted;
      background: #f1f5f9;
      padding: 2px 8px;
      border-radius: 20px;
    }
  }
}
.btn-icon {
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .15s;
  svg { width: 18px; height: 18px; color: $text-secondary; }
  &:hover { background: #f1f5f9; }
}

/* ==================== 输入面板 ==================== */
.slide-enter-active, .slide-leave-active {
  transition: all .28s cubic-bezier(.4,0,.2,1);
  max-height: 500px;
  opacity: 1;
}
.slide-enter-from, .slide-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

.input-panel {
  background: $bg-card;
  border-bottom: 1px solid $border;
  padding: 18px 24px 14px;
  flex-shrink: 0;
  overflow: hidden;
}
.input-panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.input-card {
  background: #f8fafc;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 14px 16px;
  transition: border-color .2s;
  &:focus-within { border-color: $primary-light; }

  .input-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    .input-card-icon { font-size: 16px; }
    .input-card-label { font-size: 13.5px; font-weight: 600; color: $text-primary; }
  }
}
.input-textarea {
  width: 100%;
  border: 1px solid $border;
  border-radius: $radius-sm;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.6;
  color: $text-primary;
  resize: vertical;
  font-family: inherit;
  outline: none;
  background: #fff;
  transition: border-color .2s, box-shadow .2s;
  &:focus {
    border-color: $primary-light;
    box-shadow: 0 0 0 3px $primary-glow;
  }
  &.small { min-height: 60px; }
  &::placeholder { color: $text-muted; }
}

/* Upload zone */
.upload-zone {
  border: 1.5px dashed $border;
  border-radius: $radius-sm;
  padding: 18px;
  text-align: center;
  cursor: pointer;
  transition: border-color .2s, background .2s;

  &:hover {
    border-color: $primary-light;
    background: rgba(99,102,241,.03);
  }
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: $text-muted;
  font-size: 13px;
  svg { width: 32px; height: 32px; color: #cbd5e1; }
  em { color: $primary; cursor: pointer; font-style: normal; }
}
.upload-file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: $primary;
  font-size: 13px;
  svg { width: 20px; height: 20px; }
  .btn-remove {
    width: 20px; height: 20px;
    border: none;
    background: #fee2e2;
    color: #ef4444;
    border-radius: 50%;
    font-size: 11px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    &:hover { background: #fecaca; }
  }
}
.input-divider {
  display: flex;
  align-items: center;
  margin: 10px 0;
  span {
    font-size: 11.5px;
    color: $text-muted;
    padding: 0 10px;
  }
  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: $border;
  }
}

.input-actions {
  margin-top: 14px;
  text-align: center;
}
.btn-analyze {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 36px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, $primary, #a78bfa);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: transform .15s, box-shadow .2s;
  box-shadow: 0 4px 14px $primary-glow;
  svg { width: 18px; height: 18px; }

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,.35);
  }
  &:disabled {
    opacity: .55;
    cursor: not-allowed;
  }
  &.loading {
    pointer-events: none;
  }
}
.spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.input-hint {
  font-size: 12px;
  color: $text-muted;
  margin-top: 10px;
}

/* ==================== 聊天区域 ==================== */
.chat-area {
  flex: 1;
  overflow: hidden;
}
.chat-scroll {
  height: 100%;
  overflow-y: auto;
  padding: 20px 28px;
}

/* 欢迎区 */
.welcome-hero {
  text-align: center;
  padding: 48px 20px 32px;
  position: relative;

  .welcome-glow {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 260px;
    height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,.1) 0%, transparent 70%);
    pointer-events: none;
  }
  .welcome-avatar {
    font-size: 56px;
    margin-bottom: 16px;
    animation: float 3s ease-in-out infinite;
    position: relative;
    z-index: 1;
  }
  h2 {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: 8px;
  }
  .welcome-desc {
    color: $text-secondary;
    font-size: 14px;
    margin-bottom: 28px;
  }
  .welcome-tip {
    font-size: 12.5px;
    color: $text-muted;
    margin-top: 28px;
  }
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.quick-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}
.quick-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 1px solid $border;
  border-radius: 999px;
  background: $bg-card;
  color: $text-primary;
  font-size: 13.5px;
  cursor: pointer;
  transition: all .2s;
  .qa-icon { font-size: 16px; }

  &:hover {
    border-color: $primary-light;
    color: $primary;
    background: rgba(99,102,241,.04);
    box-shadow: 0 2px 8px $primary-glow;
    transform: translateY(-1px);
  }
}

/* ==================== 消息 ==================== */
.msg-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
  animation: msg-in .3s ease;
}
@keyframes msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #f1f5f9;
}
.msg-bubble {
  flex: 1;
  min-width: 0;
  max-width: 78%;
}

.msg-row.assistant .msg-bubble .markdown-body {
  background: $bg-card;
  padding: 14px 18px;
  border-radius: 4px $radius-lg $radius-lg $radius-lg;
  border: 1px solid $border;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.msg-row.user {
  flex-direction: row-reverse;
  .msg-avatar { background: linear-gradient(135deg, $primary, #a78bfa); color: #fff; }
  .msg-bubble { display: flex; justify-content: flex-end; }
  .msg-user-text {
    background: linear-gradient(135deg, $primary, #7c3aed);
    color: #fff;
    padding: 10px 18px;
    border-radius: $radius-lg $radius-lg 4px $radius-lg;
    font-size: 14px;
    line-height: 1.6;
    display: inline-block;
    box-shadow: 0 2px 8px $primary-glow;
  }
}

.cursor-blink {
  color: $primary;
  animation: blink 1s steps(1) infinite;
  font-weight: 700;
}
@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

/* ==================== 底部输入 ==================== */
.chat-footer {
  background: $bg-card;
  border-top: 1px solid $border;
  padding: 14px 28px 10px;
  flex-shrink: 0;
}
.chat-input-box {
  max-width: 780px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 4px 4px 4px 18px;
  border: 1.5px solid transparent;
  transition: border-color .2s, box-shadow .2s;

  &:focus-within {
    border-color: $primary-light;
    box-shadow: 0 0 0 3px $primary-glow;
    background: #fff;
  }
}
.chat-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: $text-primary;
  padding: 8px 0;
  font-family: inherit;
  &::placeholder { color: $text-muted; }
  &:disabled { opacity: .5; }
}
.btn-send {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary, #a78bfa);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform .15s, box-shadow .2s;
  svg { width: 18px; height: 18px; }

  &:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 3px 12px $primary-glow;
  }
  &:disabled {
    opacity: .4;
    cursor: not-allowed;
  }
}
.chat-footer-hint {
  text-align: center;
  font-size: 11px;
  color: $text-muted;
  margin-top: 8px;
}
</style>
