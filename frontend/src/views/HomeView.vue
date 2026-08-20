<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h1>你好，{{ userName }} 👋</h1>
        <p>今天也是努力求职的一天，加油！</p>
      </div>
      <div class="welcome-date">{{ currentDate }}</div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <router-link to="/resume" class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-value">{{ stats.resume_count }}</div>
        <div class="stat-label">简历</div>
      </router-link>
      <router-link to="/applications" class="stat-card">
        <div class="stat-icon">💼</div>
        <div class="stat-value">{{ stats.applied_count }}</div>
        <div class="stat-label">已投递</div>
      </router-link>
      <router-link to="/applications" class="stat-card">
        <div class="stat-icon">📞</div>
        <div class="stat-value">{{ stats.interview_count }}</div>
        <div class="stat-label">面试</div>
      </router-link>
      <router-link to="/applications" class="stat-card">
        <div class="stat-icon">🏆</div>
        <div class="stat-value">{{ stats.offer_count }}</div>
        <div class="stat-label">Offer</div>
      </router-link>
    </div>

    <!-- 快捷入口 -->
    <div class="section">
      <div class="section-title">快捷入口</div>
      <div class="action-grid">
        <router-link to="/resume" class="action-card">
          <div class="action-icon">📄</div>
          <div class="action-text">简历管理</div>
        </router-link>
        <router-link to="/jobs" class="action-card">
          <div class="action-icon">💼</div>
          <div class="action-text">岗位匹配</div>
        </router-link>
        <router-link to="/applications" class="action-card">
          <div class="action-icon">📊</div>
          <div class="action-text">投递追踪</div>
        </router-link>
        <router-link to="/interview" class="action-card">
          <div class="action-icon">🎯</div>
          <div class="action-text">面试教练</div>
        </router-link>
        <router-link to="/agent" class="action-card">
          <div class="action-icon">🤖</div>
          <div class="action-text">AI 顾问</div>
        </router-link>
        <router-link to="/learning" class="action-card">
          <div class="action-icon">📚</div>
          <div class="action-text">学习路线</div>
        </router-link>
        <router-link to="/goals" class="action-card">
          <div class="action-icon">🎯</div>
          <div class="action-text">职业目标</div>
        </router-link>
        <router-link to="/company" class="action-card">
          <div class="action-icon">🏢</div>
          <div class="action-text">公司研究</div>
        </router-link>
      </div>
    </div>

    <!-- 最近投递 -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">最近投递</h2>
        <router-link to="/applications" class="section-link">查看全部</router-link>
      </div>
      <div v-if="recentApps.length === 0" class="empty-state">
        <p>暂无投递记录</p>
        <router-link to="/jobs" class="empty-link">去匹配岗位</router-link>
      </div>
      <div v-else class="app-list">
        <div v-for="app in recentApps" :key="app.id" class="app-item">
          <div class="app-info">
            <div class="app-company">{{ app.job?.company || '未知公司' }}</div>
            <div class="app-title">{{ app.job?.title || '未知岗位' }}</div>
          </div>
          <div class="app-status" :class="app.status">{{ formatStatus(app.status) }}</div>
          <div class="app-score" v-if="app.match_score">
            匹配 {{ app.match_score }}
          </div>
        </div>
      </div>
    </div>

    <!-- 待办提醒 -->
    <div class="section" v-if="tasks.length > 0">
      <div class="section-header">
        <h2 class="section-title">今日待办</h2>
        <router-link to="/agent" class="section-link">更多</router-link>
      </div>
      <div class="task-list">
        <div v-for="(task, idx) in tasks" :key="idx" class="task-item">
          <span class="task-check">{{ task.done ? '✓' : '○' }}</span>
          <span :class="['task-text', { done: task.done }]">{{ task.text }}</span>
          <span class="task-priority" :class="task.priority">{{ task.priority_label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { applicationApi, agentApi } from '../api/index.js'
import { useUserStore } from '../stores/user.js'

export default {
  name: 'HomeView',
  setup() {
    const userStore = useUserStore()
    return { userStore }
  },
  data() {
    return {
      stats: { resume_count: 0, applied_count: 0, interview_count: 0, offer_count: 0 },
      recentApps: [],
      tasks: []
    }
  },
  computed: {
    userName() {
      return this.userStore.userName
    },
    currentDate() {
      return new Date().toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      })
    }
  },
  async created() {
    await this.loadDashboard()
    await this.loadTasks()
  },
  methods: {
    async loadDashboard() {
      try {
        const data = await applicationApi.getDashboard()
        this.stats = data.stats || {}
        this.recentApps = data.recent_applications || []
      } catch (e) {
        console.error('加载首页数据失败', e)
      }
    },
    async loadTasks() {
      try {
        this.tasks = await agentApi.getDailyTasks()
      } catch (e) {}
    },
    formatStatus(status) {
      const map = {
        draft: '草稿', applied: '已投递', screening: '筛选中',
        written_test: '笔试', interview_invited: '面试', offer: 'Offer',
        rejected: '拒绝', withdrawn: '已撤回'
      }
      return map[status] || status
    }
  }
}
</script>

<style scoped>
.home-page {
  max-width: 980px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

/* Welcome Banner */
.welcome-banner {
  background: linear-gradient(135deg, #0071e3 0%, #40a0ff 100%);
  border-radius: var(--radius);
  padding: 28px 32px;
  margin-bottom: 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
}

.welcome-text h1 {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}

.welcome-text p {
  font-size: 15px;
  opacity: 0.85;
}

.welcome-date {
  font-size: 14px;
  opacity: 0.8;
  text-align: right;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  box-shadow: var(--shadow);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; letter-spacing: -0.02em; }
.stat-label { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }

/* Section */
.section { margin-bottom: 28px; }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.section-link {
  font-size: 14px;
  color: var(--blue);
  text-decoration: none;
}

/* Action Grid */
.action-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.action-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px 16px;
  text-align: center;
  text-decoration: none;
  color: var(--text-primary);
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.action-icon { font-size: 30px; margin-bottom: 10px; }
.action-text { font-size: 14px; font-weight: 500; color: var(--text-secondary); }

/* App List */
.app-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.app-item {
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow);
  text-decoration: none;
  color: inherit;
}

.app-info { flex: 1; }
.app-company { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.app-title { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.app-status {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 980px;
  background: var(--bg);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.app-status.applied { background: var(--blue-light); color: var(--blue); }
.app-status.screening { background: #fff4e0; color: var(--orange); }
.app-status.interview_invited { background: #e8f8ec; color: var(--green); }
.app-status.offer { background: #e8f8ec; color: var(--green); }
.app-status.rejected { background: #ffeaea; color: var(--red); }

.app-score {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

/* Task List */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
}

.task-check { font-size: 14px; flex-shrink: 0; }
.task-text { flex: 1; font-size: 14px; color: var(--text-primary); }
.task-text.done { text-decoration: line-through; opacity: 0.5; }

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

/* Empty */
.empty-state {
  text-align: center;
  padding: 32px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
}

.empty-state p { font-size: 15px; margin-bottom: 10px; }
.empty-link { font-size: 14px; color: var(--blue); text-decoration: none; }

/* Responsive */
@media (max-width: 734px) {
  .welcome-banner { flex-direction: column; gap: 12px; text-align: center; }
  .welcome-date { text-align: center; }
  .stats-grid, .action-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
