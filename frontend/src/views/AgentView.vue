<template>
  <div class="agent-page">
    <div class="page-header">
      <h1>AI 职业顾问</h1>
      <p>随时咨询求职问题，获取个性化建议</p>
    </div>

    <div class="agent-layout">
      <!-- 左侧：洞察面板 -->
      <div class="insights-panel">
        <div class="panel-title">求职洞察</div>

        <!-- 每日任务 -->
        <div class="task-section" v-if="dailyTasks.length > 0">
          <div class="section-title">今日任务</div>
          <div class="task-list">
            <div
              v-for="(task, idx) in dailyTasks"
              :key="idx"
              :class="['task-item', { done: task.done }]"
              @click="toggleTask(task)"
            >
              <span class="task-check">{{ task.done ? '✓' : '○' }}</span>
              <span class="task-text">{{ task.text }}</span>
              <span class="task-priority" :class="task.priority">{{ task.priority_label }}</span>
            </div>
          </div>
        </div>

        <!-- 技能建议 -->
        <div class="task-section" v-if="skillRecs.length > 0">
          <div class="section-title">技能提升建议</div>
          <div class="skill-list">
            <div v-for="(skill, idx) in skillRecs" :key="idx" class="skill-item">
              <div class="skill-name">{{ skill.name }}</div>
              <div class="skill-reason">{{ skill.reason }}</div>
              <div class="skill-level">
                <div class="level-bar">
                  <div class="level-fill" :style="{ width: (skill.current / 100) * 100 + '%' }"></div>
                </div>
                <span class="level-text">{{ skill.current }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 投递计划 -->
        <div class="task-section" v-if="appPlan.length > 0">
          <div class="section-title">投递计划</div>
          <div class="plan-list">
            <div v-for="(item, idx) in appPlan" :key="idx" class="plan-item">
              <div class="plan-company">{{ item.company }}</div>
              <div class="plan-title">{{ item.title }}</div>
              <div class="plan-priority">{{ item.priority_label }}</div>
            </div>
          </div>
        </div>

        <!-- 面试计划 -->
        <div class="task-section" v-if="interviewPlan.length > 0">
          <div class="section-title">面试准备</div>
          <div class="plan-list">
            <div v-for="(item, idx) in interviewPlan" :key="idx" class="plan-item">
              <div class="plan-company">{{ item.company }}</div>
              <div class="plan-title">{{ item.title }}</div>
              <div class="plan-tip">{{ item.tip }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：聊天区域 -->
      <div class="chat-panel">
        <div class="chat-header">
          <div class="chat-title">与 AI 顾问对话</div>
          <div class="chat-hint">输入你的求职问题，获取智能建议</div>
        </div>

        <div class="chat-messages" ref="messagesRef">
          <div v-if="messages.length === 0" class="empty-chat">
            <div class="empty-icon">💬</div>
            <div class="empty-text">你好！我是你的 AI 职业顾问</div>
            <div class="empty-hints">
              <button class="hint-btn" @click="quickAsk('我的简历应该如何优化？')">简历优化建议</button>
              <button class="hint-btn" @click="quickAsk('我应该如何准备技术面试？')">面试准备技巧</button>
              <button class="hint-btn" @click="quickAsk('帮我分析一下我的求职策略')">求职策略分析</button>
            </div>
          </div>
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            :class="['message', msg.role]"
          >
            <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="message-bubble">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>
          <div v-if="loading" class="message assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-input-area">
          <textarea
            v-model="inputMessage"
            class="chat-input"
            placeholder="输入你的问题..."
            rows="2"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>
          <button class="send-btn" @click="sendMessage" :disabled="!inputMessage.trim() || loading">
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { agentApi } from '../api/index.js'

export default {
  name: 'AgentView',
  data() {
    return {
      dailyTasks: [],
      skillRecs: [],
      appPlan: [],
      interviewPlan: [],
      messages: [],
      inputMessage: '',
      loading: false,
      sessionId: null,
      messagesRef: null
    }
  },
  async created() {
    await Promise.all([
      this.loadDailyTasks(),
      this.loadSkillRecs(),
      this.loadAppPlan(),
      this.loadInterviewPlan()
    ])
  },
  methods: {
    async loadDailyTasks() {
      try { this.dailyTasks = await agentApi.getDailyTasks() } catch (e) {}
    },
    async loadSkillRecs() {
      try { this.skillRecs = await agentApi.getSkillRecommendations() } catch (e) {}
    },
    async loadAppPlan() {
      try { this.appPlan = await agentApi.getApplicationPlan() } catch (e) {}
    },
    async loadInterviewPlan() {
      try { this.interviewPlan = await agentApi.getInterviewPlan() } catch (e) {}
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.loading) return
      const text = this.inputMessage.trim()
      this.inputMessage = ''
      this.messages.push({ role: 'user', content: text })
      this.loading = true
      try {
        const result = await agentApi.chat(text, this.sessionId)
        this.sessionId = result.session_id || this.sessionId
        this.messages.push({ role: 'assistant', content: result.reply || result.response || '好的，我已记录。' })
      } catch (e) {
        this.messages.push({ role: 'assistant', content: '抱歉，暂时无法回复，请稍后重试。' })
      } finally {
        this.loading = false
        this.$nextTick(() => {
          const el = this.$refs.messagesRef
          if (el) el.scrollTop = el.scrollHeight
        })
      }
    },
    quickAsk(text) {
      this.inputMessage = text
      this.sendMessage()
    },
    toggleTask(task) {
      task.done = !task.done
    },
    formatMessage(text) {
      if (!text) return ''
      return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    }
  }
}
</script>

<style scoped>
.agent-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}

.page-header p {
  font-size: 15px;
  color: var(--text-secondary);
}

.agent-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  align-items: start;
}

/* Insights Panel */
.insights-panel {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  max-height: 80vh;
  overflow-y: auto;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.task-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.task-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

.task-list, .skill-list, .plan-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 14px;
}

.task-item:hover { background: var(--bg); }
.task-item.done { opacity: 0.5; text-decoration: line-through; }

.task-check { color: var(--green); font-size: 14px; flex-shrink: 0; }
.task-text { flex: 1; color: var(--text-primary); }

.task-priority {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 980px;
  flex-shrink: 0;
}

.task-priority.high { background: #ffeaea; color: var(--red); }
.task-priority.medium { background: #fff4e0; color: var(--orange); }
.task-priority.low { background: #e8f8ec; color: var(--green); }

.skill-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.skill-item:last-child { border-bottom: none; }

.skill-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.skill-reason {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.skill-level {
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-bar {
  flex: 1;
  height: 6px;
  background: var(--bg);
  border-radius: 3px;
  overflow: hidden;
}

.level-fill {
  height: 100%;
  background: var(--blue);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.level-text {
  font-size: 12px;
  color: var(--text-tertiary);
  min-width: 32px;
  text-align: right;
}

.plan-item {
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 8px;
}

.plan-company {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.plan-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.plan-priority, .plan-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

/* Chat Panel */
.chat-panel {
  background: var(--bg-white);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  height: 80vh;
  max-height: 700px;
  overflow: hidden;
}

.chat-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.chat-title {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
}

.chat-hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-chat {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-text { font-size: 16px; color: var(--text-secondary); margin-bottom: 20px; }

.empty-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.hint-btn {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg);
  color: var(--blue);
  border: 1.5px solid var(--blue-light);
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.hint-btn:hover { background: var(--blue-light); }

.message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.message.user { flex-direction: row-reverse; }

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
}

.message.assistant .message-bubble {
  background: var(--bg);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.message.user .message-bubble {
  background: var(--blue);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: typing 1.2s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

.chat-input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  outline: none;
  resize: none;
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
  transition: border-color 0.2s ease;
}

.chat-input:focus { border-color: var(--blue); background: var(--bg-white); }

.send-btn {
  height: 44px;
  padding: 0 24px;
  font-size: 15px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

@media (max-width: 734px) {
  .agent-layout {
    grid-template-columns: 1fr;
  }
  .insights-panel {
    max-height: none;
  }
  .chat-panel {
    height: 60vh;
  }
}
</style>
