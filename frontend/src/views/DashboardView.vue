<template>
  <div class="dashboard-page">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-left">
        <h1 class="welcome-title">你好，{{ userStore.userName }} 👋</h1>
        <p class="welcome-subtitle">今天也是努力求职的一天，加油！</p>
      </div>
      <div class="welcome-right">
        <div class="date-display">{{ currentDate }}</div>
        <div class="streak-display" v-if="stats.study_streak > 0">
          🔥 {{ stats.study_streak }} 天学习 streak
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <router-link to="/resume" class="stat-card">
        <div class="stat-icon" style="background: #e8f2ff;">📄</div>
        <div class="stat-value">{{ stats.resume_count || 0 }}</div>
        <div class="stat-label">简历</div>
        <div class="stat-sub" v-if="stats.resume_completion > 0">完成度 {{ stats.resume_completion }}%</div>
      </router-link>
      <router-link to="/jobs" class="stat-card">
        <div class="stat-icon" style="background: #e8f8ec;">💼</div>
        <div class="stat-value">{{ stats.recommended_jobs || 0 }}</div>
        <div class="stat-label">推荐岗位</div>
        <div class="stat-sub">基于你的简历</div>
      </router-link>
      <router-link to="/applications" class="stat-card">
        <div class="stat-icon" style="background: #fff4e0;">📊</div>
        <div class="stat-value">{{ stats.applied_count || 0 }}</div>
        <div class="stat-label">已投递</div>
        <div class="stat-sub">{{ stats.screening_count || 0 }} 筛选中</div>
      </router-link>
      <router-link to="/interview" class="stat-card">
        <div class="stat-icon" style="background: #ffeaea;">🎯</div>
        <div class="stat-value">{{ stats.interview_count || 0 }}</div>
        <div class="stat-label">模拟面试</div>
        <div class="stat-sub" v-if="stats.last_interview_date">最近 {{ stats.last_interview_date }}</div>
        <div class="stat-sub" v-else>暂无记录</div>
      </router-link>
    </div>

    <!-- Resume Progress -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">简历完成度</h2>
        <router-link to="/resume" class="section-link">去完善 →</router-link>
      </div>
      <div class="resume-progress-card" :class="{ 'complete': stats.resume_completion >= 80 }">
        <div class="progress-header">
          <span class="progress-label">整体完成度</span>
          <span class="progress-value" :style="{ color: progressColor }">{{ stats.resume_completion || 0 }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (stats.resume_completion || 0) + '%', background: progressColor }"></div>
        </div>
        <div class="progress-tips" v-if="stats.resume_completion < 80">
          <span v-if="!stats.has_summary" class="tip-item">⚠️ 缺少个人总结</span>
          <span v-if="!stats.has_education" class="tip-item">⚠️ 缺少教育背景</span>
          <span v-if="!stats.has_experience" class="tip-item">⚠️ 缺少工作经历</span>
          <span v-if="!stats.has_skills" class="tip-item">⚠️ 缺少技能描述</span>
          <span v-if="stats.resume_completion >= 50 && stats.resume_completion < 80" class="tip-item good">✓ 基础信息已完善</span>
        </div>
        <div class="progress-tips" v-else>
          <span class="tip-item good">✓ 简历已完成，可以开始投递了！</span>
        </div>
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="two-col">
      <!-- Recent Applications -->
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">最近投递</h2>
          <router-link to="/applications" class="section-link">查看全部 →</router-link>
        </div>
        <div v-if="recentApps.length === 0" class="empty-state">
          <p>暂无投递记录</p>
          <router-link to="/jobs" class="empty-link">去匹配岗位</router-link>
        </div>
        <div v-else class="app-list">
          <div v-for="app in recentApps.slice(0, 5)" :key="app.id" class="app-item">
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

      <!-- Interview Status -->
      <div class="section">
        <div class="section-header">
          <h2 class="section-title">面试状态</h2>
          <router-link to="/interview" class="section-link">去练习 →</router-link>
        </div>
        <div v-if="interviewStats.total_sessions === 0" class="empty-state">
          <p>暂无模拟面试记录</p>
          <router-link to="/interview" class="empty-link">开始第一次面试</router-link>
        </div>
        <div v-else class="interview-stats">
          <div class="interview-summary">
            <div class="interview-num">
              <div class="interview-num-value">{{ interviewStats.total_sessions }}</div>
              <div class="interview-num-label">总次数</div>
            </div>
            <div class="interview-num">
              <div class="interview-num-value">{{ interviewStats.avg_score?.toFixed(1) || '-' }}</div>
              <div class="interview-num-label">平均评分</div>
            </div>
            <div class="interview-num">
              <div class="interview-num-value">{{ interviewStats.improved_count || 0 }}</div>
              <div class="interview-num-label">有进步</div>
            </div>
          </div>
          <div class="interview-tip" v-if="interviewStats.latest_feedback">
            <div class="tip-label">💡 最新建议</div>
            <div class="tip-text">{{ interviewStats.latest_feedback }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user.js'
import { applicationApi, interviewApi } from '../api/index.js'

const userStore = useUserStore()

const stats = ref({
  resume_count: 0,
  resume_completion: 0,
  recommended_jobs: 0,
  applied_count: 0,
  screening_count: 0,
  interview_count: 0,
  offer_count: 0,
  study_streak: 0
})

const recentApps = ref([])
const interviewStats = ref({
  total_sessions: 0,
  avg_score: 0,
  improved_count: 0,
  latest_feedback: ''
})

const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

const progressColor = computed(() => {
  const p = stats.value.resume_completion || 0
  if (p >= 80) return 'var(--green)'
  if (p >= 50) return 'var(--orange)'
  return 'var(--red)'
})

onMounted(async () => {
  await loadDashboard()
  await loadInterviewStats()
})

async function loadDashboard() {
  try {
    const data = await applicationApi.getDashboard()
    stats.value = {
      resume_count: data.stats?.resume_count || 0,
      resume_completion: data.stats?.resume_completion || 0,
      recommended_jobs: data.stats?.recommended_jobs || 0,
      applied_count: data.stats?.applied_count || 0,
      screening_count: data.stats?.screening_count || 0,
      interview_count: data.stats?.interview_count || 0,
      offer_count: data.stats?.offer_count || 0,
      study_streak: data.stats?.study_streak || 0,
      has_summary: data.stats?.has_summary,
      has_education: data.stats?.has_education,
      has_experience: data.stats?.has_experience,
      has_skills: data.stats?.has_skills,
      last_interview_date: data.stats?.last_interview_date
    }
    recentApps.value = data.recent_applications || []
  } catch (e) {
    console.error('加载Dashboard数据失败', e)
  }
}

async function loadInterviewStats() {
  try {
    const data = await interviewApi.getStats()
    interviewStats.value = {
      total_sessions: data.total_sessions || 0,
      avg_score: data.avg_score,
      improved_count: data.improved_count || 0,
      latest_feedback: data.latest_feedback || ''
    }
  } catch (e) {
    console.error('加载面试数据失败', e)
  }
}

function formatStatus(status) {
  const map = {
    draft: '草稿', applied: '已投递', screening: '筛选中',
    written_test: '笔试', interview_invited: '面试', offer: 'Offer',
    rejected: '拒绝', withdrawn: '已撤回'
  }
  return map[status] || status
}
</script>

<style scoped>
.dashboard-page {
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

.welcome-left h1 {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}

.welcome-subtitle {
  font-size: 15px;
  opacity: 0.85;
}

.welcome-right {
  text-align: right;
}

.date-display {
  font-size: 14px;
  opacity: 0.8;
}

.streak-display {
  font-size: 13px;
  opacity: 0.7;
  margin-top: 4px;
}

/* Stats Grid */
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

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stat-sub {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* Section */
.section {
  margin-bottom: 28px;
}

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

/* Resume Progress */
.resume-progress-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
}

.resume-progress-card.complete {
  border: 2px solid var(--green);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.progress-value {
  font-size: 20px;
  font-weight: 700;
}

.progress-bar {
  height: 8px;
  background: var(--bg);
  border-radius: 980px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  border-radius: 980px;
  transition: width 0.5s ease;
}

.progress-tips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tip-item {
  font-size: 13px;
  color: var(--orange);
  background: #fff4e0;
  padding: 4px 10px;
  border-radius: 980px;
}

.tip-item.good {
  color: var(--green);
  background: #e8f8ec;
}

/* Two Column */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

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

/* Interview Stats */
.interview-stats {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px 28px;
  box-shadow: var(--shadow);
}

.interview-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.interview-num {
  text-align: center;
  flex: 1;
}

.interview-num-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.interview-num-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.interview-tip {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}

.tip-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.tip-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
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

/* Empty */
.empty-state {
  text-align: center;
  padding: 32px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.empty-state p { font-size: 15px; margin-bottom: 10px; }
.empty-link { font-size: 14px; color: var(--blue); text-decoration: none; }

/* Responsive */
@media (max-width: 734px) {
  .welcome-banner { flex-direction: column; gap: 12px; text-align: center; }
  .welcome-right { text-align: center; }
  .stats-grid, .action-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
</style>
