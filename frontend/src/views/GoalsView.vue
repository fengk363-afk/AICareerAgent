<template>
  <div class="goals-page">
    <div class="page-header">
      <h1>职业目标</h1>
      <p>设定你的职业目标，追踪求职进度</p>
    </div>

    <!-- 求职偏好 -->
    <div class="pref-card">
      <div class="card-header">
        <div class="section-title">求职偏好</div>
        <button class="edit-btn" @click="togglePrefEdit">{{ prefEdit ? '完成' : '编辑' }}</button>
      </div>
      <div class="pref-grid">
        <div class="pref-item">
          <span class="pref-label">目标岗位</span>
          <input v-if="prefEdit" v-model="prefForm.target_role" class="pref-input" placeholder="如：前端工程师" />
          <span v-else class="pref-value">{{ pref?.target_role || '未设置' }}</span>
        </div>
        <div class="pref-item">
          <span class="pref-label">目标城市</span>
          <input v-if="prefEdit" v-model="prefForm.target_location" class="pref-input" placeholder="如：北京" />
          <span v-else class="pref-value">{{ pref?.target_location || '未设置' }}</span>
        </div>
        <div class="pref-item">
          <span class="pref-label">目标行业</span>
          <input v-if="prefEdit" v-model="prefForm.target_industry" class="pref-input" placeholder="如：互联网" />
          <span v-else class="pref-value">{{ pref?.target_industry || '未设置' }}</span>
        </div>
        <div class="pref-item">
          <span class="pref-label">期望薪资</span>
          <input v-if="prefEdit" v-model="prefForm.salary_min" class="pref-input" type="number" placeholder="最低" style="width:80px" />
          <input v-if="prefEdit" v-model="prefForm.salary_max" class="pref-input" type="number" placeholder="最高" style="width:80px" />
          <span v-else class="pref-value">{{ pref?.salary_min && pref?.salary_max ? pref.salary_min + '-' + pref.salary_max + 'K' : '未设置' }}</span>
        </div>
      </div>
      <button v-if="prefEdit" class="save-pref-btn" @click="savePreferences">保存偏好</button>
    </div>

    <!-- 职业目标 -->
    <div class="goals-header">
      <div class="section-title">职业目标</div>
      <button class="add-btn" @click="showAddGoal = true">+ 添加目标</button>
    </div>

    <div v-if="goals.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">🎯</div>
      <p>添加你的第一个职业目标</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-for="goal in goals" :key="goal.id" class="goal-card">
      <div class="goal-header">
        <div class="goal-title">{{ goal.target_position || '未命名目标' }}</div>
        <div class="goal-actions">
          <button class="goal-delete" @click="deleteGoal(goal.id)">×</button>
        </div>
      </div>
      <div class="goal-meta">
        <span v-if="goal.target_company">🏢 {{ goal.target_company }}</span>
        <span v-if="goal.target_city">📍 {{ goal.target_city }}</span>
        <span v-if="goal.target_industry">🏭 {{ goal.target_industry }}</span>
        <span v-if="goal.salary_expectation_min && goal.salary_expectation_max">💰 {{ goal.salary_expectation_min }}-{{ goal.salary_expectation_max }}K</span>
      </div>
      <div class="goal-progress">
        <div class="progress-label">
          <span>求职进度</span>
          <span>{{ goal.progress?.current || 0 }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (goal.progress?.current || 0) + '%' }"></div>
        </div>
      </div>
      <div v-if="goal.notes" class="goal-notes">{{ goal.notes }}</div>
    </div>

    <!-- 目标公司 -->
    <div class="goals-header" style="margin-top:24px">
      <div class="section-title">目标公司</div>
      <button class="add-btn" @click="showAddCompany = true">+ 添加公司</button>
    </div>

    <div v-if="companies.length === 0 && !loading" class="empty-state">
      <p>添加你的目标公司</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-for="comp in companies" :key="comp.id" class="company-card">
      <div class="company-card-header">
        <div class="company-card-name">{{ comp.company_name }}</div>
        <div class="company-card-meta">
          <span v-if="comp.company_type">{{ comp.company_type }}</span>
          <span v-if="comp.industry">{{ comp.industry }}</span>
          <span v-if="comp.target_position">{{ comp.target_position }}</span>
        </div>
        <button class="goal-delete" @click="deleteCompany(comp.id)">×</button>
      </div>
      <div v-if="comp.notes" class="company-card-notes">{{ comp.notes }}</div>
    </div>

    <!-- 添加目标弹窗 -->
    <div v-if="showAddGoal" class="modal-overlay" @click="showAddGoal = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>添加职业目标</h3>
          <button class="modal-close" @click="showAddGoal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">目标岗位</label>
            <input v-model="goalForm.target_position" class="form-input" placeholder="如：前端工程师" />
          </div>
          <div class="form-group">
            <label class="form-label">目标公司</label>
            <input v-model="goalForm.target_company" class="form-input" placeholder="如：字节跳动" />
          </div>
          <div class="form-group">
            <label class="form-label">目标城市</label>
            <input v-model="goalForm.target_city" class="form-input" placeholder="如：北京" />
          </div>
          <div class="form-group">
            <label class="form-label">期望薪资（K）</label>
            <div class="salary-row">
              <input v-model="goalForm.salary_min" class="form-input" type="number" placeholder="最低" style="flex:1" />
              <span class="salary-sep">—</span>
              <input v-model="goalForm.salary_max" class="form-input" type="number" placeholder="最高" style="flex:1" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="goalForm.notes" class="form-input" rows="3" placeholder="可选备注"></textarea>
          </div>
          <button class="modal-btn" @click="addGoal" :disabled="!goalForm.target_position">保存目标</button>
        </div>
      </div>
    </div>

    <!-- 添加公司弹窗 -->
    <div v-if="showAddCompany" class="modal-overlay" @click="showAddCompany = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>添加目标公司</h3>
          <button class="modal-close" @click="showAddCompany = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">公司名称</label>
            <input v-model="companyForm.company_name" class="form-input" placeholder="如：腾讯" />
          </div>
          <div class="form-group">
            <label class="form-label">公司类型</label>
            <input v-model="companyForm.company_type" class="form-input" placeholder="如：互联网" />
          </div>
          <div class="form-group">
            <label class="form-label">目标岗位</label>
            <input v-model="companyForm.target_position" class="form-input" placeholder="如：后端开发" />
          </div>
          <div class="form-group">
            <label class="form-label">备注</label>
            <textarea v-model="companyForm.notes" class="form-input" rows="3" placeholder="可选备注"></textarea>
          </div>
          <button class="modal-btn" @click="addCompany" :disabled="!companyForm.company_name">保存公司</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { goalApi } from '../api/index.js'

export default {
  name: 'GoalsView',
  data() {
    return {
      pref: null,
      prefEdit: false,
      prefForm: { target_role: '', target_location: '', target_industry: '', salary_min: '', salary_max: '' },
      goals: [],
      companies: [],
      loading: false,
      showAddGoal: false,
      showAddCompany: false,
      goalForm: { target_position: '', target_company: '', target_city: '', salary_min: '', salary_max: '', notes: '' },
      companyForm: { company_name: '', company_type: '', target_position: '', notes: '' }
    }
  },
  async created() {
    await Promise.all([this.loadPreferences(), this.loadGoals(), this.loadCompanies()])
  },
  methods: {
    async loadPreferences() {
      try { this.pref = await goalApi.getPreferences() } catch (e) {}
    },
    async loadGoals() {
      this.loading = true
      try { this.goals = await goalApi.getGoals() } catch (e) {} finally { this.loading = false }
    },
    async loadCompanies() {
      try { this.companies = await goalApi.getTargetCompanies() } catch (e) {}
    },
    togglePrefEdit() {
      if (this.prefEdit) {
        this.savePreferences()
      }
      this.prefEdit = !this.prefEdit
    },
    async savePreferences() {
      try {
        this.pref = await goalApi.updatePreferences(this.prefForm)
        this.prefEdit = false
      } catch (e) {
        console.error('保存偏好失败', e)
      }
    },
    async addGoal() {
      if (!this.goalForm.target_position) return
      try {
        await goalApi.createGoal(this.goalForm)
        this.showAddGoal = false
        this.goalForm = { target_position: '', target_company: '', target_city: '', salary_min: '', salary_max: '', notes: '' }
        await this.loadGoals()
      } catch (e) {
        console.error('添加目标失败', e)
      }
    },
    async deleteGoal(goalId) {
      if (!confirm('确定删除该目标？')) return
      try { await goalApi.deleteGoal(goalId); await this.loadGoals() } catch (e) {}
    },
    async addCompany() {
      if (!this.companyForm.company_name) return
      try {
        await goalApi.addTargetCompany(this.companyForm)
        this.showAddCompany = false
        this.companyForm = { company_name: '', company_type: '', target_position: '', notes: '' }
        await this.loadCompanies()
      } catch (e) {
        console.error('添加公司失败', e)
      }
    },
    async deleteCompany(companyId) {
      if (!confirm('确定删除该公司？')) return
      try { await goalApi.deleteTargetCompany(companyId); await this.loadCompanies() } catch (e) {}
    }
  }
}
</script>

<style scoped>
.goals-page {
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

.goals-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.add-btn {
  padding: 6px 16px;
  font-size: 14px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
}

/* Preference Card */
.pref-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.edit-btn {
  font-size: 13px;
  color: var(--blue);
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

.pref-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.pref-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pref-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.pref-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.pref-input {
  height: 40px;
  padding: 0 12px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  outline: none;
  font-family: inherit;
  color: var(--text-primary);
}

.pref-input:focus { border-color: var(--blue); }

.save-pref-btn {
  margin-top: 16px;
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}

/* Goal Card */
.goal-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.goal-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.goal-delete {
  font-size: 20px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: 0 4px;
}

.goal-delete:hover { color: var(--red); }

.goal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 14px;
}

.goal-progress { margin-bottom: 8px; }

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.progress-bar {
  height: 6px;
  background: var(--bg);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--blue);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.goal-notes {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

/* Company Card */
.company-card {
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
  box-shadow: var(--shadow);
  margin-bottom: 10px;
}

.company-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.company-card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.company-card-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.company-card-notes {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 28px;
  max-width: 480px;
  width: 90%;
  max-height: 85vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 700;
}

.modal-close {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
}

.form-group {
  margin-bottom: 14px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  font-size: 15px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  outline: none;
  font-family: inherit;
  color: var(--text-primary);
  transition: border-color 0.2s ease;
}

.form-input:focus { border-color: var(--blue); background: var(--bg-white); }
.form-input[type="number"] { -moz-appearance: textfield; }
.form-input::-webkit-inner-spin-button, .form-input::-webkit-outer-spin-button { -webkit-appearance: none; }

.salary-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.salary-sep { color: var(--text-tertiary); font-size: 15px; }

.modal-btn {
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
  margin-top: 8px;
}

.modal-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-tertiary);
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; }

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }

@media (max-width: 734px) {
  .pref-grid { grid-template-columns: 1fr; }
}
</style>
