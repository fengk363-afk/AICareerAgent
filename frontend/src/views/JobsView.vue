<template>
  <div class="jobs-page">
    <div class="page-header">
      <h1>岗位中心</h1>
      <p>汇聚广东人才网、公共招聘平台等优质岗位，AI 精准匹配</p>
    </div>

    <!-- 统计面板 -->
    <div class="stats-panel">
      <div class="stat-item">
        <div class="stat-num">{{ stats.total_jobs || 0 }}</div>
        <div class="stat-label">总岗位</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ stats.guangdong_jobs || 0 }}</div>
        <div class="stat-label">广东岗位</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ stats.campus_jobs || 0 }}</div>
        <div class="stat-label">校招岗位</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ stats.foreign_jobs || 0 }}</div>
        <div class="stat-label">外企岗位</div>
      </div>
      <div class="stat-item">
        <div class="stat-num">{{ stats.remote_jobs || 0 }}</div>
        <div class="stat-label">远程岗位</div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="search-bar">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索岗位、公司..."
          class="search-input"
          @keyup.enter="searchJobs"
        />
        <button class="search-btn" @click="searchJobs">搜索</button>
      </div>
      <div class="action-buttons">
        <button class="sync-btn" @click="syncJobs" :disabled="syncing">
          {{ syncing ? '同步中...' : '🔄 同步岗位' }}
        </button>
        <button class="seed-btn" @click="seedJobs" :disabled="seeding">
          {{ seeding ? '初始化中...' : '📦 初始化数据' }}
        </button>
      </div>
    </div>

    <!-- 地点筛选 -->
    <div class="location-filter">
      <div class="location-label">📍 地点：</div>
      <!-- 已选地点标签 -->
      <div v-if="selectedLocations.length > 0" class="selected-tags">
        <span
          v-for="loc in selectedLocations"
          :key="loc"
          class="selected-tag"
        >
          {{ loc }}
          <button class="tag-remove" @click="removeLocation(loc)">×</button>
        </span>
        <button class="clear-all" @click="clearLocations">清空</button>
      </div>
      <!-- 地点选择面板 -->
      <div class="location-dropdown" v-if="showLocationPicker">
        <div class="location-options">
          <label
            v-for="loc in allLocations"
            :key="loc"
            class="location-option"
          >
            <input
              type="checkbox"
              :value="loc"
              v-model="selectedLocations"
              @change="onLocationChange"
            />
            <span>{{ loc }}</span>
          </label>
        </div>
        <div class="location-actions">
          <button class="apply-btn" @click="applyLocations">确定</button>
          <button class="cancel-btn" @click="showLocationPicker = false">取消</button>
        </div>
      </div>
      <!-- 展开按钮 -->
      <button
        class="location-toggle-btn"
        @click="showLocationPicker = !showLocationPicker"
      >
        {{ showLocationPicker ? '收起' : '选择地点' }}
      </button>
    </div>

    <!-- 薪资筛选 -->
    <div class="salary-filter">
      <div class="filter-label">💰 薪资：</div>
      <!-- 已选薪资标签 -->
      <div v-if="selectedSalaryRanges.length > 0" class="selected-tags">
        <span
          v-for="range in selectedSalaryRanges"
          :key="range.label"
          class="selected-tag"
        >
          {{ range.label }}
          <button class="tag-remove" @click="removeSalaryRange(range)">×</button>
        </span>
        <button class="clear-all" @click="clearSalaryRanges">清空</button>
      </div>
      <!-- 薪资选择面板 -->
      <div class="salary-dropdown" v-if="showSalaryPicker">
        <div class="salary-options">
          <label
            v-for="range in salaryRanges"
            :key="range.value"
            class="salary-option"
          >
            <input
              type="checkbox"
              :value="range"
              v-model="selectedSalaryRanges"
              @change="onSalaryChange"
            />
            <span>{{ range.label }}</span>
          </label>
        </div>
        <div class="salary-actions">
          <button class="apply-btn" @click="applySalaryRanges">确定</button>
          <button class="cancel-btn" @click="showSalaryPicker = false">取消</button>
        </div>
      </div>
      <!-- 展开按钮 -->
      <button
        class="salary-toggle-btn"
        @click="showSalaryPicker = !showSalaryPicker"
      >
        {{ showSalaryPicker ? '收起' : '选择薪资' }}
      </button>
    </div>

    <!-- 行业筛选 -->
    <div class="industry-filter">
      <div class="filter-label">🏢 行业：</div>
      <!-- 已选行业标签 -->
      <div v-if="selectedIndustries.length > 0" class="selected-tags">
        <span
          v-for="ind in selectedIndustries"
          :key="ind"
          class="selected-tag"
        >
          {{ ind }}
          <button class="tag-remove" @click="removeIndustry(ind)">×</button>
        </span>
        <button class="clear-all" @click="clearIndustries">清空</button>
      </div>
      <!-- 行业选择面板 -->
      <div class="industry-dropdown" v-if="showIndustryPicker">
        <div class="industry-options">
          <label
            v-for="ind in allIndustries"
            :key="ind.value"
            class="industry-option"
          >
            <input
              type="checkbox"
              :value="ind.value"
              v-model="selectedIndustries"
              @change="onIndustryChange"
            />
            <span>{{ ind.label }}</span>
          </label>
        </div>
        <div class="industry-actions">
          <button class="apply-btn" @click="applyIndustries">确定</button>
          <button class="cancel-btn" @click="showIndustryPicker = false">取消</button>
        </div>
      </div>
      <!-- 展开按钮 -->
      <button
        class="industry-toggle-btn"
        @click="showIndustryPicker = !showIndustryPicker"
      >
        {{ showIndustryPicker ? '收起' : '选择行业' }}
      </button>
    </div>

    <!-- 岗位分类筛选 -->
    <div class="category-filter">
      <div class="filter-label">📋 岗位分类：</div>
      <!-- 已选分类标签 -->
      <div v-if="selectedCategories.length > 0" class="selected-tags">
        <span
          v-for="cat in selectedCategories"
          :key="cat"
          class="selected-tag"
        >
          {{ cat }}
          <button class="tag-remove" @click="removeCategory(cat)">×</button>
        </span>
        <button class="clear-all" @click="clearCategories">清空</button>
      </div>
      <!-- 分类选择面板 -->
      <div class="category-dropdown" v-if="showCategoryPicker">
        <div class="category-options">
          <label
            v-for="cat in allCategories"
            :key="cat.value"
            class="category-option"
          >
            <input
              type="checkbox"
              :value="cat.value"
              v-model="selectedCategories"
              @change="onCategoryChange"
            />
            <span>{{ cat.label }}</span>
          </label>
        </div>
        <div class="category-actions">
          <button class="apply-btn" @click="applyCategories">确定</button>
          <button class="cancel-btn" @click="showCategoryPicker = false">取消</button>
        </div>
      </div>
      <!-- 展开按钮 -->
      <button
        class="category-toggle-btn"
        @click="showCategoryPicker = !showCategoryPicker"
      >
        {{ showCategoryPicker ? '收起' : '选择分类' }}
      </button>
    </div>

    <!-- 筛选 -->
    <div class="filters">
      <button
        v-for="f in filterOptions"
        :key="f.value"
        :class="['filter-btn', { active: activeFilter === f.value }]"
        @click="activeFilter = f.value; searchJobs()"
      >
        {{ f.label }}
      </button>
      <button
        :class="['filter-btn', { active: filterRemote }]"
        @click="filterRemote = !filterRemote; searchJobs()"
      >🏠 远程</button>
      <button
        :class="['filter-btn', { active: filterForeign }]"
        @click="filterForeign = !filterForeign; searchJobs()"
      >🌍 外企</button>
      <button
        :class="['filter-btn', { active: filterCampus }]"
        @click="filterCampus = !filterCampus; searchJobs()"
      >🎓 校招</button>
    </div>

    <!-- 排序 -->
    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <button
        v-for="opt in sortOptions"
        :key="opt.value"
        :class="['sort-btn', { active: sortBy === opt.value }]"
        @click="sortBy = opt.value; searchJobs()"
      >{{ opt.label }}</button>
      <span class="job-count">{{ jobs.length }} 个岗位</span>
    </div>

    <!-- 空状态 -->
    <div v-if="jobs.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无岗位数据</p>
      <div class="empty-actions">
        <button class="sync-btn" @click="syncJobs" :disabled="syncing">
          {{ syncing ? '同步中...' : '🔄 同步广东岗位' }}
        </button>
        <button class="seed-btn" @click="seedJobs" :disabled="seeding">
          {{ seeding ? '初始化中...' : '📦 初始化数据' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 岗位列表 -->
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
            <span
              v-for="tag in getUniqueJobTags(job)"
              :key="tag"
              :class="['tag', tagClass(tag)]"
            >{{ tag }}</span>
          </div>
        </div>
        <div class="job-title">{{ job.title }}</div>
        <div class="job-meta">
          <span>📍 {{ job.location }}</span>
          <span v-if="job.salary_range">· 💰 {{ job.salary_range.min }}-{{ job.salary_range.max }}K</span>
          <span v-if="job.job_type">· {{ job.job_type }}</span>
        </div>
        <div class="job-desc">{{ truncate(job.description, 120) }}</div>
        <div class="job-footer">
          <div class="job-tags-row">
            <span
              v-for="skill in (job.preferred_skills || []).slice(0, 3)"
              :key="skill"
              class="mini-tag"
            >{{ skill }}</span>
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
      stats: {},
      loading: false,
      syncing: false,
      seeding: false,
      searchKeyword: '',
      activeFilter: 'all',
      filterRemote: false,
      filterForeign: false,
      filterCampus: false,
      sortBy: 'default',
      sortOptions: [
        { label: '默认', value: 'default' },
        { label: '薪资', value: 'salary' },
        { label: '最新', value: 'latest' }
      ],
      filterOptions: [
        { label: '全部', value: 'all' },
        { label: '广东人才网', value: 'gdrc' },
        { label: '公共招聘', value: 'gd_public' },
        { label: '校招', value: 'campus' },
        { label: '外企', value: 'foreign' }
      ],
      savedJobs: new Set(),
      // 地点筛选
      selectedLocations: [],
      allLocations: [],
      showLocationPicker: false,
      // 薪资筛选
      selectedSalaryRanges: [],
      salaryRanges: [
        { value: '0-10', label: '0-10K' },
        { value: '10-20', label: '10-20K' },
        { value: '20-30', label: '20-30K' },
        { value: '30-50', label: '30-50K' },
        { value: '50+', label: '50K+' }
      ],
      showSalaryPicker: false,
      // 行业筛选
      selectedIndustries: [],
      allIndustries: [],
      showIndustryPicker: false,
      // 岗位分类筛选
      selectedCategories: [],
      allCategories: [],
      showCategoryPicker: false
    }
  },
  async created() {
    await this.loadStats()
    await this.loadJobs()
    await this.loadSavedJobs()
    await this.loadLocations()
    await this.loadFilterOptions()
  },
  methods: {
    async loadStats() {
      try {
        this.stats = await jobApi.getJobStats()
      } catch (e) {
        console.error('加载统计失败', e)
      }
    },

    async loadLocations() {
      // 从已有岗位中提取所有地点
      try {
        const allJobs = await jobApi.listJobs({ limit: 100 })
        const locSet = new Set()
        for (const job of allJobs) {
          if (job.locations && Array.isArray(job.locations)) {
            for (const loc of job.locations) {
              locSet.add(loc)
            }
          }
          if (job.location) {
            locSet.add(job.location)
          }
        }
        this.allLocations = Array.from(locSet).sort()
      } catch (e) {
        console.error('加载地点列表失败', e)
      }
    },

    async loadFilterOptions() {
      // 从 API 加载行业和岗位分类
      try {
        const res = await jobApi.getFilterOptions()
        this.allIndustries = res.industries || []
        this.allCategories = res.job_categories || []
      } catch (e) {
        console.error('加载筛选选项失败', e)
      }
    },

    async loadJobs() {
      this.loading = true
      try {
        const params = { keyword: this.searchKeyword || undefined }
        if (this.filterRemote) params.is_remote = true
        if (this.filterForeign) params.is_foreign = true
        if (this.filterCampus) params.campus_recruitment = true
        // 地点筛选
        if (this.selectedLocations.length > 0) {
          params.locations = this.selectedLocations.join(',')
        }
        // 薪资筛选
        if (this.selectedSalaryRanges.length > 0) {
          const ranges = this.selectedSalaryRanges.map(r => r.value)
          params.salary_ranges = ranges.join(',')
        }
        // 行业筛选
        if (this.selectedIndustries.length > 0) {
          params.industry = this.selectedIndustries.join(',')
        }
        // 岗位分类筛选
        if (this.selectedCategories.length > 0) {
          params.job_category = this.selectedCategories.join(',')
        }

        // 来源筛选
        if (this.activeFilter === 'gdrc') {
          params.source_type = 'gdrc'
        } else if (this.activeFilter === 'gd_public') {
          params.source_type = 'gd_public'
        } else if (this.activeFilter === 'campus') {
          params.campus_recruitment = true
        } else if (this.activeFilter === 'foreign') {
          params.is_foreign = true
        }

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

    async syncJobs() {
      this.syncing = true
      try {
        await jobApi.syncJobs('gdrc')
        await jobApi.syncJobs('gd_public')
        await this.loadJobs()
        await this.loadStats()
        await this.loadLocations()
      } catch (e) {
        console.error('同步失败', e)
        alert('同步失败，请重试')
      } finally {
        this.syncing = false
      }
    },

    async seedJobs() {
      this.seeding = true
      try {
        await jobApi.seedJobs()
        await this.loadJobs()
        await this.loadStats()
        await this.loadLocations()
      } catch (e) {
        console.error('初始化失败', e)
        alert('初始化失败，请重试')
      } finally {
        this.seeding = false
      }
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

    truncate(str, len) {
      return str && str.length > len ? str.slice(0, len) + '...' : str || ''
    },

    seasonLabel(season) {
      const map = { spring: '春招', autumn: '秋招', regular: '日常' }
      return map[season] || season
    },

    // 标签标准化：去除 emoji、特殊字符
    normalizeTag(tag) {
      if (!tag) return ''
      // 去除 emoji 和特殊字符，只保留中文、英文、数字
      return tag.replace(/[\u{1F000}-\u{1FFFF}]\u{FE0F}?[\u{20E3}]?|[\u{2700}-\u{27BF}]|·|•|✓|☆|→|—|–/gu, '').trim()
    },

    // 检查岗位是否已包含标准化后的标签
    hasNormalizedTag(job, tagName) {
      const normalizedTags = (job.tags || []).map(t => this.normalizeTag(t))
      return normalizedTags.includes(this.normalizeTag(tagName))
    },

    // 根据标签文本返回对应的 CSS class
    tagClass(tag) {
      const map = {
        '广东人才网': 'gdrc',
        '公共招聘': 'gd_public',
        '远程': 'remote',
        '外企': 'foreign',
        '校招': 'campus'
      }
      if (map[tag]) return map[tag]
      if (['春招', '秋招', '日常'].includes(tag)) return 'season'
      return ''
    },

    // 获取去重后的岗位标签
    getUniqueJobTags(job) {
      const normalizedSet = new Set()
      const result = []

      // 合并 job.tags 和系统标签到一个统一数组
      const allTags = [...(job.tags || [])]
      if (job.source === 'gdrc') allTags.push('广东人才网')
      if (job.source === 'gd_public') allTags.push('公共招聘')
      if (job.is_remote) allTags.push('远程')
      if (job.is_foreign) allTags.push('外企')
      if (job.campus_recruitment) allTags.push('校招')
      if (job.season) allTags.push(this.seasonLabel(job.season))

      // 统一 normalizeTag 后去重，显示标准化文本
      for (const tag of allTags) {
        const normalized = this.normalizeTag(tag)
        if (normalized && !normalizedSet.has(normalized)) {
          normalizedSet.add(normalized)
          result.push(normalized)
        }
      }

      return result
    },

    // 地点筛选方法
    onLocationChange() {
      // checkbox 变化时实时更新
      this.searchJobs()
    },

    applyLocations() {
      this.showLocationPicker = false
      this.searchJobs()
    },

    removeLocation(loc) {
      const idx = this.selectedLocations.indexOf(loc)
      if (idx > -1) {
        this.selectedLocations.splice(idx, 1)
      }
      this.searchJobs()
    },

    clearLocations() {
      this.selectedLocations = []
      this.searchJobs()
    },

    // 薪资筛选方法
    onSalaryChange() {
      this.searchJobs()
    },

    applySalaryRanges() {
      this.showSalaryPicker = false
      this.searchJobs()
    },

    removeSalaryRange(range) {
      const idx = this.selectedSalaryRanges.indexOf(range)
      if (idx > -1) {
        this.selectedSalaryRanges.splice(idx, 1)
      }
      this.searchJobs()
    },

    clearSalaryRanges() {
      this.selectedSalaryRanges = []
      this.searchJobs()
    },

    // 行业筛选方法
    onIndustryChange() {
      this.searchJobs()
    },

    applyIndustries() {
      this.showIndustryPicker = false
      this.searchJobs()
    },

    removeIndustry(ind) {
      const idx = this.selectedIndustries.indexOf(ind)
      if (idx > -1) {
        this.selectedIndustries.splice(idx, 1)
      }
      this.searchJobs()
    },

    clearIndustries() {
      this.selectedIndustries = []
      this.searchJobs()
    },

    // 岗位分类筛选方法
    onCategoryChange() {
      this.searchJobs()
    },

    applyCategories() {
      this.showCategoryPicker = false
      this.searchJobs()
    },

    removeCategory(cat) {
      const idx = this.selectedCategories.indexOf(cat)
      if (idx > -1) {
        this.selectedCategories.splice(idx, 1)
      }
      this.searchJobs()
    },

    clearCategories() {
      this.selectedCategories = []
      this.searchJobs()
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

/* 统计面板 */
.stats-panel {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.stat-item {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 20px 16px;
  text-align: center;
  box-shadow: var(--shadow);
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--blue);
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

/* 操作栏 */
.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.search-bar {
  flex: 1;
  display: flex;
  gap: 10px;
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

.action-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.sync-btn, .seed-btn {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.sync-btn {
  background: var(--blue-light);
  color: var(--blue);
}

.sync-btn:hover:not(:disabled) { background: #d0e8ff; }
.sync-btn:disabled { background: var(--bg); color: var(--text-tertiary); cursor: not-allowed; }

.seed-btn {
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
}

.seed-btn:hover:not(:disabled) { background: var(--border); }
.seed-btn:disabled { cursor: not-allowed; }

/* 地点筛选 */
.location-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  position: relative;
}

.location-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.selected-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 13px;
  font-weight: 500;
  background: var(--blue-light);
  color: var(--blue);
  border-radius: 980px;
}

.tag-remove {
  background: none;
  border: none;
  color: var(--blue);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0 2px;
  opacity: 0.7;
  transition: opacity 0.15s;
}

.tag-remove:hover { opacity: 1; }

.clear-all {
  font-size: 12px;
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  font-family: inherit;
}

.clear-all:hover { color: var(--blue); }

.location-toggle-btn {
  padding: 7px 14px;
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

.location-toggle-btn:hover {
  border-color: var(--blue);
  color: var(--blue);
}

.location-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  padding: 12px;
  z-index: 50;
  min-width: 200px;
}

.location-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.location-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 0;
}

.location-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--blue);
}

.location-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.apply-btn {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
}

.apply-btn:hover { background: #0077ed; }

.cancel-btn {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
}

.cancel-btn:hover { background: var(--border); }

/* 薪资筛选 */
.salary-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  position: relative;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.salary-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  padding: 12px;
  z-index: 50;
  min-width: 180px;
}

.salary-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.salary-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 0;
}

.salary-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--blue);
}

.salary-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.salary-toggle-btn {
  padding: 7px 14px;
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

.salary-toggle-btn:hover {
  border-color: var(--blue);
  color: var(--blue);
}

/* 行业筛选 */
.industry-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  position: relative;
}

.industry-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  padding: 12px;
  z-index: 50;
  min-width: 200px;
}

.industry-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.industry-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 0;
}

.industry-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--blue);
}

.industry-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.industry-toggle-btn {
  padding: 7px 14px;
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

.industry-toggle-btn:hover {
  border-color: var(--blue);
  color: var(--blue);
}

/* 岗位分类筛选 */
.category-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  position: relative;
}

.category-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  padding: 12px;
  z-index: 50;
  min-width: 200px;
}

.category-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  padding: 4px 0;
}

.category-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--blue);
}

.category-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.category-toggle-btn {
  padding: 7px 14px;
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

.category-toggle-btn:hover {
  border-color: var(--blue);
  color: var(--blue);
}

/* 筛选 */
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

/* 排序 */
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

/* 岗位列表 */
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
  flex-shrink: 0;
}

.tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
}

.tag.gdrc { background: #e8f8ec; color: var(--green); }
.tag.gd_public { background: #fff4e0; color: var(--orange); }
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

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; margin-bottom: 16px; }

.empty-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

/* Loading */
.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }

/* 响应式 */
@media (max-width: 734px) {
  .stats-panel {
    grid-template-columns: repeat(3, 1fr);
  }
  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .action-buttons {
    justify-content: center;
  }
}
</style>
