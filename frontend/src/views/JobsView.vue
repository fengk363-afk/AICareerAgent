<template>
  <div class="jobs-page">
    <div class="page-header">
      <h1>岗位匹配</h1>
      <p>发现适合你的机会，AI 精准匹配</p>
    </div>

    <!-- 搜索 -->
    <div class="search-bar">
      <input v-model="searchKeyword" type="text" placeholder="搜索岗位、公司..." class="search-input" @keyup.enter="searchJobs" />
      <button class="search-btn" @click="searchJobs">搜索</button>
    </div>

    <!-- 筛选 -->
    <div class="filters">
      <button :class="['filter-btn', { active: filterRemote }]" @click="filterRemote = !filterRemote">🏠 远程</button>
      <button :class="['filter-btn', { active: filterForeign }]" @click="filterForeign = !filterForeign">🌍 外企</button>
      <button :class="['filter-btn', { active: filterCampus }]" @click="filterCampus = !filterCampus">🎓 校招</button>
      <button :class="['filter-btn', { active: filterOverseas }]" @click="filterOverseas = !filterOverseas">✈️ 海外</button>
    </div>

    <!-- 排序 -->
    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <button
        v-for="opt in sortOptions"
        :key="opt.value"
        :class="['sort-btn', { active: sortBy === opt.value }]"
        @click="sortBy = opt.value"
      >
        {{ opt.label }}
      </button>
      <span class="job-count" v-if="!loading">{{ jobs.length }} 个岗位</span>
    </div>

    <!-- 岗位列表 -->
    <div v-if="jobs.length === 0 && !loading" class="empty-state">
      <p>暂无岗位，点击初始化</p>
      <button class="init-btn" @click="initJobs">初始化岗位数据</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="job-list">
      <div
        v-for="job in jobs"
        :key="job.id"
        class="job-card"
        @click="goToDetail(job)"
      >
        <div class="job-header">
          <div class="job-company">{{ job.company }}</div>
          <div class="job-tags">
            <span v-if="job.is_remote" class="tag remote">远程</span>
            <span v-if="job.is_foreign" class="tag foreign">外企</span>
            <span v-if="job.campus_recruitment" class="tag campus">校招</span>
            <span v-if="job.season" class="tag season">{{ job.season }}</span>
          </div>
        </div>
        <div class="job-title">{{ job.title }}</div>
        <div class="job-meta">
          <span>📍 {{ job.location }}</span>
          <span v-if="job.salary_range">· 💰 {{ job.salary_range.min }}-{{ job.salary_range.max }}K</span>
        </div>
        <div class="job-desc">{{ truncate(job.description, 100) }}</div>
        <div class="job-footer">
          <div class="job-tags-row">
            <span v-for="skill in (job.preferred_skills || []).slice(0, 3)" :key="skill" class="mini-tag">{{ skill }}</span>
          </div>
          <div class="job-actions" @click.stop>
            <button
              class="btn-save"
              :class="{ saved: isSaved(job.id) }"
              @click="toggleSave(job)"
            >
              {{ isSaved(job.id) ? '✓ 已收藏' : '☆ 收藏' }}
            </button>
            <router-link :to="`/jobs/${job.id}`" class="btn-detail">查看详情</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { jobApi } from '../api/index.js'

export default {
  name: 'JobsView',
  data() {
    return {
      jobs: [],
      loading: false,
      searchKeyword: '',
      filterRemote: false,
      filterForeign: false,
      filterCampus: false,
      filterOverseas: false,
      sortBy: 'default',
      sortOptions: [
        { label: '默认', value: 'default' },
        { label: '匹配度', value: 'match' },
        { label: '薪资', value: 'salary' },
        { label: '最新', value: 'latest' }
      ],
      savedJobs: new Set()
    }
  },
  async created() {
    await this.loadJobs()
    await this.loadSavedJobs()
  },
  methods: {
    async loadJobs() {
      this.loading = true
      try {
        const params = { keyword: this.searchKeyword || undefined }
        if (this.filterRemote) params.is_remote = true
        if (this.filterForeign) params.is_foreign = true
        if (this.filterCampus) params.campus_recruitment = true
        if (this.filterOverseas) params.visa_support = true
        this.jobs = await jobApi.listJobs(params)
        if (this.sortBy === 'salary') {
          this.jobs.sort((a, b) => (b.salary_range?.max || 0) - (a.salary_range?.max || 0))
        } else if (this.sortBy === 'latest') {
          this.jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        }
      } catch (e) {
        console.error('加载岗位失败', e)
      } finally {
        this.loading = false
      }
    },
    async loadSavedJobs() {
      try {
        const saved = await jobApi.getSavedJobs()
        this.savedJobs = new Set(saved.map(j => j.job_id))
      } catch (e) {}
    },
    async searchJobs() {
      await this.loadJobs()
    },
    async toggleSave(job) {
      if (this.savedJobs.has(job.id)) {
        await jobApi.removeSavedJob(job.id)
        this.savedJobs.delete(job.id)
      } else {
        await jobApi.saveJob(job.id)
        this.savedJobs.add(job.id)
      }
    },
    isSaved(jobId) {
      return this.savedJobs.has(jobId)
    },
    goToDetail(job) {
      this.$router.push(`/jobs/${job.id}`)
    },
    async initJobs() {
      try {
        await jobApi.seedJobs()
        await this.loadJobs()
      } catch (e) {
        console.error('初始化失败', e)
      }
    },
    truncate(str, len) {
      return str && str.length > len ? str.slice(0, len) + '...' : str || ''
    }
  }
}
</script>

<style scoped>
.jobs-page {
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

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.search-input {
  flex: 1;
  height: 48px;
  padding: 0 16px;
  font-size: 17px;
  background: var(--bg-white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  outline: none;
  font-family: inherit;
}

.search-input:focus { border-color: var(--blue); }

.search-btn {
  height: 48px;
  padding: 0 24px;
  font-size: 17px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
}

.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.filter-btn {
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

.filter-btn.active {
  background: var(--blue-light);
  color: var(--blue);
  border-color: var(--blue);
}

.sort-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  font-size: 14px;
}

.sort-label { color: var(--text-tertiary); }

.sort-btn {
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg-white);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.sort-btn.active {
  background: var(--blue);
  color: #fff;
  border-color: var(--blue);
}

.job-count {
  margin-left: auto;
  font-size: 13px;
  color: var(--text-tertiary);
}

.job-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 22px 24px;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: all 0.2s ease;
}

.job-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.job-company {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
}

.job-tags {
  display: flex;
  gap: 6px;
}

.tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
}

.tag.remote { background: #e8f8ec; color: var(--green); }
.tag.foreign { background: var(--blue-light); color: var(--blue); }
.tag.campus { background: #f3e8ff; color: #7c3aed; }
.tag.season { background: #fff4e0; color: var(--orange); }

.job-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}

.job-meta {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.job-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.55;
  margin-bottom: 12px;
}

.job-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-tags-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.mini-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
  background: var(--bg);
  color: var(--text-secondary);
}

.job-actions {
  display: flex;
  gap: 8px;
}

.btn-save {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  text-decoration: none;
  transition: all 0.15s ease;
}

.btn-save.saved {
  background: #fff4e0;
  color: var(--orange);
  border-color: var(--orange);
}

.btn-detail {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  background: var(--blue-light);
  color: var(--blue);
  border: none;
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  text-decoration: none;
}

.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
}

.empty-state p { font-size: 15px; margin-bottom: 16px; }

.init-btn {
  padding: 10px 24px;
  font-size: 15px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }
</style>
