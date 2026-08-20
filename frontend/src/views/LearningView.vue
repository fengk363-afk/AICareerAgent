<template>
  <div class="learning-page">
    <div class="page-header">
      <h1>学习路线</h1>
      <p>基于你的简历和目标岗位，生成个性化能力提升计划</p>
    </div>

    <!-- 选择简历和岗位 -->
    <div class="selector-card">
      <div class="selector-row">
        <div class="selector-group">
          <label class="selector-label">选择简历</label>
          <select v-model="selectedProfileId" class="selector-select">
            <option value="" disabled>请选择简历画像</option>
            <option v-for="p in profiles" :key="p.id" :value="p.id">
              {{ p.original_filename || '简历画像' }}
            </option>
          </select>
        </div>
        <div class="selector-group">
          <label class="selector-label">选择目标岗位</label>
          <select v-model="selectedJobId" class="selector-select">
            <option value="" disabled>请选择岗位</option>
            <option v-for="j in jobs" :key="j.id" :value="j.id">
              {{ j.company }} · {{ j.title }}
            </option>
          </select>
        </div>
      </div>
      <button class="generate-btn" @click="generatePlan" :disabled="!selectedProfileId || !selectedJobId || generating">
        {{ generating ? '生成中...' : '生成学习路线' }}
      </button>
    </div>

    <!-- 学习路线列表 -->
    <div v-if="plans.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">📚</div>
      <p>选择简历和岗位后，点击生成学习路线</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-for="plan in plans" :key="plan.id" class="plan-card">
      <div class="plan-header">
        <div>
          <div class="plan-title">{{ plan.job_title }} · 学习路线</div>
          <div class="plan-meta">{{ plan.company }} · {{ formatDate(plan.created_at) }}</div>
        </div>
        <div class="plan-score" :class="getScoreClass(plan.improvement_score || 0)">
          {{ plan.improvement_score || '-' }}
        </div>
      </div>

      <!-- 缺失技能 -->
      <div v-if="plan.missing_skills?.length" class="plan-section">
        <div class="section-title">缺失技能</div>
        <div class="skill-tags">
          <span v-for="s in plan.missing_skills" :key="s" class="skill-tag">{{ s }}</span>
        </div>
      </div>

      <!-- 已有技能 -->
      <div v-if="plan.existing_skills?.length" class="plan-section">
        <div class="section-title">已有技能</div>
        <div class="skill-tags">
          <span v-for="s in plan.existing_skills" :key="s" class="skill-tag existing">{{ s }}</span>
        </div>
      </div>

      <!-- 学习阶段 -->
      <div v-if="plan.stages?.length" class="plan-section">
        <div class="section-title">学习阶段</div>
        <div class="stages-list">
          <div v-for="(stage, idx) in plan.stages" :key="idx" class="stage-item">
            <div class="stage-num">{{ idx + 1 }}</div>
            <div class="stage-content">
              <div class="stage-title">{{ stage.title }}</div>
              <div class="stage-desc">{{ stage.description }}</div>
              <div class="stage-duration" v-if="stage.duration">⏱ {{ stage.duration }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 建议 -->
      <div v-if="plan.suggestions?.length" class="plan-section">
        <div class="section-title">建议</div>
        <ul class="suggest-list">
          <li v-for="(s, idx) in plan.suggestions" :key="idx">{{ s }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { learningApi, resumeApi, jobApi } from '../api/index.js'

export default {
  name: 'LearningView',
  data() {
    return {
      profiles: [],
      jobs: [],
      selectedProfileId: '',
      selectedJobId: '',
      plans: [],
      loading: false,
      generating: false
    }
  },
  async created() {
    await Promise.all([this.loadProfiles(), this.loadJobs()])
  },
  methods: {
    async loadProfiles() {
      try { this.profiles = await resumeApi.listProfiles() } catch (e) {}
    },
    async loadJobs() {
      try { this.jobs = await jobApi.listJobs({ limit: 50 }) } catch (e) {}
    },
    async generatePlan() {
      if (!this.selectedProfileId || !this.selectedJobId) return
      this.generating = true
      try {
        const result = await learningApi.generatePlan(this.selectedProfileId, this.selectedJobId)
        this.plans.unshift(result)
      } catch (e) {
        console.error('生成学习路线失败', e)
      } finally {
        this.generating = false
      }
    },
    getScoreClass(score) {
      if (score >= 70) return 'high'
      if (score >= 50) return 'medium'
      return 'low'
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleDateString('zh-CN')
    }
  }
}
</script>

<style scoped>
.learning-page {
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

.selector-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 24px;
}

.selector-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.selector-select {
  height: 44px;
  padding: 0 12px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  outline: none;
  font-family: inherit;
  color: var(--text-primary);
  cursor: pointer;
}

.selector-select:focus { border-color: var(--blue); }

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

.plan-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 16px;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.plan-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.plan-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.plan-score {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.plan-score.high { background: var(--green); }
.plan-score.medium { background: var(--orange); }
.plan-score.low { background: var(--red); }

.plan-section {
  margin-bottom: 20px;
}

.plan-section:last-child { margin-bottom: 0; }

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.skill-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 980px;
  background: #fff4e0;
  color: var(--orange);
}

.skill-tag.existing {
  background: var(--blue-light);
  color: var(--blue);
}

.stages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.stage-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--blue);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.stage-content { flex: 1; }
.stage-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.stage-desc { font-size: 14px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
.stage-duration { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }

.suggest-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggest-list li {
  font-size: 14px;
  color: var(--text-secondary);
  padding-left: 16px;
  position: relative;
  line-height: 1.5;
}

.suggest-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--blue);
}

.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; }

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }

@media (max-width: 734px) {
  .selector-row {
    grid-template-columns: 1fr;
  }
}
</style>
