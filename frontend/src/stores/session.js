import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export const useSessionStore = defineStore('session', () => {
  const sessionId = ref(localStorage.getItem('sessionId') || '')
  const chatHistory = ref([])
  const analysisResults = ref({})
  const isAnalyzing = ref(false)
  const sessions = ref([])

  // 创建新会话
  async function createSession() {
    const res = await api.createSession()
    sessionId.value = res.session_id
    localStorage.setItem('sessionId', res.session_id)
    chatHistory.value = []
    analysisResults.value = {}
    return res.session_id
  }

  // 加载会话历史
  async function loadHistory() {
    if (!sessionId.value) return
    try {
      const res = await api.getSessionHistory(sessionId.value)
      chatHistory.value = res.chat_history || []
      analysisResults.value = res.analysis_results || {}
    } catch (e) {
      console.error('加载历史失败:', e)
    }
  }

  // 加载会话列表
  async function loadSessions() {
    try {
      const res = await api.listSessions()
      sessions.value = res.sessions || []
    } catch (e) {
      console.error('加载会话列表失败:', e)
    }
  }

  // 切换会话
  async function switchSession(sid) {
    sessionId.value = sid
    localStorage.setItem('sessionId', sid)
    chatHistory.value = []
    analysisResults.value = {}
    await loadHistory()
  }

  // 添加聊天消息
  function addMessage(role, content) {
    chatHistory.value.push({ role, content })
  }

  // 更新最后一条AI消息
  function updateLastAIMessage(content) {
    const lastMsg = chatHistory.value[chatHistory.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = content
    }
  }

  return {
    sessionId,
    chatHistory,
    analysisResults,
    isAnalyzing,
    sessions,
    createSession,
    loadHistory,
    loadSessions,
    switchSession,
    addMessage,
    updateLastAIMessage,
  }
})
