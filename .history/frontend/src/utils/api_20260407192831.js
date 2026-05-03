/**
 * API请求封装 - 支持SSE流式请求
 */
import axios from 'axios'

const BASE_URL = '/api'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
})

const api = {
  // ==================== 会话管理 ====================
  
  async createSession() {
    const res = await http.post('/session/create')
    return res.data
  },

  async listSessions() {
    const res = await http.get('/session/list')
    return res.data
  },

  async getSessionHistory(sessionId) {
    const res = await http.get(`/session/${sessionId}/history`)
    return res.data
  },

  async deleteSession(sessionId) {
    const res = await http.delete(`/session/${sessionId}`)
    return res.data
  },

  // ==================== SSE流式请求封装 ====================
  
  /**
   * SSE流式分析请求
   * @param {FormData} formData - 包含session_id, jd_text, resume_file/resume_text
   * @param {Function} onChunk - 每个chunk的回调 (data) => void
   * @param {Function} onDone - 完成回调
   * @param {Function} onError - 错误回调
   * @returns {AbortController} 用于取消请求
   */
  analyzeStream(formData, onChunk, onDone, onError) {
    const controller = new AbortController()
    
    fetch(`${BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok) {
        const errText = await response.text()
        onError(errText)
        return
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'content') {
                onChunk(data.data)
              } else if (data.type === 'done') {
                onDone()
              } else if (data.type === 'error') {
                onError(data.data)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    }).catch((e) => {
      if (e.name !== 'AbortError') {
        onError(e.message)
      }
    })
    
    return controller
  },

  /**
   * SSE流式聊天请求
   * @param {string} sessionId
   * @param {string} message
   * @param {Function} onChunk
   * @param {Function} onDone
   * @param {Function} onError
   * @returns {AbortController}
   */
  chatStream(sessionId, message, onChunk, onDone, onError) {
    const controller = new AbortController()
    
    fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok) {
        const errText = await response.text()
        onError(errText)
        return
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'content') {
                onChunk(data.data)
              } else if (data.type === 'done') {
                onDone()
              } else if (data.type === 'error') {
                onError(data.data)
              }
            } catch (e) {
              // 忽略
            }
          }
        }
      }
    }).catch((e) => {
      if (e.name !== 'AbortError') {
        onError(e.message)
      }
    })
    
    return controller
  },

  // ==================== 获取结果 ====================
  
  async getResults(sessionId) {
    const res = await http.get(`/results/${sessionId}`)
    return res.data
  },

  async healthCheck() {
    const res = await http.get('/health')
    return res.data
  },

  // ==================== 用户画像（长期记忆） ====================

  async getUserProfile() {
    const res = await http.get('/profile')
    return res.data
  },

  async addWeakness(weakness) {
    const res = await http.post('/profile/weakness', { weakness })
    return res.data
  },

  async addStrength(skill) {
    const res = await http.post('/profile/strength', { skill })
    return res.data
  },
}

export default api
