<template>
  <div class="applications-page">
    <div class="page-header">
      <h1>投递追踪</h1>
      <p>管理你的求职进度，把握每一个机会</p>
    </div>

    <!-- Stats -->
    <div class="stats-bar">
      <div class="stat-item" v-for="(count, status) in stats" :key="status" :class="{ highlight: count > 0 }">
        <div class="stat-num">{{ count }}</div>
        <div class="stat-label">{{ formatStatusLabel(status) }}</div>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="filter-tabs">
      <button :class="['tab', { active: filterStatus === 'all' }]" @click="filterStatus = 'all'">全部</button>
      <button :class="['tab', { active: filterStatus === 'applied' }]" @click="filterStatus = 'applied'">已投递</button>
      <button :class="['tab', { active: filterStatus === 'screening' }]" @click="filterStatus = 'screening'">筛选中</button>
      <button :class="['tab', { active: filterStatus === 'interview_invited' }]" @click="filterStatus = 'interview_invited'">面试</button>
      <button :class="['tab', { active: filterStatus === 'offer' }]" @click="filterStatus = 'offer'">Offer</button>
      <button :class="['tab', { active: filterStatus === 'rejected' }]" @click="filterStatus = 'rejected'">拒绝</button>
    </div>

    <!-- Application List -->
    <div v-if="applications.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无投递记录</p>
      <router-link to="/jobs" class="empty-link">去匹配岗位</router-link>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="app-list">
      <div v-for="app in filteredApps" :key="app.id" class="app-card">
        <div class="app-header">
          <div class="app-company">{{ app.job?.company || '未知公司' }}</div>
          <div class="app-status" :class="app.status">{{ formatStatus(app.status) }}</div>
        </div>
        <div class="app-title">{{ app.job?.title || '未知岗位' }}</div>
        <div class="app-meta">
          <span>📍 {{ app.job?.location || '' }}</span>
          <span v-if="app.match_score">· 匹配 {{ app.match_score }}</span>
          <span v-if="app.applied_at">· {{ formatDate(app.applied_at) }}</span>
        </div>
        <div class="app-actions">
          <select v-if="app.status !== 'offer' && app.status !== 'rejected'" v-model="app.status" @change="updateStatus(app)">
            <option value="draft">草稿</option>
            <option value="applied">已投递</option>
            <option value="screening">筛选中</option>
            <option value="written_test">笔试</option>
            <option value="interview_invited">面试</option>
            <option value="offer">Offer</option>
            <option value="rejected">拒绝</option>
          </select>
          <button
            class="btn-interview"
            v-if="app.job?.id"
            @click="goToInterview(app.job.id)"
          >
            🎯 模拟面试
          </button>
          <button class="btn-apply" v-if="!app.job?.apply_url" @click="applyToJob(app)">去投递</button>
          <a v-else-if="app.job?.apply_url" :href="app.job.apply_url" target="_blank" class="btn-apply">去投递</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { applicationApi } from '../api/index.js'

export default {
  name: 'ApplicationsView',
  data() {
    return {
      applications: [],
      loading: false,
      filterStatus: 'all'
    }
  },
  computed: {
    stats() {
      const s = { draft: 0, applied: 0, screening: 0, written_test: 0, interview_invited: 0, offer: 0, rejected: 0 }
      for (const app of this.applications) {
        if (s[app.status] !== undefined) s[app.status]++
      }
      return s
    },
    filteredApps() {
      if (this.filterStatus === 'all') return this.applications
      return this.applications.filter(a => a.status === this.filterStatus)
    }
  },
  async created() {
    await this.loadApplications()
  },
  methods: {
    async loadApplications() {
      this.loading = true
      try {
        this.applications = await applicationApi.listApplications()
      } catch (e) {
        console.error('加载投递记录失败', e)
      } finally {
        this.loading = false
      }
    },
    async updateStatus(app) {
      try {
        await applicationApi.updateStatus(app.id, app.status)
      } catch (e) {
        console.error('更新状态失败', e)
      }
    },
    async applyToJob(app) {
      const profileId = localStorage.getItem('profileId')
      if (!profileId) {
        alert('请先上传简历')
        return
      }
      try {
        await applicationApi.applyJob(app.job?.id || app.job_id, profileId)
        await this.loadApplications()
      } catch (e) {
        console.error('投递失败', e)
      }
    },
    goToInterview(jobId) {
      this.$router.push({ path: '/interview', query: { jobId } })
    },
    formatStatus(status) {
      const map = { draft: '草稿', applied: '已投递', screening: '筛选中', written_test: '笔试', interview_invited: '面试', offer: 'Offer', rejected: '拒绝', withdrawn: '已撤回' }
      return map[status] || status
    },
    formatStatusLabel(status) {
      return this.formatStatus(status)
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.applications-page {
  max-width: 980px;
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

/* Stats */
.stats-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-item {
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  padding: 14px 20px;
  text-align: center;
  box-shadow: var(--shadow);
  min-width: 80px;
  transition: all 0.2s ease;
}

.stat-item.highlight {
  background: var(--blue-light);
}

.stat-num {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  background: var(--bg-white);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.tab.active {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
}

/* App List */
.app-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.app-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 18px 22px;
  box-shadow: var(--shadow);
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.app-company {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

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

.app-title {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.app-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.app-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.app-actions select {
  padding: 8px 12px;
  font-size: 14px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
  color: var(--text-primary);
  font-family: inherit;
  cursor: pointer;
}

.btn-apply {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  text-decoration: none;
  font-family: inherit;
}

.btn-interview {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
}

.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; margin-bottom: 12px; }
.empty-link { font-size: 14px; color: var(--blue); text-decoration: none; }

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }
</style>
