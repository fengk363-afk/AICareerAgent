<template>
  <div class="interview-page">
    <!-- 选择岗位 -->
    <div class="page-header">
      <h1>面试教练</h1>
      <p>AI 生成面试题，模拟面试并给出专业反馈</p>
    </div>

    <!-- 岗位选择 -->
    <div class="job-select-card">
      <div class="section-title">选择目标岗位</div>
      <div class="search-bar">
        <input v-model="searchKeyword" type="text" placeholder="搜索岗位..." class="search-input" @keyup.enter="searchJobs" />
        <button class="search-btn" @click="searchJobs">搜索</button>
      </div>
      <div v-if="jobs.length === 0 && !loading" class="empty-state">
        <p>暂无岗位，请先在岗位页面初始化数据</p>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else class="job-list">
        <div
          v-for="job in jobs"
          :key="job.id"
          class="job-item"
          :class="{ active: selectedJob?.id === job.id }"
          @click="selectedJob = job"
        >
          <div class="job-item-info">
            <div class="job-item-company">{{ job.company }}</div>
            <div class="job-item-title">{{ job.title }}</div>
          </div>
          <div class="job-item-meta">{{ job.location }}</div>
        </div>
      </div>
    </div>

    <!-- 问题类型选择 -->
    <div v-if="selectedJob" class="question-type-card">
      <div class="section-title">问题类型</div>
      <div class="type-tags">
        <button
          v-for="type in questionTypes"
          :key="type.value"
          :class="['type-tag', { active: selectedTypes.includes(type.value) }]"
          @click="toggleType(type.value)"
        >
          {{ type.label }}
        </button>
      </div>
      <button class="generate-btn" @click="generateQuestions" :disabled="generating">
        {{ generating ? '生成中...' : '生成面试题' }}
      </button>
    </div>

    <!-- 面试会话 -->
    <div v-if="session" class="session-card">
      <div class="session-header">
        <div>
          <div class="session-title">{{ session.job?.company }} · {{ session.job?.title }}</div>
          <div class="session-meta">进度: {{ answeredCount }}/{{ questions.length }} 题</div>
        </div>
        <button class="close-btn" @click="closeSession">×</button>
      </div>

      <!-- 当前问题 -->
      <div v-if="currentQuestion" class="question-area">
        <div class="question-badge">{{ currentQuestion.category }}</div>
        <div class="question-text">{{ currentQuestion.question }}</div>
        <textarea
          v-model="currentAnswer"
          class="answer-input"
          placeholder="请输入你的回答..."
          rows="4"
        ></textarea>
        <div class="question-actions">
          <button class="submit-btn" @click="submitAnswer" :disabled="!currentAnswer.trim()">
            提交答案
          </button>
          <button v-if="answeredCount < questions.length" class="skip-btn" @click="skipQuestion">
            跳过
          </button>
        </div>
      </div>

      <!-- 反馈 -->
      <div v-if="feedback" class="feedback-area">
        <div class="feedback-score">
          <div class="score-circle" :class="getScoreClass(feedback.score)">
            {{ feedback.score }}
          </div>
          <div class="feedback-content">
            <div class="feedback-title">AI 反馈</div>
            <div class="feedback-points">
              <div v-for="(point, idx) in feedback.points" :key="idx" class="point-item">
                <span class="point-icon">{{ point.type === 'good' ? '✓' : point.type === 'bad' ? '✗' : '→' }}</span>
                <span>{{ point.text }}</span>
              </div>
            </div>
            <div class="feedback-suggestion" v-if="feedback.suggestion">
              <strong>建议：</strong>{{ feedback.suggestion }}
            </div>
          </div>
        </div>
        <button class="next-btn" @click="nextQuestion">
          {{ answeredCount < questions.length ? '下一题' : '查看结果' }}
        </button>
      </div>

      <!-- 完成 -->
      <div v-if="sessionCompleted" class="completed-area">
        <div class="completed-icon">🎉</div>
        <h3>面试完成！</h3>
        <div class="overall-score">
          <div class="score-circle large" :class="getScoreClass(session.overall_score || 0)">
            {{ session.overall_score || 0 }}
          </div>
          <div class="score-label">综合评分</div>
        </div>
        <div class="answer-list">
          <div v-for="(ans, idx) in session.answers" :key="idx" class="answer-item">
            <div class="answer-q">{{ questions[idx]?.question || '问题 ' + (idx+1) }}</div>
            <div class="answer-a">{{ ans.answer }}</div>
            <div class="answer-score">得分: {{ ans.score || '-' }}</div>
          </div>
        </div>
        <button class="new-session-btn" @click="startNewSession">再来一次</button>
      </div>
    </div>

    <!-- 历史记录 -->
    <div v-if="history.length > 0" class="history-section">
      <div class="section-title">面试历史</div>
      <div class="history-list">
        <div v-for="h in history" :key="h.id" class="history-item">
          <div class="history-info">
            <div class="history-company">{{ h.job?.company || '未知公司' }}</div>
            <div class="history-title">{{ h.job?.title || '未知岗位' }}</div>
          </div>
          <div class="history-score" :class="getScoreClass(h.overall_score || 0)">
            {{ h.overall_score || '-' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { interviewApi, jobApi } from '../api/index.js'

export default {
  name: 'InterviewView',
  data() {
    return {
      jobs: [],
      loading: false,
      searchKeyword: '',
      selectedJob: null,
      questionTypes: [
        { label: '技术题', value: 'technical' },
        { label: '行为题', value: 'behavioral' },
        { label: '情景题', value: 'situational' },
        { label: 'HR 题', value: 'hr' },
        { label: '英语题', value: 'english' }
      ],
      selectedTypes: ['technical', 'behavioral'],
      generating: false,
      questions: [],
      session: null,
      currentQuestion: null,
      currentAnswer: '',
      feedback: null,
      sessionCompleted: false,
      history: []
    }
  },
  computed: {
    answeredCount() {
      return this.session?.answers?.length || 0
    }
  },
  async created() {
    await this.loadJobs()
    await this.loadHistory()
  },
  methods: {
    async loadJobs() {
      this.loading = true
      try {
        this.jobs = await jobApi.listJobs({ limit: 50 })
      } catch (e) {
        console.error('加载岗位失败', e)
      } finally {
        this.loading = false
      }
    },
    async searchJobs() {
      try {
        this.jobs = await jobApi.listJobs({ keyword: this.searchKeyword, limit: 50 })
      } catch (e) {}
    },
    toggleType(type) {
      const idx = this.selectedTypes.indexOf(type)
      if (idx >= 0) {
        if (this.selectedTypes.length > 1) this.selectedTypes.splice(idx, 1)
      } else {
        this.selectedTypes.push(type)
      }
    },
    async generateQuestions() {
      if (!this.selectedJob) return
      this.generating = true
      try {
        this.questions = await interviewApi.generateQuestions(
          this.selectedJob.id,
          this.selectedTypes.join(',')
        )
        await this.startSession()
      } catch (e) {
        console.error('生成面试题失败', e)
      } finally {
        this.generating = false
      }
    },
    async startSession() {
      try {
        this.session = await interviewApi.createSession(this.selectedJob.id)
        this.currentQuestion = this.questions[0] || null
        this.currentAnswer = ''
        this.feedback = null
        this.sessionCompleted = false
      } catch (e) {
        console.error('创建面试会话失败', e)
      }
    },
    async submitAnswer() {
      if (!this.currentAnswer.trim() || !this.session) return
      try {
        const answerData = {
          question_index: this.answeredCount,
          answer: this.currentAnswer.trim()
        }
        const result = await interviewApi.submitAnswer(this.session.id, answerData)
        this.feedback = result
        this.currentAnswer = ''
      } catch (e) {
        console.error('提交答案失败', e)
      }
    },
    skipQuestion() {
      this.nextQuestion()
    },
    async nextQuestion() {
      this.feedback = null
      const nextIdx = this.answeredCount + 1
      if (nextIdx < this.questions.length) {
        this.currentQuestion = this.questions[nextIdx]
        this.currentAnswer = ''
      } else {
        // 面试完成
        await this.loadSession()
        this.sessionCompleted = true
      }
    },
    async loadSession() {
      try {
        this.session = await interviewApi.getSession(this.session.id)
      } catch (e) {}
    },
    async loadHistory() {
      try {
        this.history = await interviewApi.getHistory()
      } catch (e) {}
    },
    startNewSession() {
      this.session = null
      this.currentQuestion = null
      this.currentAnswer = ''
      this.feedback = null
      this.sessionCompleted = false
      this.generateQuestions()
    },
    closeSession() {
      this.session = null
      this.currentQuestion = null
      this.currentAnswer = ''
      this.feedback = null
      this.sessionCompleted = false
    },
    getScoreClass(score) {
      if (score >= 70) return 'high'
      if (score >= 50) return 'medium'
      return 'low'
    }
  }
}
</script>

<style scoped>
.interview-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

.page-header {
  margin-bottom: 28px;
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

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 14px;
}

.job-select-card, .question-type-card, .session-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  height: 42px;
  padding: 0 14px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  outline: none;
  font-family: inherit;
}

.search-input:focus { border-color: var(--blue); }

.search-btn {
  height: 42px;
  padding: 0 20px;
  font-size: 15px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.job-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1.5px solid transparent;
}

.job-item:hover { background: var(--bg); }
.job-item.active { background: var(--blue-light); border-color: var(--blue); }

.job-item-info { flex: 1; }
.job-item-company { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.job-item-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.job-item-meta { font-size: 13px; color: var(--text-tertiary); }

.type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.type-tag {
  padding: 6px 14px;
  font-size: 14px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.type-tag.active {
  background: var(--blue-light);
  color: var(--blue);
  border-color: var(--blue);
}

.generate-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}

.generate-btn:hover:not(:disabled) { background: #0077ed; }
.generate-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

/* Session */
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.session-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.session-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.close-btn {
  font-size: 22px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: 0 4px;
}

.question-area { margin-bottom: 20px; }

.question-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: var(--blue);
  background: var(--blue-light);
  padding: 3px 10px;
  border-radius: 980px;
  margin-bottom: 12px;
}

.question-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 16px;
}

.answer-input {
  width: 100%;
  padding: 14px 16px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
  transition: border-color 0.2s ease;
}

.answer-input:focus { border-color: var(--blue); background: var(--bg-white); }

.question-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.submit-btn {
  padding: 12px 28px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

.submit-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

.skip-btn {
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

/* Feedback */
.feedback-area {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 20px;
  margin-top: 16px;
}

.feedback-score {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.score-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.score-circle.high { background: var(--green); }
.score-circle.medium { background: var(--orange); }
.score-circle.low { background: var(--red); }
.score-circle.large { width: 80px; height: 80px; font-size: 28px; }

.feedback-content { flex: 1; }
.feedback-title { font-size: 16px; font-weight: 600; margin-bottom: 10px; }

.point-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  padding: 4px 0;
}

.point-icon { flex-shrink: 0; font-size: 12px; }
.point-item .point-icon.good { color: var(--green); }
.point-item .point-icon.bad { color: var(--red); }
.point-item .point-icon.neutral { color: var(--blue); }

.feedback-suggestion {
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--bg-white);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.next-btn {
  margin-top: 16px;
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

/* Completed */
.completed-area {
  text-align: center;
  padding: 32px 20px;
}

.completed-icon { font-size: 48px; margin-bottom: 12px; }
.completed-area h3 { font-size: 22px; font-weight: 700; margin-bottom: 20px; }

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.score-label { font-size: 14px; color: var(--text-secondary); margin-top: 8px; }

.answer-list {
  text-align: left;
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-item {
  background: var(--bg);
  border-radius: 10px;
  padding: 16px;
}

.answer-q {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.answer-a {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 6px;
}

.answer-score {
  font-size: 13px;
  font-weight: 600;
  color: var(--blue);
}

.new-session-btn {
  margin-top: 16px;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

/* History */
.history-section { margin-top: 24px; }

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow);
}

.history-info { flex: 1; }
.history-company { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.history-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.history-score {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: var(--text-tertiary);
  font-size: 15px;
}

.loading { text-align: center; padding: 24px; color: var(--text-tertiary); }
</style>
