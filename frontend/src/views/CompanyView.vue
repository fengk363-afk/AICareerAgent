<template>
  <div class="company-page">
    <div class="page-header">
      <h1>公司研究</h1>
      <p>深入了解目标公司，做出更明智的求职决策</p>
    </div>

    <!-- 搜索 -->
    <div class="search-card">
      <div class="search-bar">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="输入公司名称搜索..."
          class="search-input"
          @keyup.enter="searchCompany"
        />
        <button class="search-btn" @click="searchCompany" :disabled="!searchKeyword.trim()">搜索</button>
      </div>
    </div>

    <!-- 公司档案 -->
    <div v-if="company" class="company-card">
      <div class="company-header">
        <div class="company-logo">{{ company.name?.[0] || '🏢' }}</div>
        <div class="company-info">
          <h2 class="company-name">{{ company.name }}</h2>
          <div class="company-meta">
            <span v-if="company.industry">🏭 {{ company.industry }}</span>
            <span v-if="company.size">👥 {{ company.size }}人</span>
            <span v-if="company.location">📍 {{ company.location }}</span>
            <span v-if="company.website">🌐 <a :href="company.website" target="_blank">{{ company.website }}</a></span>
          </div>
        </div>
        <div class="company-rating" v-if="company.rating">
          <div class="rating-stars">
            <span v-for="n in 5" :key="n" :class="['star', { filled: n <= company.rating }]">★</span>
          </div>
          <span class="rating-num">{{ company.rating }}</span>
        </div>
      </div>

      <!-- 公司概述 -->
      <div v-if="company.overview" class="company-section">
        <div class="section-title">公司概述</div>
        <p class="section-text">{{ company.overview }}</p>
      </div>

      <!-- 文化价值观 -->
      <div v-if="company.culture?.length" class="company-section">
        <div class="section-title">文化价值观</div>
        <div class="culture-tags">
          <span v-for="c in company.culture" :key="c" class="culture-tag">{{ c }}</span>
        </div>
      </div>

      <!-- 面试经验 -->
      <div v-if="company.interviews?.length" class="company-section">
        <div class="section-title">面试经验</div>
        <div class="interview-list">
          <div v-for="(exp, idx) in company.interviews" :key="idx" class="interview-item">
            <div class="interview-round">{{ exp.round }}</div>
            <div class="interview-content">
              <div class="interview-q">{{ exp.question }}</div>
              <div class="interview-tip" v-if="exp.tip">💡 {{ exp.tip }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 薪资范围 -->
      <div v-if="company.salary_range" class="company-section">
        <div class="section-title">薪资范围</div>
        <div class="salary-grid">
          <div v-for="(range, role) in company.salary_range" :key="role" class="salary-item">
            <div class="salary-role">{{ role }}</div>
            <div class="salary-range">{{ range }}</div>
          </div>
        </div>
      </div>

      <!-- 优缺点 -->
      <div v-if="company.pros?.length || company.cons?.length" class="company-section">
        <div class="section-title">评价</div>
        <div class="pros-cons">
          <div v-if="company.pros?.length" class="pc-group">
            <div class="pc-label good">优点</div>
            <ul class="pc-list">
              <li v-for="(p, idx) in company.pros" :key="idx">{{ p }}</li>
            </ul>
          </div>
          <div v-if="company.cons?.length" class="pc-group">
            <div class="pc-label bad">缺点</div>
            <ul class="pc-list">
              <li v-for="(c, idx) in company.cons" :key="idx">{{ c }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索历史 -->
    <div v-if="history.length > 0" class="history-section">
      <div class="section-title">最近搜索</div>
      <div class="history-list">
        <div
          v-for="(name, idx) in history"
          :key="idx"
          class="history-item"
          @click="searchByName(name)"
        >
          {{ name }}
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!company && !loading" class="empty-state">
      <div class="empty-icon">🏢</div>
      <p>搜索公司名称，获取详细档案</p>
    </div>
  </div>
</template>

<script>
import { companyApi } from '../api/index.js'

export default {
  name: 'CompanyView',
  data() {
    return {
      searchKeyword: '',
      company: null,
      loading: false,
      history: JSON.parse(localStorage.getItem('companyHistory') || '[]')
    }
  },
  methods: {
    async searchCompany() {
      if (!this.searchKeyword.trim()) return
      await this.searchByName(this.searchKeyword.trim())
    },
    async searchByName(name) {
      this.loading = true
      this.company = null
      try {
        this.company = await companyApi.search(name)
        // 更新历史
        this.history = [name, ...this.history.filter(h => h !== name)].slice(0, 8)
        localStorage.setItem('companyHistory', JSON.stringify(this.history))
      } catch (e) {
        console.error('搜索公司失败', e)
        this.company = { name, error: '未找到该公司信息' }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.company-page {
  max-width: 800px;
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

.search-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 10px;
}

.search-input {
  flex: 1;
  height: 48px;
  padding: 0 16px;
  font-size: 17px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  outline: none;
  font-family: inherit;
}

.search-input:focus { border-color: var(--blue); }

.search-btn {
  height: 48px;
  padding: 0 24px;
  font-size: 16px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
}

.search-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

/* Company Card */
.company-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.company-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px 32px;
  border-bottom: 1px solid var(--border);
}

.company-logo {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: var(--blue-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.company-info { flex: 1; }
.company-name { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
.company-meta { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 6px; font-size: 14px; color: var(--text-secondary); }
.company-meta a { color: var(--blue); }

.company-rating {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.rating-stars { display: flex; gap: 2px; }
.star { font-size: 16px; color: var(--border); }
.star.filled { color: #ffc107; }
.rating-num { font-size: 14px; font-weight: 600; color: var(--text-secondary); }

.company-section {
  padding: 20px 32px;
  border-bottom: 1px solid var(--border);
}

.company-section:last-child { border-bottom: none; }

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.section-text {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

.culture-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.culture-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 980px;
  background: var(--bg);
  color: var(--text-secondary);
}

.interview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.interview-item {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg);
  border-radius: 10px;
}

.interview-round {
  font-size: 12px;
  font-weight: 600;
  color: var(--blue);
  background: var(--blue-light);
  padding: 3px 10px;
  border-radius: 980px;
  height: fit-content;
  flex-shrink: 0;
}

.interview-content { flex: 1; }
.interview-q { font-size: 14px; font-weight: 500; color: var(--text-primary); margin-bottom: 4px; }
.interview-tip { font-size: 13px; color: var(--text-secondary); }

.salary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.salary-item {
  padding: 12px 16px;
  background: var(--bg);
  border-radius: 10px;
}

.salary-role { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.salary-range { font-size: 13px; color: var(--green); margin-top: 4px; }

.pros-cons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.pc-group { display: flex; flex-direction: column; gap: 8px; }
.pc-label { font-size: 13px; font-weight: 600; }
.pc-label.good { color: var(--green); }
.pc-label.bad { color: var(--red); }

.pc-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pc-list li {
  font-size: 14px;
  color: var(--text-secondary);
  padding-left: 14px;
  position: relative;
  line-height: 1.5;
}

.pc-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--text-tertiary);
}

/* History */
.history-section { margin-top: 24px; }

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-item {
  padding: 6px 14px;
  font-size: 14px;
  color: var(--blue);
  background: var(--blue-light);
  border-radius: 980px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.history-item:hover { background: #d0e8ff; }

.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; }

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }

@media (max-width: 734px) {
  .company-header { flex-direction: column; text-align: center; padding: 20px; }
  .company-meta { justify-content: center; }
  .company-section { padding: 16px 20px; }
  .pros-cons { grid-template-columns: 1fr; }
}
</style>
