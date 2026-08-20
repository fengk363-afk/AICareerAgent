<template>
  <div class="job-detail-page">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!job" class="empty-state">
      <p>岗位不存在</p>
      <router-link to="/jobs" class="empty-link">返回岗位列表</router-link>
    </div>
    <div v-else class="job-detail">
      <!-- 返回按钮 -->
      <router-link to="/jobs" class="back-btn">← 返回岗位列表</router-link>

      <!-- 基本信息 -->
      <div class="detail-header">
        <div class="detail-company">{{ job.company }}</div>
        <div class="detail-tags">
          <span v-if="job.is_remote" class="tag remote">远程</span>
          <span v-if="job.is_foreign" class="tag foreign">外企</span>
          <span v-if="job.company_type" class="tag">{{ job.company_type }}</span>
          <span v-if="job.season" class="tag season">{{ job.season }}</span>
        </div>
      </div>
      <h1 class="detail-title">{{ job.title }}</h1>
      <div class="detail-meta">
        <span>📍 {{ job.location }}</span>
        <span v-if="job.salary_range">💰 {{ job.salary_range.min }}-{{ job.salary_range.max }}K</span>
        <span v-if="job.job_type">{{ job.job_type }}</span>
        <span v-if="job.posted_at">📅 {{ formatDate(job.posted_at) }}</span>
      </div>

      <!-- 操作按钮 -->
      <div class="detail-actions">
        <button class="btn-apply" v-if="job.apply_url" :href="job.apply_url" target="_blank">
          立即投递 →
        </button>
        <button class="btn-apply" v-else @click="applyNow">
          一键投递
        </button>
        <button
          class="btn-save"
          :class="{ saved: isSaved }"
          @click="toggleSave"
        >
          {{ isSaved ? '✓ 已收藏' : '☆ 收藏' }}
        </button>
        <button class="btn-interview" @click="startInterview">
          🎯 模拟面试
        </button>
      </div>

      <!-- 匹配度 -->
      <div v-if="matchResult" class="match-section">
        <div class="match-header">
          <h3>匹配度分析</h3>
          <div class="match-score" :class="getScoreClass(matchResult.overall_score)">
            {{ matchResult.overall_score }}
          </div>
        </div>
        <div class="match-bars">
          <div class="match-bar">
            <span class="match-label">技能匹配</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: matchResult.skill_match + '%', background: getScoreColor(matchResult.skill_match) }"></div>
            </div>
            <span class="match-val">{{ matchResult.skill_match }}</span>
          </div>
          <div class="match-bar">
            <span class="match-label">经历匹配</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: matchResult.experience_match + '%', background: getScoreColor(matchResult.experience_match) }"></div>
            </div>
            <span class="match-val">{{ matchResult.experience_match }}</span>
          </div>
          <div class="match-bar">
            <span class="match-label">学历匹配</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: matchResult.education_match + '%', background: getScoreColor(matchResult.education_match) }"></div>
            </div>
            <span class="match-val">{{ matchResult.education_match }}</span>
          </div>
        </div>
        <div v-if="matchResult.gaps?.length" class="gap-section">
          <div class="gap-title">技能差距</div>
          <div class="gap-tags">
            <span v-for="g in matchResult.gaps" :key="g" class="gap-tag">{{ g }}</span>
          </div>
        </div>
        <div v-if="matchResult.strengths?.length" class="gap-section">
          <div class="gap-title">你的优势</div>
          <div class="gap-tags">
            <span v-for="s in matchResult.strengths" :key="s" class="gap-tag good">{{ s }}</span>
          </div>
        </div>
        <div v-if="matchResult.suggestions?.length" class="gap-section">
          <div class="gap-title">优化建议</div>
          <ul class="suggest-list">
            <li v-for="s in matchResult.suggestions" :key="s">{{ s }}</li>
          </ul>
        </div>
      </div>
      <div v-else class="match-section">
        <button class="calc-match-btn" @click="calcMatch" :disabled="!profileId || matchLoading">
          {{ matchLoading ? '计算中...' : '计算匹配度' }}
        </button>
      </div>

      <!-- 岗位详情 -->
      <div class="detail-section">
        <h3>岗位描述</h3>
        <div class="detail-text">{{ job.description }}</div>
      </div>

      <div v-if="job.requirements?.length" class="detail-section">
        <h3>任职要求</h3>
        <ul class="require-list">
          <li v-for="(r, idx) in job.requirements" :key="idx">{{ r }}</li>
        </ul>
      </div>

      <div v-if="job.preferred_skills?.length" class="detail-section">
        <h3>优先技能</h3>
        <div class="skill-tags">
          <span v-for="s in job.preferred_skills" :key="s" class="skill-tag">{{ s }}</span>
        </div>
      </div>

      <!-- 公司信息 -->
      <div v-if="job.company_website" class="detail-section">
        <h3>公司信息</h3>
        <a :href="job.company_website" target="_blank" class="company-link">
          {{ job.company_website }} →
        </a>
      </div>

      <!-- 差距分析 -->
      <div v-if="gapResult" class="detail-section gap-section">
        <h3>能力差距分析</h3>
        <div v-if="gapResult.missing_skills?.length" class="gap-tags">
          <span v-for="s in gapResult.missing_skills" :key="s" class="gap-tag">{{ s }}</span>
        </div>
        <div v-if="gapResult.suggestions?.length" class="suggest-list">
          <li v-for="s in gapResult.suggestions" :key="s">{{ s }}</li>
        </div>
      </div>
      <div v-else class="detail-section">
        <button class="calc-match-btn" @click="calcGap" :disabled="!profileId || gapLoading">
          {{ gapLoading ? '分析中...' : '能力差距分析' }}
        </button>
      </div>

      <!-- 学习路线 -->
      <div class="detail-section">
        <button class="calc-match-btn" @click="goToLearning" :disabled="!profileId">
          📚 生成学习路线
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { jobApi, applicationApi, gapApi, learningApi } from '../api/index.js'

export default {
  name: 'JobDetailView',
  data() {
    return {
      job: null,
      loading: false,
      matchResult: null,
      matchLoading: false,
      gapResult: null,
      gapLoading: false,
      isSaved: false,
      profileId: localStorage.getItem('profileId') || ''
    }
  },
  async created() {
    await this.loadJob()
    await this.checkSaved()
  },
  methods: {
    async loadJob() {
      this.loading = true
      try {
        this.job = await jobApi.getJob(this.$route.params.id)
      } catch (e) {
        console.error('加载岗位失败', e)
      } finally {
        this.loading = false
      }
    },
    async checkSaved() {
      try {
        const saved = await jobApi.getSavedJobs()
        this.isSaved = saved.some(j => j.job_id === this.$route.params.id)
      } catch (e) {}
    },
    async calcMatch() {
      if (!this.profileId) {
        alert('请先上传简历')
        return
      }
      this.matchLoading = true
      try {
        this.matchResult = await jobApi.getMatch(this.profileId, this.job.id)
      } catch (e) {
        console.error('计算匹配度失败', e)
      } finally {
        this.matchLoading = false
      }
    },
    async calcGap() {
      if (!this.profileId) {
        alert('请先上传简历')
        return
      }
      this.gapLoading = true
      try {
        this.gapResult = await gapApi.analyze(this.profileId, this.job.id)
      } catch (e) {
        console.error('差距分析失败', e)
      } finally {
        this.gapLoading = false
      }
    },
    async toggleSave() {
      if (this.isSaved) {
        await jobApi.removeSavedJob(this.job.id)
        this.isSaved = false
      } else {
        await jobApi.saveJob(this.job.id)
        this.isSaved = true
      }
    },
    async applyNow() {
      if (!this.profileId) {
        alert('请先上传简历')
        return
      }
      try {
        await applicationApi.applyJob(this.job.id, this.profileId)
        alert('投递成功！')
        this.$router.push('/applications')
      } catch (e) {
        console.error('投递失败', e)
        alert('投递失败，请重试')
      }
    },
    startInterview() {
      this.$router.push({ path: '/interview', query: { jobId: this.job.id } })
    },
    goToLearning() {
      localStorage.setItem('learningProfileId', this.profileId)
      localStorage.setItem('learningJobId', this.job.id)
      this.$router.push('/learning')
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleDateString('zh-CN')
    },
    getScoreClass(score) {
      if (score >= 70) return 'high'
      if (score >= 50) return 'medium'
      return 'low'
    },
    getScoreColor(score) {
      if (score >= 70) return 'var(--green)'
      if (score >= 50) return 'var(--orange)'
      return 'var(--red)'
    }
  }
}
</script>

<style scoped>
.job-detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px 80px;
}

.back-btn {
  display: inline-block;
  font-size: 14px;
  color: var(--blue);
  text-decoration: none;
  margin-bottom: 20px;
}

.loading { text-align: center; padding: 60px; color: var(--text-tertiary); }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-tertiary); }
.empty-link { font-size: 15px; color: var(--blue); text-decoration: none; }

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.detail-company {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-secondary);
}

.detail-tags {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.tag {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 980px;
}

.tag.remote { background: #e8f8ec; color: var(--green); }
.tag.foreign { background: var(--blue-light); color: var(--blue); }
.tag.season { background: #fff4e0; color: var(--orange); }

.detail-title {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.detail-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.btn-apply {
  padding: 12px 28px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  text-decoration: none;
}

.btn-save {
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

.btn-save.saved {
  background: #fff4e0;
  color: var(--orange);
  border-color: var(--orange);
}

.btn-interview {
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

/* Match Section */
.match-section {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.match-header h3 {
  font-size: 17px;
  font-weight: 700;
}

.match-score {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.match-score.high { background: var(--green); }
.match-score.medium { background: var(--orange); }
.match-score.low { background: var(--red); }

.match-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.match-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.match-label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 60px;
}

.bar-track {
  flex: 1;
  height: 8px;
  background: var(--bg);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.match-val {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 36px;
  text-align: right;
}

.calc-match-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  background: var(--blue-light);
  color: var(--blue);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}

.calc-match-btn:hover:not(:disabled) { background: #d0e8ff; }
.calc-match-btn:disabled { background: var(--bg); color: var(--text-tertiary); cursor: not-allowed; }

/* Detail Sections */
.detail-section {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 16px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--text-primary);
}

.detail-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.require-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.require-list li {
  font-size: 14px;
  color: var(--text-secondary);
  padding-left: 16px;
  position: relative;
  line-height: 1.5;
}

.require-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--blue);
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
  background: var(--blue-light);
  color: var(--blue);
}

.gap-section .gap-title,
.gap-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.gap-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.gap-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 980px;
  background: #fff4e0;
  color: var(--orange);
}

.gap-tag.good {
  background: #e8f8ec;
  color: var(--green);
}

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

.company-link {
  font-size: 14px;
  color: var(--blue);
  text-decoration: none;
}

.company-link:hover { text-decoration: underline; }
</style>
