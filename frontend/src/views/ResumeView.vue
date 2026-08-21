<template>
  <div class="resume-page">
    <div class="page-header">
      <h1>简历画像</h1>
      <p>上传 PDF 简历，AI 自动解析并生成能力画像</p>
    </div>

    <!-- Upload Section -->
    <div class="upload-section">
      <div class="upload-icon">📄</div>
      <h2>上传简历</h2>
      <p>支持 PDF 格式，文件大小不超过 10MB</p>
      <input
        type="file"
        ref="fileInput"
        accept=".pdf"
        class="upload-input"
        @change="handleFileChange"
      />
      <button class="upload-btn" @click="triggerUpload" :disabled="uploading">
        <span v-if="!uploading">选择 PDF 文件</span>
        <span v-else>解析中...</span>
      </button>
      <div v-if="uploadStatus" class="upload-status">{{ uploadStatus }}</div>
    </div>

    <!-- Profile List -->
    <div v-if="profiles.length === 0 && !loading" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>暂无简历，请上传 PDF 文件</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- Profile Cards -->
    <div v-for="profile in profiles" :key="profile.id" class="profile-card">
      <!-- Card Header -->
      <div class="profile-card-header">
        <div>
          <h3>{{ profile.original_filename || '简历画像' }}</h3>
          <span class="filename">{{ formatDate(profile.created_at) }}</span>
        </div>
        <div class="profile-actions">
          <button
            v-if="editingId !== profile.id"
            class="edit-btn"
            @click="startEdit(profile)"
            title="编辑"
          >✏️</button>
          <button class="gen-btn" @click="generateRecommendations(profile.id)" :disabled="generatingIds.has(profile.id)">
            {{ generatingIds.has(profile.id) ? '生成中...' : '🎯 生成推荐' }}
          </button>
          <button class="del-btn" @click="deleteProfile(profile.id)">🗑</button>
        </div>
      </div>

      <!-- Edit Toolbar -->
      <div v-if="editingId === profile.id" class="edit-toolbar">
        <span class="edit-hint">编辑模式 — 可修改、删除或新增各项内容</span>
        <div class="edit-toolbar-actions">
          <button class="save-btn" @click="saveProfile(profile)" :disabled="savingIds.has(profile.id)">
            {{ savingIds.has(profile.id) ? '保存中...' : '💾 保存' }}
          </button>
          <button class="cancel-btn" @click="cancelEdit(profile)">取消</button>
        </div>
      </div>

      <div class="profile-card-body">
        <!-- 个人摘要 -->
        <div class="section" v-if="profile.summary !== undefined">
          <div class="section-title">个人摘要</div>
          <template v-if="editingId === profile.id">
            <textarea
              class="edit-textarea"
              v-model="editData[profile.id].summary"
              rows="3"
            ></textarea>
          </template>
          <p v-else class="summary-text">{{ profile.summary }}</p>
        </div>

        <!-- 教育背景 -->
        <div class="section">
          <div class="section-title">
            教育背景
            <button v-if="editingId === profile.id" class="add-btn" @click="addEducation(profile)">+ 新增</button>
          </div>
          <div v-if="!editData[profile.id]?.education?.length && (!profile.education || !profile.education.length)" class="empty-hint">暂无教育经历</div>
          <div v-for="(edu, idx) in (editData[profile.id]?.education || profile.education || [])" :key="idx" class="edu-item">
            <template v-if="editingId === profile.id">
              <div class="edit-row">
                <input class="edit-input" v-model="edu.school" placeholder="学校" />
                <input class="edit-input" v-model="edu.degree" placeholder="学历" />
                <input class="edit-input" v-model="edu.major" placeholder="专业" />
                <button class="remove-btn" @click="removeEducation(profile, idx)">✕</button>
              </div>
            </template>
            <template v-else>
              <div class="edu-school">{{ edu.school }}</div>
              <div class="edu-detail" v-if="edu.degree || edu.major">
                {{ [edu.degree, edu.major].filter(Boolean).join(' · ') }}
              </div>
            </template>
          </div>
        </div>

        <!-- 实习经历 -->
        <div class="section">
          <div class="section-title">
            实习经历
            <button v-if="editingId === profile.id" class="add-btn" @click="addExperience(profile)">+ 新增</button>
          </div>
          <div v-if="!editData[profile.id]?.experience?.length && (!profile.experience || !profile.experience.length)" class="empty-hint">暂无实习经历</div>
          <div v-for="(exp, idx) in (editData[profile.id]?.experience || profile.experience || [])" :key="idx" class="exp-item">
            <template v-if="editingId === profile.id">
              <div class="edit-row">
                <input class="edit-input" v-model="exp.company" placeholder="公司" />
                <input class="edit-input" v-model="exp.position" placeholder="职位" />
              </div>
              <div class="edit-row">
                <input class="edit-input edit-input-sm" v-model="exp.start_date" placeholder="开始日期（如 2023.06）" />
                <input class="edit-input edit-input-sm" v-model="exp.end_date" placeholder="结束日期（如 2023.12 或 至今）" />
                <button class="remove-btn" @click="removeExperience(profile, idx)">✕</button>
              </div>
              <textarea class="edit-textarea" v-model="exp.description" placeholder="工作内容描述" rows="3"></textarea>
            </template>
            <template v-else>
              <div class="exp-header">
                <div>
                  <span class="exp-company">{{ exp.company }}</span>
                  <span class="exp-position" v-if="exp.position">{{ exp.position }}</span>
                </div>
                <span class="exp-time" v-if="exp.start_date">
                  {{ formatExpDate(exp.start_date) }}
                  <span v-if="exp.end_date === '至今' || exp.end_date === 'current'"> — 至今</span>
                  <span v-else-if="exp.end_date"> — {{ formatExpDate(exp.end_date) }}</span>
                </span>
              </div>
              <div class="exp-desc" v-if="exp.description">{{ exp.description }}</div>
            </template>
          </div>
        </div>

        <!-- 项目经历 -->
        <div class="section">
          <div class="section-title">
            项目经历
            <button v-if="editingId === profile.id" class="add-btn" @click="addProject(profile)">+ 新增</button>
          </div>
          <div v-if="!editData[profile.id]?.project_experience?.length && (!profile.project_experience || !profile.project_experience.length)" class="empty-hint">暂无项目经历</div>
          <div v-for="(proj, idx) in (editData[profile.id]?.project_experience || profile.project_experience || [])" :key="idx" class="proj-item">
            <template v-if="editingId === profile.id">
              <div class="edit-row">
                <input class="edit-input" v-model="proj.project_name" placeholder="项目名称" />
                <input class="edit-input" v-model="proj.role" placeholder="角色" />
              </div>
              <div class="edit-row">
                <input class="edit-input edit-input-sm" v-model="proj.date" placeholder="时间（如 2023.03-2023.09）" />
                <button class="remove-btn" @click="removeProject(profile, idx)">✕</button>
              </div>
              <textarea class="edit-textarea" v-model="proj.description" placeholder="项目描述" rows="3"></textarea>
              <input class="edit-input" v-model="proj.technologies" placeholder="技术栈（用逗号或顿号分隔）" />
            </template>
            <template v-else>
              <div class="proj-header">
                <div>
                  <span class="proj-name">{{ proj.project_name }}</span>
                  <span class="proj-role" v-if="proj.role">{{ proj.role }}</span>
                </div>
                <span class="proj-duration" v-if="proj.date">{{ formatExpDate(proj.date) }}</span>
                <span class="proj-duration date-pending" v-else>至今</span>
              </div>
              <div class="proj-desc" v-if="proj.description">{{ proj.description }}</div>
              <div class="proj-tech" v-if="proj.technologies">
                <span
                  v-for="tech in splitByDelimiter(proj.technologies)"
                  :key="tech"
                  class="tech-tag"
                >{{ tech }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- 专业技能 -->
        <div class="section">
          <div class="section-title">
            专业技能
            <button v-if="editingId === profile.id" class="add-btn" @click="addSkill(profile)">+ 新增</button>
          </div>
          <div v-if="!editData[profile.id]?.skills?.length && (!profile.skills || !profile.skills.length)" class="empty-hint">暂无技能</div>
          <div v-for="(skill, idx) in (editData[profile.id]?.skills || profile.skills || [])" :key="idx" class="skill-row">
            <template v-if="editingId === profile.id">
              <div class="edit-row edit-row-skill">
                <input class="edit-input" v-model="skill.name" placeholder="技能名称" />
                <select class="edit-select" v-model="skill.category">
                  <option value="technical_skills">技术</option>
                  <option value="business_skills">商业</option>
                  <option value="tools_skills">工具</option>
                  <option value="content_skills">内容</option>
                </select>
                <input class="edit-input" v-model="skill.description" placeholder="描述（可选）" />
                <button class="remove-btn" @click="removeSkill(profile, idx)">✕</button>
              </div>
            </template>
            <template v-else>
              <span class="skill-name">{{ skill.name }}</span>
              <span v-if="skill.category" class="skill-category">{{ formatCategory(skill.category) }}</span>
              <span class="skill-desc" v-if="skill.description">{{ skill.description }}</span>
            </template>
          </div>
        </div>

        <!-- 能力优势（只读） -->
        <div class="section" v-if="profile.strength_analysis && profile.strength_analysis.length > 0">
          <div class="section-title">能力优势</div>
          <div class="strengths-list">
            <div v-for="(st, idx) in profile.strength_analysis" :key="idx" class="strength-item">
              <span class="strength-score">{{ st.score }}</span>
              <span class="strength-desc">{{ st.desc }}</span>
              <span class="strength-type">{{ formatStrengthType(st.type) }}</span>
            </div>
          </div>
        </div>

        <!-- 推荐岗位（只读） -->
        <div class="section" v-if="profile.recommendations && profile.recommendations.length > 0">
          <div class="section-title">推荐岗位</div>
          <div class="rec-list">
            <div v-for="(rec, idx) in profile.recommendations" :key="idx" class="rec-item">
              <div class="rec-header">
                <div class="rec-job-info">
                  <span class="rec-company">{{ rec.job?.company || '未知公司' }}</span>
                  <span class="rec-title">{{ rec.job?.title || '未知岗位' }}</span>
                </div>
                <div class="rec-scores">
                  <span class="rec-score-item" :class="{ 'rec-high': rec.overall_score >= 70 }">
                    匹配 {{ rec.overall_score }}
                  </span>
                  <span v-if="rec.should_recommend" class="rec-badge">推荐</span>
                </div>
              </div>
              <div class="rec-meta" v-if="rec.job?.location || rec.job?.salary_range">
                <span v-if="rec.job?.location">{{ rec.job.location }}</span>
                <span v-if="rec.job?.salary_range">· {{ rec.job.salary_range?.min }}-{{ rec.job.salary_range?.max }}K</span>
              </div>
              <div class="rec-reason" v-if="rec.recommendation_reason">{{ rec.recommendation_reason }}</div>
              <div class="rec-tags" v-if="rec.advantages?.length">
                <span
                  v-for="(adv, i) in rec.advantages.slice(0, 3)"
                  :key="i"
                  class="rec-tag rec-tag-pos"
                >{{ adv }}</span>
                <span
                  v-for="(risk, i) in (rec.risks || []).slice(0, 1)"
                  :key="'r'+i"
                  class="rec-tag rec-tag-neg"
                >{{ risk }}</span>
              </div>
              <div class="rec-actions">
                <router-link :to="`/jobs/${rec.job?.id}`" class="rec-link" v-if="rec.job?.id">查看详情</router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { resumeApi } from '../api/index.js'

export default {
  name: 'ResumeView',
  data() {
    return {
      profiles: [],
      loading: false,
      uploading: false,
      uploadStatus: '',
      generatingIds: new Set(),
      editingId: null,
      savingIds: new Set(),
      editData: {}
    }
  },
  async created() {
    await this.loadProfiles()
  },
  methods: {
    async loadProfiles() {
      this.loading = true
      try {
        this.profiles = await resumeApi.listProfiles()
        console.log('[ResumeView] API 返回数据:', JSON.stringify(this.profiles, null, 2))
        console.log('[ResumeView] profiles 数量:', this.profiles.length)
        if (this.profiles.length > 0) {
          const first = this.profiles[0]
          console.log('[ResumeView] 第一个 profile 字段:', {
            id: first.id,
            has_experience: !!first.experience,
            experience_count: first.experience?.length,
            has_project_experience: !!first.project_experience,
            project_experience_count: first.project_experience?.length,
            has_skills: !!first.skills,
            skills_count: first.skills?.length,
            has_education: !!first.education,
            education_count: first.education?.length,
            has_summary: !!first.summary,
            summary_length: first.summary?.length,
            all_keys: Object.keys(first)
          })
        }
        for (const profile of this.profiles) {
          this.loadRecommendations(profile)
        }
      } catch (e) {
        console.error('加载简历列表失败', e)
      } finally {
        this.loading = false
      }
    },

    async loadRecommendations(profile) {
      try {
        const recs = await resumeApi.getRecommendations(profile.id)
        profile.recommendations = recs
      } catch (e) {}
    },

    async generateRecommendations(profileId) {
      this.generatingIds.add(profileId)
      try {
        await resumeApi.generateRecommendations(profileId)
        const profile = this.profiles.find(p => p.id === profileId)
        if (profile) await this.loadRecommendations(profile)
      } catch (e) {
        console.error('生成推荐失败', e)
      } finally {
        this.generatingIds.delete(profileId)
      }
    },

    triggerUpload() {
      this.$refs.fileInput.click()
    },

    async handleFileChange(event) {
      const file = event.target.files[0]
      if (!file) return
      if (!file.name.endsWith('.pdf')) {
        this.uploadStatus = '仅支持 PDF 格式'
        return
      }
      this.uploading = true
      this.uploadStatus = '正在解析简历...'
      try {
        await resumeApi.uploadResume(file)
        this.uploadStatus = '✅ 解析完成'
        await this.loadProfiles()
      } catch (e) {
        console.error('上传失败', e)
        this.uploadStatus = '❌ 解析失败，请重试'
      } finally {
        this.uploading = false
      }
      event.target.value = ''
    },

    async deleteProfile(profileId) {
      if (!confirm('确定删除该简历画像？')) return
      try {
        await resumeApi.deleteProfile(profileId)
        this.profiles = this.profiles.filter(p => p.id !== profileId)
        if (this.editingId === profileId) {
          this.editingId = null
          delete this.editData[profileId]
        }
      } catch (e) {
        console.error('删除失败', e)
      }
    },

    // ---- Edit ----
    startEdit(profile) {
      this.editingId = profile.id
      this.editData[profile.id] = {
        summary: profile.summary || '',
        education: profile.education ? JSON.parse(JSON.stringify(profile.education)) : [],
        experience: profile.experience ? JSON.parse(JSON.stringify(profile.experience)) : [],
        project_experience: profile.project_experience ? JSON.parse(JSON.stringify(profile.project_experience)) : [],
        skills: profile.skills ? JSON.parse(JSON.stringify(profile.skills)) : []
      }
    },

    cancelEdit(profile) {
      this.editingId = null
      delete this.editData[profile.id]
    },

    async saveProfile(profile) {
      this.savingIds.add(profile.id)
      try {
        // 更新本地数据
        const edited = this.editData[profile.id]
        profile.summary = edited.summary
        profile.education = edited.education
        profile.experience = edited.experience
        profile.project_experience = edited.project_experience
        profile.skills = edited.skills

        // 刷新推荐（因为技能/经历可能影响推荐结果）
        await this.loadRecommendations(profile)

        this.editingId = null
        delete this.editData[profile.id]
      } catch (e) {
        console.error('保存失败', e)
      } finally {
        this.savingIds.delete(profile.id)
      }
    },

    // ---- Education ----
    addEducation(profile) {
      const arr = this.editData[profile.id].education
      arr.push({ school: '', degree: '', major: '' })
    },
    removeEducation(profile, idx) {
      this.editData[profile.id].education.splice(idx, 1)
    },

    // ---- Experience ----
    addExperience(profile) {
      const arr = this.editData[profile.id].experience
      arr.push({ company: '', position: '', start_date: '', end_date: '', description: '' })
    },
    removeExperience(profile, idx) {
      this.editData[profile.id].experience.splice(idx, 1)
    },

    // ---- Project ----
    addProject(profile) {
      const arr = this.editData[profile.id].project_experience
      arr.push({ project_name: '', role: '', date: '', description: '', technologies: '' })
    },
    removeProject(profile, idx) {
      this.editData[profile.id].project_experience.splice(idx, 1)
    },

    // ---- Skills ----
    addSkill(profile) {
      const arr = this.editData[profile.id].skills
      arr.push({ name: '', category: 'technical_skills', description: '' })
    },
    removeSkill(profile, idx) {
      this.editData[profile.id].skills.splice(idx, 1)
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
    },

    splitByDelimiter(str) {
      if (!str) return []
      return str.split(/[、，,；;|]/).map(s => s.trim()).filter(Boolean)
    },

    formatCategory(cat) {
      const map = { technical_skills: '技术', business_skills: '商业', tools_skills: '工具', content_skills: '内容' }
      return map[cat] || cat
    },

    formatStrengthType(type) {
      const map = { technical: '技术能力', project_execution: '项目执行', data_analysis: '数据分析', content_operations: '内容运营', collaboration: '协作沟通' }
      return map[type] || type
    },

    formatExpDate(dateStr) {
      if (!dateStr) return ''
      const numMatches = dateStr.match(/\d+/g)
      if (!numMatches || numMatches.length === 0) return dateStr

      const padYear = (n) => n.padStart(4, '0')
      const padMonth = (n) => n.padStart(2, '0')

      const isCurrent = /至今|current/.test(dateStr)
      if (isCurrent) {
        if (numMatches.length >= 1) {
          const year = padYear(numMatches[0])
          const month = numMatches.length >= 2 ? padMonth(numMatches[1]) : '01'
          return `${year}.${month}-至今`
        }
        return dateStr
      }

      const isRange = /[-—~]/.test(dateStr)

      if (!isRange) {
        if (numMatches.length === 1) return padYear(numMatches[0])
        if (numMatches.length === 2) return `${padYear(numMatches[0])}.${padMonth(numMatches[1])}`
        return dateStr
      }

      if (numMatches.length === 2) {
        const start = padYear(numMatches[0])
        const end = numMatches[1]
        const endNorm = end.length === 4 ? end + '.01' : end.padStart(2, '0')
        const startNorm = start.length === 4 ? start + '.01' : start
        if (startNorm === endNorm) return startNorm
        return `${startNorm}-${endNorm}`
      } else if (numMatches.length === 3) {
        const year1 = numMatches[0].padStart(4, '0')
        const month1 = numMatches[1].padStart(2, '0')
        const rest = numMatches[2]
        const startNorm = `${year1}.${month1}`
        const endNorm = rest.length === 4 ? rest + '.01' : rest.padStart(2, '0')
        if (startNorm === endNorm) return startNorm
        return `${startNorm}-${endNorm}`
      } else if (numMatches.length >= 4) {
        const year1 = numMatches[0].padStart(4, '0')
        const month1 = numMatches[1].padStart(2, '0')
        const year2 = numMatches[2].padStart(4, '0')
        const month2 = numMatches[3].padStart(2, '0')
        return `${year1}.${month1}-${year2}.${month2}`
      }
      return dateStr
    }
  }
}
</script>

<style scoped>
.resume-page {
  max-width: 980px;
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

/* Upload */
.upload-section {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 40px;
  text-align: center;
  margin-bottom: 28px;
  box-shadow: var(--shadow);
}

.upload-icon { font-size: 40px; margin-bottom: 12px; }
.upload-section h2 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.upload-section p {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 980px;
  padding: 14px 32px;
  font-size: 17px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-btn:hover:not(:disabled) { background: #0077ed; }
.upload-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

.upload-input { display: none; }
.upload-status { margin-top: 14px; font-size: 15px; color: var(--text-secondary); }

/* Profile Card */
.profile-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.profile-card-header {
  padding: 20px 28px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.profile-card-header h3 {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-bottom: 4px;
}

.profile-card-header .filename {
  font-size: 13px;
  color: var(--text-tertiary);
}

.profile-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-btn {
  padding: 8px 12px;
  font-size: 16px;
  background: var(--bg);
  color: var(--text-secondary);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  line-height: 1;
}

.edit-btn:hover { background: var(--blue-light); color: var(--blue); }

.gen-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  background: var(--blue-light);
  color: var(--blue);
  border: none;
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.gen-btn:hover:not(:disabled) { background: #d0e8ff; }
.gen-btn:disabled { background: var(--bg); color: var(--text-tertiary); cursor: not-allowed; }

.del-btn {
  padding: 8px 12px;
  font-size: 14px;
  background: var(--bg);
  color: var(--text-tertiary);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.del-btn:hover { background: #ffeaea; color: var(--red); }

/* Edit Toolbar */
.edit-toolbar {
  padding: 10px 28px;
  background: #f0f7ff;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.edit-hint {
  font-size: 13px;
  color: var(--blue);
  font-weight: 500;
}

.edit-toolbar-actions {
  display: flex;
  gap: 8px;
}

.save-btn {
  padding: 7px 18px;
  font-size: 14px;
  font-weight: 500;
  background: var(--blue);
  color: #fff;
  border: none;
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.save-btn:hover:not(:disabled) { background: #0077ed; }
.save-btn:disabled { background: var(--text-tertiary); cursor: not-allowed; }

.cancel-btn {
  padding: 7px 18px;
  font-size: 14px;
  font-weight: 500;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 980px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.cancel-btn:hover { background: var(--border); }

/* Section */
.profile-card-body {
  padding: 24px 28px 28px;
}

.section {
  margin-bottom: 24px;
}

.section:last-child { margin-bottom: 0; }

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-text {
  font-size: 17px;
  line-height: 1.6;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.edu-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.edu-item:last-child { border-bottom: none; padding-bottom: 0; }
.edu-item:first-child { padding-top: 0; }

.edu-school {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  margin-bottom: 4px;
}

.edu-detail {
  font-size: 14px;
  color: var(--text-secondary);
}

.exp-item, .proj-item {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
  margin-bottom: 10px;
  overflow: hidden;
}

.exp-item:last-child, .proj-item:last-child { margin-bottom: 0; }

.exp-header, .proj-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}

.exp-company, .proj-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
  word-break: keep-all;
}

.exp-position, .proj-role {
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: 6px;
}

.exp-time, .proj-duration {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.date-pending {
  color: var(--orange);
  font-weight: 400;
}

.exp-desc, .proj-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
  letter-spacing: -0.01em;
  word-break: normal;
  overflow-wrap: break-word;
  hyphens: none;
  padding: 8px 0 0;
}

.skills-list {
  display: flex;
  flex-direction: column;
}

.skill-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  gap: 16px;
}

.skill-row:last-child { border-bottom: none; padding-bottom: 0; }
.skill-row:first-child { padding-top: 0; }

.skill-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  word-break: keep-all;
  hyphens: none;
}

.skill-category {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: 980px;
  flex-shrink: 0;
}

.skill-desc {
  font-size: 14px;
  color: var(--text-secondary);
  text-align: right;
  max-width: 55%;
  word-break: normal;
  overflow-wrap: break-word;
}

.strengths-list {
  display: flex;
  flex-direction: column;
}

.strength-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.strength-item:last-child { border-bottom: none; padding-bottom: 0; }
.strength-item:first-child { padding-top: 0; }

.strength-score {
  font-size: 24px;
  font-weight: 700;
  color: var(--blue);
  min-width: 40px;
  text-align: center;
  letter-spacing: -0.02em;
}

.strength-desc {
  font-size: 15px;
  color: var(--text-primary);
  flex: 1;
  word-break: normal;
  overflow-wrap: break-word;
}

.strength-type {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg);
  padding: 3px 8px;
  border-radius: 980px;
  flex-shrink: 0;
}

.tech-tag {
  font-size: 12px;
  font-weight: 500;
  color: var(--blue);
  background: var(--blue-light);
  padding: 2px 8px;
  border-radius: 980px;
  margin-right: 4px;
  margin-top: 6px;
  display: inline-block;
  white-space: nowrap;
  word-break: keep-all;
  hyphens: none;
}

/* Recommendations */
.rec-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rec-item {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.rec-job-info {
  display: flex;
  flex-direction: column;
}

.rec-company {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.rec-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.rec-scores {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rec-score-item {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
}

.rec-score-item.rec-high { color: var(--green); }

.rec-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 980px;
  background: #e8f8ec;
  color: var(--green);
}

.rec-meta {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.rec-reason {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.rec-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.rec-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
}

.rec-tag-pos { background: #e8f8ec; color: var(--green); }
.rec-tag-neg { background: #ffeaea; color: var(--red); }

.rec-actions {
  margin-top: 8px;
}

.rec-link {
  font-size: 13px;
  color: var(--blue);
  text-decoration: none;
}

.rec-link:hover { text-decoration: underline; }

/* Empty */
.empty-state {
  text-align: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
  background: var(--bg-white);
  border-radius: var(--radius);
}

.empty-icon { font-size: 40px; margin-bottom: 12px; }
.empty-state p { font-size: 15px; }

.loading { text-align: center; padding: 40px; color: var(--text-tertiary); }

.empty-hint {
  font-size: 14px;
  color: var(--text-tertiary);
  padding: 8px 0;
}

/* ---- Edit mode controls ---- */
.add-btn {
  font-size: 12px;
  font-weight: 500;
  color: var(--blue);
  background: var(--blue-light);
  border: none;
  border-radius: 980px;
  padding: 3px 12px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

.add-btn:hover { background: #c0dfff; }

.edit-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.edit-row-skill {
  align-items: center;
}

.edit-input {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-white);
  color: var(--text-primary);
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.edit-input:focus {
  outline: none;
  border-color: var(--blue);
}

.edit-input-sm {
  flex: 0 0 140px;
}

.edit-textarea {
  width: 100%;
  padding: 8px 10px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-white);
  color: var(--text-primary);
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.15s ease;
  box-sizing: border-box;
}

.edit-textarea:focus {
  outline: none;
  border-color: var(--blue);
}

.edit-select {
  padding: 7px 10px;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-white);
  color: var(--text-primary);
  font-family: inherit;
  cursor: pointer;
  min-width: 90px;
}

.edit-select:focus {
  outline: none;
  border-color: var(--blue);
}

.remove-btn {
  padding: 6px 10px;
  font-size: 13px;
  background: var(--bg);
  color: var(--text-tertiary);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.remove-btn:hover { background: #ffeaea; color: var(--red); }
</style>
