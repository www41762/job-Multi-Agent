<template>
  <div class="app-shell">
    <!-- ==================== 左侧边栏 ==================== -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark">J</div>
        <div class="brand-text">
          <h1>JobMind</h1>
          <span class="brand-sub">智能求职工作台</span>
        </div>
      </div>

      <button class="btn-new-session" @click="handleNewSession">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建分析
      </button>

      <div class="session-list">
        <div
          v-for="s in store.sessions"
          :key="s.session_id"
          :class="['session-item', { active: s.session_id === store.sessionId }]"
          @click="store.switchSession(s.session_id)"
          @contextmenu.prevent="openCtxMenu($event, s)"
        >
          <div class="session-item-dot" :class="{ analyzed: s.has_analysis }"></div>
          <div class="session-item-body">
            <input
              v-if="renamingId === s.session_id"
              v-model="renameInput"
              class="rename-input"
              @keydown.enter.prevent="confirmRename(s.session_id)"
              @keydown.escape="cancelRename"
              @blur="confirmRename(s.session_id)"
              @click.stop
              ref="renameInputRef"
            />
            <template v-else>
              <span class="session-item-title">{{ s.title || '会话 ' + s.session_id }}</span>
              <span class="session-item-meta">
                {{ s.chat_count }} 条对话
                <span v-if="s.has_analysis" class="badge-analyzed">已分析</span>
              </span>
            </template>
          </div>
          <span class="session-item-time" v-if="s.updated_at">{{ formatTime(s.updated_at) }}</span>
          <button class="session-more-btn" @click.stop="openCtxMenu($event, s)" title="更多">
            <svg viewBox="0 0 16 16" fill="currentColor"><circle cx="8" cy="3" r="1.2"/><circle cx="8" cy="8" r="1.2"/><circle cx="8" cy="13" r="1.2"/></svg>
          </button>
        </div>
        <div v-if="store.sessions.length === 0" class="session-empty">
          还没有会话，点击上方开始
        </div>
      </div>

      <!-- 右键菜单 -->
      <Teleport to="body">
        <div v-if="ctxMenu.visible" class="ctx-menu" :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }" @click.stop>
          <div class="ctx-item" @click="startRename">重命名</div>
          <div class="ctx-item" @click="handleClearChat">清空聊天</div>
          <div class="ctx-item danger" @click="handleDeleteSession">删除</div>
        </div>
      </Teleport>

      <!-- 用户画像 -->
      <div class="profile-panel" v-if="userProfile.weaknesses.length || userProfile.strong_skills.length">
        <div class="profile-heading">能力画像</div>
        <div class="profile-row" v-if="userProfile.strong_skills.length">
          <span class="profile-row-label">优势</span>
          <div class="profile-tags">
            <span class="tag green" v-for="s in userProfile.strong_skills.slice(0, 5)" :key="s">{{ s }}</span>
          </div>
        </div>
        <div class="profile-row" v-if="userProfile.weaknesses.length">
          <span class="profile-row-label">待提升</span>
          <div class="profile-tags">
            <span class="tag amber" v-for="w in userProfile.weaknesses.slice(0, 5)" :key="w">{{ w }}</span>
          </div>
        </div>
      </div>

      <div class="sidebar-footer">
        <span>LangGraph × Vue 3</span>
      </div>
    </aside>

    <!-- ==================== 主区域 ==================== -->
    <main class="main-area">
      <!-- 顶部工具栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <nav class="tab-nav">
            <button :class="['tab-item', { active: activeTab === 'analyze' }]" @click="activeTab = 'analyze'">求职分析</button>
            <button :class="['tab-item', { active: activeTab === 'search' }]" @click="activeTab = 'search'">搜索岗位</button>
          </nav>
        </div>
        <div class="topbar-right">
          <button class="topbar-btn" @click="showInputPanel = !showInputPanel">
            {{ showInputPanel ? '收起' : '展开输入' }}
          </button>
          <button v-if="hasResults" class="topbar-btn accent" @click="showResultDrawer = !showResultDrawer">
            {{ showResultDrawer ? '关闭结果' : '查看分析结果' }}
          </button>
        </div>
      </header>

      <!-- ==================== 岗位搜索面板 ==================== -->
      <transition name="fold">
        <section class="search-panel" v-show="showInputPanel && activeTab === 'search'">
          <div class="search-row">
            <input v-model="searchKeyword" type="text" class="search-input" placeholder="岗位关键词，如 大模型开发 / Python后端 / AI Agent" @keydown.enter.prevent="handleSearchJobs" />
            <select v-model="searchCity" class="search-select">
              <option value="">全国</option>
              <option v-for="c in ['北京','上海','深圳','杭州','广州','成都','南京','武汉']" :key="c" :value="c">{{ c }}</option>
            </select>
            <select v-model="searchExperience" class="search-select">
              <option value="">经验不限</option>
              <option v-for="e in ['应届','1-3年','3-5年','5-10年']" :key="e" :value="e">{{ e }}</option>
            </select>
            <button class="btn-primary sm" @click="handleSearchJobs" :disabled="!searchKeyword.trim() || isSearching">
              {{ isSearching ? '搜索中…' : '搜索' }}
            </button>
          </div>

          <div class="search-results" v-if="searchResults.length > 0">
            <p class="search-count">找到 <strong>{{ searchResults.length }}</strong> 个岗位</p>
            <div class="job-card" v-for="(job, idx) in searchResults" :key="idx">
              <div class="job-card-head">
                <div>
                  <h4 class="job-name">{{ job.title }}</h4>
                  <span class="job-co">{{ job.company }}</span>
                </div>
                <span class="job-pay">{{ job.salary }}</span>
              </div>
              <div class="job-metas">
                <span>{{ job.city }}</span>
                <span>{{ job.experience }}</span>
                <span>{{ job.education }}</span>
              </div>
              <div class="job-tags" v-if="job.tags?.length">
                <span class="jtag" v-for="tag in job.tags.slice(0, 4)" :key="tag">{{ tag }}</span>
              </div>
              <div class="job-actions">
                <button class="btn-primary sm" @click="useJobJD(job)">使用此JD分析</button>
                <button class="btn-ghost sm" @click="toggleJobDetail(idx)">{{ expandedJob === idx ? '收起' : 'JD详情' }}</button>
              </div>
              <transition name="fold">
                <pre class="job-jd-text" v-show="expandedJob === idx">{{ job.jd_text }}</pre>
              </transition>
            </div>
          </div>
          <div class="empty-hint" v-else-if="!isSearching && hasSearched">未找到匹配岗位，试试换个关键词</div>
        </section>
      </transition>

      <!-- ==================== 分析输入面板 ==================== -->
      <transition name="fold">
        <section class="input-panel" v-show="showInputPanel && activeTab === 'analyze'">
          <div class="input-grid">
            <div class="input-block">
              <label class="input-label">招聘JD</label>
              <textarea v-model="jdText" class="field-textarea" rows="5" placeholder="粘贴完整的招聘JD，包含岗位名称、职责、要求…"></textarea>
            </div>
            <div class="input-block">
              <label class="input-label">我的简历</label>
              <div class="upload-box" @dragover.prevent @drop.prevent="handleDrop" @click="triggerFileInput">
                <input ref="fileInputRef" type="file" accept=".pdf" hidden @change="handleFileSelect" />
                <template v-if="!resumeFile">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                  <span>拖拽 PDF 到此处，或 <em>点击上传</em></span>
                </template>
                <template v-else>
                  <span class="file-name">{{ resumeFileName }}</span>
                  <button class="btn-x" @click.stop="removeFile">×</button>
                </template>
              </div>
              <div class="or-divider"><span>或粘贴文本</span></div>
              <textarea v-model="resumeText" class="field-textarea sm" rows="3" placeholder="直接粘贴简历文本…"></textarea>
            </div>
          </div>
          <div class="input-footer">
            <button class="btn-primary lg" :disabled="!jdText || (!resumeFile && !resumeText) || store.isAnalyzing" @click="handleAnalyze">
              <span class="spin-dot" v-if="store.isAnalyzing"></span>
              {{ store.isAnalyzing ? '分析中…' : '开始分析' }}
            </button>
            <p class="input-tip">自动执行 JD解析 → 简历分析 → 匹配评估 → 简历优化 → 面试题生成</p>
          </div>
        </section>
      </transition>

      <!-- ==================== 聊天区 ==================== -->
      <section class="chat-area" ref="chatAreaRef">
        <div class="chat-scroll" ref="messagesRef">

          <!-- 欢迎 -->
          <div v-if="store.chatHistory.length === 0 && !streamContent" class="welcome">
            <div class="welcome-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="10" width="36" height="28" rx="4"/><path d="M6 18h36"/><circle cx="15" cy="28" r="3"/><path d="M24 25v6"/><circle cx="33" cy="28" r="3"/></svg>
            </div>
            <h2>准备好了吗？</h2>
            <p>上传简历 + 粘贴JD，一键获取全方位求职分析报告</p>
            <div class="welcome-actions">
              <button class="chip" @click="quickAction('帮我解析这个JD的核心要求')">解析JD</button>
              <button class="chip" @click="quickAction('帮我优化简历，突出技术亮点')">优化简历</button>
              <button class="chip" @click="quickAction('分析我的简历和JD匹配度')">匹配分析</button>
              <button class="chip" @click="quickAction('针对这个岗位生成面试题')">面试题库</button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-for="(msg, idx) in store.chatHistory" :key="idx" :class="['msg', msg.role]">
            <div class="msg-indicator" v-if="msg.role === 'assistant'">AI</div>
            <div class="msg-body">
              <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMd(msg.content)"></div>
              <div v-else class="msg-text">{{ msg.content }}</div>
            </div>
          </div>

          <!-- 流式输出 -->
          <div v-if="streamContent" class="msg assistant">
            <div class="msg-indicator">AI</div>
            <div class="msg-body">
              <div class="markdown-body" v-html="renderMd(streamContent)"></div>
              <span class="typing-cursor" v-if="isStreaming">|</span>
            </div>
          </div>

        </div>
      </section>

      <!-- 底部输入 -->
      <footer class="chat-footer">
        <div class="chat-input-wrap">
          <input v-model="chatInput" type="text" class="chat-input" placeholder="输入消息，追问分析结果或自由对话…" @keydown.enter.prevent="handleSendChat" :disabled="isStreaming" />
          <button class="btn-send" @click="handleSendChat" :disabled="!chatInput.trim() || isStreaming">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
      </footer>
    </main>

    <!-- ==================== 分析结果抽屉 ==================== -->
    <transition name="drawer">
      <aside class="result-drawer" v-if="showResultDrawer && hasResults">
        <div class="drawer-head">
          <h3>分析结果</h3>
          <button class="btn-x" @click="showResultDrawer = false">×</button>
        </div>
        <div class="drawer-body">

          <!-- 匹配 -->
          <details open v-if="store.analysisResults.matcher_result" class="drawer-section">
            <summary class="drawer-section-title">匹配分析</summary>
            <div class="drawer-section-content">
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (store.analysisResults.matcher_result?.matcher_result?.match_score || 0) + '%' }"></div>
                <span class="score-num">{{ store.analysisResults.matcher_result?.matcher_result?.match_score || '-' }}/100</span>
              </div>
              <div v-if="store.analysisResults.matcher_result?.matcher_result?.advantages?.length" class="tag-group">
                <span class="tag-label">优势</span>
                <ul class="plain-list"><li v-for="a in store.analysisResults.matcher_result.matcher_result.advantages" :key="a">{{ a }}</li></ul>
              </div>
              <div v-if="store.analysisResults.matcher_result?.matcher_result?.shortcomings?.length" class="tag-group">
                <span class="tag-label">不足</span>
                <ul class="plain-list warn"><li v-for="s in store.analysisResults.matcher_result.matcher_result.shortcomings" :key="s">{{ s }}</li></ul>
              </div>
            </div>
          </details>

          <!-- 面试题 -->
          <details open v-if="store.analysisResults.interview_qa" class="drawer-section">
            <summary class="drawer-section-title">面试题库</summary>
            <div class="drawer-section-content">
              <template v-if="store.analysisResults.interview_qa?.interview_qa_result?.technical_qa?.length">
                <h5 class="qa-heading">技术面</h5>
                <div class="qa-card" v-for="(q, i) in store.analysisResults.interview_qa.interview_qa_result.technical_qa" :key="'t'+i">
                  <div class="qa-q" @click="toggleQA('t'+i)">
                    <span>{{ i+1 }}. {{ q.question }}</span>
                    <span class="qa-toggle">{{ expandedQA['t'+i] ? '−' : '+' }}</span>
                  </div>
                  <div class="qa-a" v-show="expandedQA['t'+i]">{{ q.answer }}</div>
                </div>
              </template>
              <template v-if="store.analysisResults.interview_qa?.interview_qa_result?.project_qa?.length">
                <h5 class="qa-heading">项目深挖</h5>
                <div class="qa-card" v-for="(q, i) in store.analysisResults.interview_qa.interview_qa_result.project_qa" :key="'p'+i">
                  <div class="qa-q" @click="toggleQA('p'+i)">
                    <span>{{ i+1 }}. {{ q.question }}</span>
                    <span class="qa-toggle">{{ expandedQA['p'+i] ? '−' : '+' }}</span>
                  </div>
                  <div class="qa-a" v-show="expandedQA['p'+i]">{{ q.answer }}</div>
                </div>
              </template>
              <template v-if="store.analysisResults.interview_qa?.interview_qa_result?.behavior_qa?.length">
                <h5 class="qa-heading">行为面</h5>
                <div class="qa-card" v-for="(q, i) in store.analysisResults.interview_qa.interview_qa_result.behavior_qa" :key="'b'+i">
                  <div class="qa-q" @click="toggleQA('b'+i)">
                    <span>{{ i+1 }}. {{ q.question }}</span>
                    <span class="qa-toggle">{{ expandedQA['b'+i] ? '−' : '+' }}</span>
                  </div>
                  <div class="qa-a" v-show="expandedQA['b'+i]">{{ q.answer }}</div>
                </div>
              </template>
            </div>
          </details>

          <!-- 简历优化 -->
          <details v-if="store.analysisResults.optimized_resume" class="drawer-section">
            <summary class="drawer-section-title">简历优化</summary>
            <div class="drawer-section-content">
              <div v-if="store.analysisResults.optimized_resume?.optimization_highlights?.length" class="tag-group">
                <span class="tag-label">优化亮点</span>
                <ul class="plain-list highlight"><li v-for="h in store.analysisResults.optimized_resume.optimization_highlights" :key="h">{{ h }}</li></ul>
              </div>
              <div v-if="store.analysisResults.optimized_resume?.optimized_resume" class="resume-preview">
                <div class="markdown-body" v-html="renderMd(store.analysisResults.optimized_resume.optimized_resume)"></div>
              </div>
            </div>
          </details>

        </div>
      </aside>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useSessionStore } from '../stores/session'
import { renderMarkdown } from '../utils/markdown'
import api from '../utils/api'
import { ElMessage } from 'element-plus'

const store = useSessionStore()
const chatAreaRef = ref(null)
const messagesRef = ref(null)
const fileInputRef = ref(null)

const activeTab = ref('analyze')
const jdText = ref('')
const resumeFile = ref(null)
const resumeFileName = ref('')
const resumeText = ref('')
const chatInput = ref('')
const showInputPanel = ref(true)

// 岗位搜索
const searchKeyword = ref('')
const searchCity = ref('')
const searchExperience = ref('')
const searchResults = ref([])
const isSearching = ref(false)
const hasSearched = ref(false)
const expandedJob = ref(-1)

// 流式
const streamContent = ref('')
const isStreaming = ref(false)
let currentController = null

// 结果抽屉
const showResultDrawer = ref(false)
const expandedQA = ref({})
const hasResults = computed(() => {
  const r = store.analysisResults
  return r && (r.matcher_result || r.interview_qa || r.optimized_resume)
})
function toggleQA(key) { expandedQA.value[key] = !expandedQA.value[key] }

// 用户画像
const userProfile = ref({ weaknesses: [], strong_skills: [] })
async function loadUserProfile() {
  try { userProfile.value = await api.getUserProfile() } catch (e) { /* ignore */ }
}

function renderMd(text) { return renderMarkdown(text) }

// ==================== 会话管理 ====================
const renamingId = ref('')
const renameInput = ref('')
const renameInputRef = ref(null)
const ctxMenu = ref({ visible: false, x: 0, y: 0, session: null })

function openCtxMenu(e, session) { ctxMenu.value = { visible: true, x: e.clientX, y: e.clientY, session } }
function closeCtxMenu() { ctxMenu.value.visible = false }

function startRename() {
  const s = ctxMenu.value.session
  if (!s) return
  renamingId.value = s.session_id
  renameInput.value = s.title || ''
  closeCtxMenu()
  nextTick(() => {
    if (renameInputRef.value) {
      const el = Array.isArray(renameInputRef.value) ? renameInputRef.value[0] : renameInputRef.value
      el?.focus()
    }
  })
}
async function confirmRename(sid) {
  if (renameInput.value.trim()) await store.renameSession(sid, renameInput.value.trim())
  renamingId.value = ''
}
function cancelRename() { renamingId.value = '' }

async function handleDeleteSession() {
  const s = ctxMenu.value.session
  closeCtxMenu()
  if (!s) return
  await store.deleteSession(s.session_id)
  if (!store.sessionId) await store.createSession()
  ElMessage.success('已删除')
}
async function handleClearChat() {
  const s = ctxMenu.value.session
  closeCtxMenu()
  if (!s) return
  await store.clearChat(s.session_id)
  ElMessage.success('已清空')
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
    if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch { return '' }
}

if (typeof document !== 'undefined') {
  document.addEventListener('click', closeCtxMenu)
}

function scrollToBottom() {
  nextTick(() => { if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight })
}
watch(() => store.chatHistory.length, scrollToBottom)
watch(streamContent, scrollToBottom)

onMounted(async () => {
  await store.loadSessions()
  if (!store.sessionId) await store.createSession()
  await store.loadHistory()
  await store.loadSessions()
  await loadUserProfile()
  if (hasResults.value) showResultDrawer.value = true
})

// 自动打开结果抽屉
watch(hasResults, (v) => { if (v) showResultDrawer.value = true })

async function handleNewSession() {
  await store.createSession()
  await store.loadSessions()
  jdText.value = ''
  resumeFile.value = null
  resumeFileName.value = ''
  resumeText.value = ''
  showInputPanel.value = true
  showResultDrawer.value = false
  ElMessage.success('新会话已创建')
}

// ==================== 文件上传 ====================
function triggerFileInput() { fileInputRef.value?.click() }
function handleFileSelect(e) {
  const f = e.target.files[0]
  if (f) { resumeFile.value = f; resumeFileName.value = f.name }
}
function handleDrop(e) {
  const f = e.dataTransfer.files[0]
  if (f?.name.endsWith('.pdf')) { resumeFile.value = f; resumeFileName.value = f.name }
}
function removeFile() { resumeFile.value = null; resumeFileName.value = '' }

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
  if (resumeFile.value) formData.append('resume_file', resumeFile.value)
  else if (resumeText.value) formData.append('resume_text', resumeText.value)

  currentController = api.analyzeStream(
    formData,
    (data) => { streamContent.value += data },
    async () => {
      streamContent.value = ''
      isStreaming.value = false
      store.isAnalyzing = false
      ElMessage.success('分析完成')
      await store.loadHistory()
      await store.loadSessions()
      await loadUserProfile()
    },
    (err) => {
      streamContent.value += `\n\n❌ 错误: ${err}`
      store.addMessage('assistant', streamContent.value)
      streamContent.value = ''
      isStreaming.value = false
      store.isAnalyzing = false
      ElMessage.error('分析出错')
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
    store.sessionId, msg,
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

function quickAction(text) { chatInput.value = text; showInputPanel.value = true }

// ==================== 搜索 ====================
async function handleSearchJobs() {
  if (!searchKeyword.value.trim() || isSearching.value) return
  isSearching.value = true
  hasSearched.value = true
  searchResults.value = []
  expandedJob.value = -1
  try {
    const res = await api.searchJobs({
      keyword: searchKeyword.value.trim(),
      city: searchCity.value,
      experience: searchExperience.value,
    })
    searchResults.value = res.jobs || []
    searchResults.value.length === 0
      ? ElMessage.warning('未找到匹配岗位')
      : ElMessage.success(`找到 ${searchResults.value.length} 个岗位`)
  } catch (e) {
    ElMessage.error('搜索失败：' + (e.message || '网络错误'))
  } finally {
    isSearching.value = false
  }
}

function toggleJobDetail(idx) { expandedJob.value = expandedJob.value === idx ? -1 : idx }

function useJobJD(job) {
  jdText.value = `【${job.title}】- ${job.company}\n城市：${job.city} | 薪资：${job.salary} | 经验：${job.experience}\n\n${job.jd_text}`
  activeTab.value = 'analyze'
  showInputPanel.value = true
  ElMessage.success(`已填入「${job.title}」的JD`)
}
</script>

<style lang="scss" scoped>
@use "sass:color";

/* ===== Design Tokens ===== */
$ink: #0b0b2b;
$ink-secondary: #555770;
$ink-muted: #8b8da3;
$surface: #f5f5f0;
$surface-card: #ffffff;
$border: #e4e4de;
$accent: #d97706;
$accent-light: #fbbf24;
$accent-bg: rgba(217, 119, 6, .07);
$green: #059669;
$green-bg: rgba(5, 150, 105, .08);
$red: #dc2626;
$red-bg: rgba(220, 38, 38, .06);
$amber-bg: rgba(245, 158, 11, .08);
$r: 10px;
$sidebar-w: 260px;
$drawer-w: 380px;

/* ===== Shell ===== */
.app-shell { display: flex; height: 100vh; overflow: hidden; background: $surface; }

/* ===== Sidebar ===== */
.sidebar {
  width: $sidebar-w; min-width: $sidebar-w; background: $ink; color: #7a7aee;
  display: flex; flex-direction: column; user-select: none; font-size: 13px;
}
.sidebar-brand {
  display: flex; align-items: center; gap: 10px; padding: 20px 18px 16px;
  border-bottom: 1px solid rgba(255,255,255,.06);
  .brand-mark {
    width: 34px; height: 34px; border-radius: 8px;
    background: $accent; color: #fff; font-weight: 800; font-size: 18px;
    display: flex; align-items: center; justify-content: center;
  }
  h1 { font-size: 16px; font-weight: 700; color: #f0f0f5; letter-spacing: -.3px; }
  .brand-sub { font-size: 11px; color: $ink-muted; }
}
.btn-new-session {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  margin: 12px 14px 4px; padding: 9px 0;
  border: 1.5px dashed rgba(255,255,255,.12); border-radius: 8px;
  background: transparent; color: #b0b0c0; font-size: 13px; cursor: pointer;
  transition: .15s; font-family: inherit;
  svg { width: 15px; height: 15px; }
  &:hover { border-color: $accent; color: $accent-light; background: rgba(217,119,6,.06); }
}
.session-list { flex: 1; overflow-y: auto; padding: 6px 10px; }

.session-item {
  display: flex; align-items: center; gap: 8px; padding: 9px 10px; border-radius: 8px;
  cursor: pointer; margin-bottom: 1px; transition: background .12s; position: relative;
  &:hover { background: rgba(255,255,255,.05); }
  &.active { background: rgba(255,255,255,.08); box-shadow: inset 3px 0 0 $accent; }
}
.session-item-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #555770; flex-shrink: 0;
  &.analyzed { background: $green; }
}
.session-item-body { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.session-item-title {
  font-size: 13px; font-weight: 500; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; color: #d4d4dc;
}
.session-item-meta {
  font-size: 11px; color: $ink-muted;
  display: flex; align-items: center; gap: 6px;
}
.badge-analyzed {
  font-size: 10px; padding: 1px 6px; border-radius: 99px;
  background: $green-bg; color: $green;
}
.session-item-time { font-size: 10px; color: rgba(255,255,255,.2); white-space: nowrap; }
.session-more-btn {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  width: 22px; height: 22px; border: none; background: transparent; color: rgba(255,255,255,.2);
  border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: .12s; svg { width: 12px; height: 12px; }
  &:hover { color: #fff; background: rgba(255,255,255,.08); }
}
.session-item:hover .session-more-btn { opacity: 1; }

.rename-input {
  width: 100%; padding: 3px 6px; border: 1px solid $accent; border-radius: 4px;
  background: rgba(255,255,255,.06); color: #e0e0e8; font-size: 12px; outline: none; font-family: inherit;
}
.session-empty { text-align: center; color: $ink-muted; font-size: 12px; padding: 30px 0; }

/* 右键菜单 */
.ctx-menu {
  position: fixed; z-index: 9999; background: #2a2a3c;
  border: 1px solid rgba(255,255,255,.08); border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0,0,0,.45); padding: 4px 0; min-width: 140px;
  .ctx-item {
    padding: 7px 14px; font-size: 13px; color: #d4d4dc; cursor: pointer; transition: background .1s;
    &:hover { background: rgba(255,255,255,.06); }
    &.danger { color: $red; }
    &.danger:hover { background: $red-bg; }
  }
}

/* 画像 */
.profile-panel {
  padding: 10px 14px; border-top: 1px solid rgba(255,255,255,.05); flex-shrink: 0;
  .profile-heading {
    font-size: 11px; font-weight: 600; color: #a0a0b0;
    margin-bottom: 8px; text-transform: uppercase; letter-spacing: .5px;
  }
  .profile-row { margin-bottom: 6px; }
  .profile-row-label { font-size: 11px; color: $ink-muted; display: block; margin-bottom: 4px; }
  .profile-tags { display: flex; flex-wrap: wrap; gap: 4px; }
}
.tag {
  font-size: 10px; padding: 2px 8px; border-radius: 99px;
  white-space: nowrap; max-width: 110px; overflow: hidden; text-overflow: ellipsis;
  &.green { background: $green-bg; color: $green; }
  &.amber { background: $amber-bg; color: $accent; }
}
.sidebar-footer {
  padding: 12px 14px; border-top: 1px solid rgba(255,255,255,.05);
  span { font-size: 10px; color: rgba(255,255,255,.15); display: block; text-align: center; }
}

/* ===== Main area ===== */
.main-area {
  flex: 1; display: flex; flex-direction: column; overflow: hidden; background: $surface;
}
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 48px; min-height: 48px;
  background: $surface-card; border-bottom: 1px solid $border;
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.topbar-right { display: flex; align-items: center; gap: 8px; }

.tab-nav { display: flex; gap: 2px; }
.tab-item {
  padding: 5px 14px; border: none; border-radius: 6px; background: transparent;
  color: $ink-secondary; font-size: 13px; font-weight: 500; cursor: pointer;
  transition: .12s; font-family: inherit;
  &:hover { background: #eeeee8; color: $ink; }
  &.active { background: $ink; color: #fff; }
}
.topbar-btn {
  padding: 5px 14px; border: 1px solid $border; border-radius: 6px;
  background: $surface-card; color: $ink-secondary; font-size: 12px; cursor: pointer;
  transition: .12s; font-family: inherit;
  &:hover { border-color: #ccc; color: $ink; }
  &.accent {
    border-color: $accent; color: $accent; font-weight: 600;
    &:hover { background: $accent-bg; }
  }
}

/* ===== Transitions ===== */
.fold-enter-active, .fold-leave-active { transition: all .25s ease; max-height: 600px; opacity: 1; }
.fold-enter-from, .fold-leave-to { max-height: 0; opacity: 0; overflow: hidden; }
.drawer-enter-active, .drawer-leave-active { transition: all .3s cubic-bezier(.4,0,.2,1); }
.drawer-enter-from, .drawer-leave-to { transform: translateX(100%); opacity: 0; }

/* ===== Input panels ===== */
.search-panel, .input-panel {
  background: $surface-card; border-bottom: 1px solid $border;
  padding: 16px 20px; flex-shrink: 0; overflow: hidden;
}
.search-row { display: flex; gap: 8px; align-items: center; }
.search-input {
  flex: 1; padding: 9px 14px; border: 1px solid $border; border-radius: 8px;
  font-size: 13px; color: $ink; outline: none; font-family: inherit; background: $surface;
  &:focus { border-color: $accent; box-shadow: 0 0 0 2px $accent-bg; }
  &::placeholder { color: $ink-muted; }
}
.search-select {
  padding: 9px 10px; border: 1px solid $border; border-radius: 8px;
  font-size: 12px; color: $ink; background: $surface; font-family: inherit; outline: none; cursor: pointer;
  &:focus { border-color: $accent; }
}
.search-count { font-size: 13px; color: $ink-secondary; margin: 14px 0 10px; strong { color: $accent; } }

/* Job cards */
.job-card {
  background: $surface; border: 1px solid $border; border-radius: $r; padding: 14px; margin-bottom: 8px;
  transition: border-color .15s;
  &:hover { border-color: #ccc; }
}
.job-card-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.job-name { font-size: 14px; font-weight: 600; color: $ink; }
.job-co { font-size: 12px; color: $ink-secondary; }
.job-pay { font-size: 15px; font-weight: 700; color: $red; }
.job-metas { display: flex; gap: 10px; margin-bottom: 6px; font-size: 12px; color: $ink-muted; }
.job-tags { display: flex; gap: 5px; margin-bottom: 10px; flex-wrap: wrap; }
.jtag { font-size: 11px; padding: 2px 9px; border-radius: 99px; background: $accent-bg; color: $accent; }
.job-actions { display: flex; gap: 6px; }
.job-jd-text {
  margin-top: 10px; background: $surface; border: 1px solid $border; border-radius: 8px;
  padding: 12px; font-size: 12px; line-height: 1.7; color: $ink; white-space: pre-wrap;
  word-wrap: break-word; font-family: inherit; max-height: 260px; overflow-y: auto;
}
.empty-hint { text-align: center; padding: 36px; color: $ink-muted; font-size: 13px; }

/* Input panel */
.input-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.input-block { display: flex; flex-direction: column; gap: 6px; }
.input-label { font-size: 12px; font-weight: 600; color: $ink; letter-spacing: .3px; }
.field-textarea {
  width: 100%; border: 1px solid $border; border-radius: 8px; padding: 10px 12px;
  font-size: 13px; line-height: 1.6; color: $ink; resize: vertical; font-family: inherit;
  outline: none; background: $surface;
  &:focus { border-color: $accent; box-shadow: 0 0 0 2px $accent-bg; }
  &.sm { min-height: 52px; }
  &::placeholder { color: $ink-muted; }
}
.upload-box {
  border: 1.5px dashed $border; border-radius: 8px; padding: 18px; text-align: center;
  cursor: pointer; transition: .15s; color: $ink-muted; font-size: 13px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  svg { width: 28px; height: 28px; color: #c0c0c8; }
  em { color: $accent; font-style: normal; }
  &:hover { border-color: $accent; background: $accent-bg; }
  .file-name { color: $accent; font-weight: 500; }
}
.or-divider {
  display: flex; align-items: center; margin: 6px 0;
  span { font-size: 11px; color: $ink-muted; padding: 0 8px; }
  &::before, &::after { content: ''; flex: 1; height: 1px; background: $border; }
}
.input-footer { margin-top: 14px; text-align: center; }
.input-tip { font-size: 11px; color: $ink-muted; margin-top: 8px; }

/* ===== Buttons ===== */
.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 28px; border: none; border-radius: 8px;
  background: $accent; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: .15s; font-family: inherit;
  &:hover:not(:disabled) { background: color.adjust($accent, $lightness: -6%); }
  &:disabled { opacity: .45; cursor: not-allowed; }
  &.sm { padding: 7px 16px; font-size: 12px; border-radius: 6px; }
  &.lg { padding: 12px 36px; font-size: 15px; }
}
.btn-ghost {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px; border: 1px solid $border; border-radius: 6px;
  background: $surface-card; color: $ink-secondary; font-size: 12px; cursor: pointer;
  transition: .12s; font-family: inherit;
  &:hover { border-color: $accent; color: $accent; }
}
.btn-x {
  width: 24px; height: 24px; border: none; background: #eeeee8; color: $ink-muted;
  border-radius: 50%; font-size: 15px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: .12s; line-height: 1;
  &:hover { background: $red-bg; color: $red; }
}
.spin-dot {
  width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== Chat ===== */
.chat-area { flex: 1; overflow: hidden; }
.chat-scroll { height: 100%; overflow-y: auto; padding: 20px 24px; }

.welcome {
  text-align: center; padding: 60px 20px 40px;
  .welcome-icon { margin-bottom: 20px; svg { width: 56px; height: 56px; color: $ink-muted; } }
  h2 { font-size: 22px; font-weight: 700; color: $ink; margin-bottom: 8px; }
  p { color: $ink-secondary; font-size: 14px; margin-bottom: 28px; }
}
.welcome-actions { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
.chip {
  padding: 8px 18px; border: 1px solid $border; border-radius: 99px;
  background: $surface-card; color: $ink; font-size: 13px; cursor: pointer;
  transition: .15s; font-family: inherit;
  &:hover { border-color: $accent; color: $accent; background: $accent-bg; }
}

/* Messages */
.msg { display: flex; gap: 10px; margin-bottom: 16px; animation: msgIn .25s ease; }
.msg.user { flex-direction: row-reverse; }
@keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.msg-indicator {
  width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; letter-spacing: .3px;
  background: $ink; color: #fafaf9;
}
.msg-body { flex: 1; min-width: 0; max-width: 76%; }
.msg.assistant .msg-body .markdown-body {
  background: $surface-card; padding: 14px 16px; border-radius: 2px $r $r $r;
  border: 1px solid $border;
}
.msg.user .msg-body { display: flex; justify-content: flex-end; }
.msg.user .msg-text {
  background: $ink; color: #f0f0f5; padding: 10px 16px;
  border-radius: $r $r 2px $r; font-size: 14px; line-height: 1.6; display: inline-block;
}
.typing-cursor { color: $accent; font-weight: 700; animation: blink 1s steps(1) infinite; }
@keyframes blink { 0%,49% { opacity: 1; } 50%,100% { opacity: 0; } }

/* Footer */
.chat-footer {
  background: $surface-card; border-top: 1px solid $border;
  padding: 12px 24px 10px; flex-shrink: 0;
}
.chat-input-wrap {
  max-width: 720px; margin: 0 auto; display: flex; align-items: center; gap: 8px;
  background: $surface; border-radius: 99px; padding: 4px 4px 4px 16px;
  border: 1.5px solid transparent; transition: .15s;
  &:focus-within { border-color: $accent; box-shadow: 0 0 0 3px $accent-bg; background: #fff; }
}
.chat-input {
  flex: 1; border: none; outline: none; background: transparent;
  font-size: 14px; color: $ink; padding: 8px 0; font-family: inherit;
  &::placeholder { color: $ink-muted; }
  &:disabled { opacity: .4; }
}
.btn-send {
  width: 38px; height: 38px; border: none; border-radius: 50%; background: $ink;
  color: #fafaf9; cursor: pointer; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: .12s;
  svg { width: 16px; height: 16px; }
  &:hover:not(:disabled) { background: color.adjust($ink, $lightness: 12%); }
  &:disabled { opacity: .3; cursor: not-allowed; }
}

/* ===== Result drawer ===== */
.result-drawer {
  width: $drawer-w; min-width: $drawer-w; background: $surface-card;
  border-left: 1px solid $border; display: flex; flex-direction: column; overflow: hidden;
}
.drawer-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 18px; border-bottom: 1px solid $border;
  h3 { font-size: 15px; font-weight: 700; color: $ink; }
}
.drawer-body { flex: 1; overflow-y: auto; padding: 12px 16px; }

.drawer-section {
  margin-bottom: 8px; border: 1px solid $border; border-radius: $r; overflow: hidden;
}
.drawer-section-title {
  display: block; padding: 10px 14px; font-size: 13px; font-weight: 600; color: $ink;
  background: $surface; cursor: pointer; user-select: none; list-style: none;
  &::-webkit-details-marker { display: none; }
}
details[open] > .drawer-section-title { border-bottom: 1px solid $border; }
.drawer-section-content { padding: 12px 14px; }

.score-bar {
  position: relative; height: 24px; background: #eeeee8; border-radius: 99px;
  overflow: hidden; margin-bottom: 12px;
  .score-fill {
    position: absolute; left: 0; top: 0; height: 100%;
    background: linear-gradient(90deg, $accent, $accent-light);
    border-radius: 99px; transition: width .6s ease;
  }
  .score-num {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    font-size: 12px; font-weight: 700; color: $ink;
  }
}
.tag-group { margin-bottom: 10px; }
.tag-label {
  font-size: 11px; font-weight: 600; color: $ink-muted; display: block;
  margin-bottom: 4px; text-transform: uppercase; letter-spacing: .3px;
}
.plain-list {
  list-style: none; padding: 0; margin: 0;
  li {
    font-size: 13px; color: $ink; padding: 3px 0 3px 14px; position: relative;
    &::before {
      content: ''; position: absolute; left: 0; top: 10px;
      width: 5px; height: 5px; border-radius: 50%; background: $green;
    }
  }
  &.warn li::before { background: $accent; }
  &.highlight li::before { background: $accent-light; }
}

/* QA */
.qa-heading {
  font-size: 12px; font-weight: 600; color: $accent; margin: 10px 0 6px;
  text-transform: uppercase; letter-spacing: .3px;
}
.qa-card { border: 1px solid $border; border-radius: 8px; margin-bottom: 6px; overflow: hidden; }
.qa-q {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;
  padding: 10px 12px; font-size: 13px; font-weight: 500; color: $ink; cursor: pointer;
  transition: background .1s;
  &:hover { background: $surface; }
  .qa-toggle { color: $ink-muted; font-size: 16px; flex-shrink: 0; line-height: 1; }
}
.qa-a {
  padding: 10px 12px; font-size: 13px; color: $ink-secondary; line-height: 1.65;
  background: $surface; border-top: 1px solid $border;
}
.resume-preview {
  margin-top: 8px; border: 1px solid $border; border-radius: 8px; padding: 14px;
  max-height: 400px; overflow-y: auto;
}
</style>
