import axios from 'axios'

const api = axios.create({
  baseURL: 'https://aicareeragent-production.up.railway.app/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

const userId = () => JSON.parse(localStorage.getItem('user') || '{}').id || 1

export const authApi = {
  sendCode: async (phone) => {
    const res = await api.post('/auth/send-code', { phone })
    return res.data
  },
  register: async (data) => {
    const res = await api.post('/auth/register', data)
    return res.data
  },
  login: async (data) => {
    const res = await api.post('/auth/login', data)
    return res.data
  },
  getMe: async () => {
    const res = await api.get('/auth/me')
    return res.data
  },
  logout: async () => {
    await api.post('/auth/logout')
  }
}

export const resumeApi = {
  uploadResume: async (file, versionName) => {
    const formData = new FormData()
    formData.append('file', file)
    if (versionName) formData.append('version_name', versionName)
    const res = await api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },
  listProfiles: async () => {
    const res = await api.get('/resume/profiles')
    return res.data
  },
  getProfile: async (profileId) => {
    const res = await api.get(`/resume/profiles/${profileId}`)
    return res.data
  },
  deleteProfile: async (profileId) => {
    const res = await api.delete(`/resume/profiles/${profileId}`)
    return res.data
  },
  getRecommendations: async (profileId) => {
    const res = await api.get(`/recommend/${profileId}`)
    return res.data
  },
  generateRecommendations: async (profileId) => {
    const res = await api.post(`/recommend/generate/${profileId}`)
    return res.data
  },
  listVersions: async (profileId) => {
    const res = await api.get('/resume-versions/', { params: profileId ? { resume_profile_id: profileId } : {} })
    return res.data
  },
  createVersion: async (data) => {
    const res = await api.post('/resume-versions/', data)
    return res.data
  },
  deleteVersion: async (versionId) => {
    const res = await api.delete(`/resume-versions/${versionId}`)
    return res.data
  }
}

export const jobApi = {
  listJobs: async (params = {}) => {
    const res = await api.get('/jobs', { params })
    return res.data
  },
  getJob: async (jobId) => {
    const res = await api.get(`/jobs/${jobId}`)
    return res.data
  },
  getApplyInfo: async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/apply-info`)
    return res.data
  },
  seedJobs: async () => {
    const res = await api.post('/jobs/seed')
    return res.data
  },
  getMatch: async (profileId, jobId) => {
    const res = await api.get('/match/match', { params: { profile_id: profileId, job_id: jobId } })
    return res.data
  },
  getAnalysis: async (profileId, jobId) => {
    const res = await api.get(`/match/analysis/${profileId}/${jobId}`)
    return res.data
  },
  saveJob: async (jobId) => {
    const res = await api.post(`/applications/save/${jobId}`, null, { params: { user_id: userId() } })
    return res.data
  },
  removeSavedJob: async (jobId) => {
    const res = await api.delete(`/applications/save/${jobId}`, { params: { user_id: userId() } })
    return res.data
  },
  getSavedJobs: async () => {
    const res = await api.get(`/applications/saved/${userId()}`)
    return res.data
  },
  getFilterOptions: async () => {
    const res = await api.get('/jobs/filters/filter-options')
    return res.data
  },
  rankJobs: async (profileId, limit = 20) => {
    const res = await api.get(`/jobs/rank/${profileId}`, { params: { user_id: userId(), limit } })
    return res.data
  },
  advancedSearch: async (params) => {
    const res = await api.get('/jobs/source/search/advanced', { params })
    return res.data
  },
  getForeignJobs: async (limit = 20) => {
    const res = await api.get('/jobs/source/foreign', { params: { limit } })
    return res.data
  },
  getCampusJobs: async (limit = 20) => {
    const res = await api.get('/jobs/source/campus', { params: { limit } })
    return res.data
  },
  getRemoteJobs: async (limit = 20) => {
    const res = await api.get('/jobs/source/remote', { params: { limit } })
    return res.data
  },
  getJobStats: async () => {
    const res = await api.get('/jobs/source/stats')
    return res.data
  },
  syncJobs: async (sourceName = null) => {
    const params = sourceName ? { source_name: sourceName } : {}
    const res = await api.post('/jobs/source/sync', null, { params })
    return res.data
  },
  listSources: async () => {
    const res = await api.get('/jobs/source/sources')
    return res.data
  },
  listAdapters: async () => {
    const res = await api.get('/jobs/source/adapters')
    return res.data
  }
}

export const applicationApi = {
  listApplications: async () => {
    const res = await api.get(`/applications/user/${userId()}`)
    return res.data
  },
  updateStatus: async (applicationId, status, notes = null) => {
    const res = await api.patch(`/applications/${applicationId}/status?status=${status}&notes=${notes || ''}`)
    return res.data
  },
  applyJob: async (jobId, profileId) => {
    const res = await api.post('/applications/', { user_id: userId(), job_id: jobId, resume_profile_id: profileId })
    return res.data
  },
  getDashboard: async () => {
    const res = await api.get(`/tracker/dashboard/${userId()}`)
    return res.data
  },
  optimizeResume: async (profileId, jobId) => {
    const res = await api.post('/applications/optimize', null, { params: { resume_profile_id: profileId, job_id: jobId } })
    return res.data
  }
}

export const interviewApi = {
  generateQuestions: async (jobId, questionTypes) => {
    const res = await api.post(`/interview/generate/${jobId}`, null, { params: { question_types: questionTypes } })
    return res.data
  },
  getQuestions: async (jobId) => {
    const res = await api.get(`/interview/questions/${jobId}`)
    return res.data
  },
  createSession: async (jobId) => {
    const res = await api.post('/interview/session/create', { user_id: userId(), job_id: jobId })
    return res.data
  },
  submitAnswer: async (sessionId, answerData) => {
    const res = await api.post(`/interview/session/${sessionId}/answer`, answerData)
    return res.data
  },
  evaluateAnswer: async (answerId) => {
    const res = await api.post(`/interview/evaluate/${answerId}`)
    return res.data
  },
  getSession: async (sessionId) => {
    const res = await api.get(`/interview/session/${sessionId}`)
    return res.data
  },
  getHistory: async () => {
    const res = await api.get(`/interview/history/${userId()}`)
    return res.data
  },
  getStats: async () => {
    const res = await api.get(`/interview/stats/${userId()}`)
    return res.data
  }
}

export const agentApi = {
  chat: async (message, sessionId = null) => {
    const res = await api.post('/agent/chat', { user_id: userId(), message, session_id: sessionId })
    return res.data
  },
  getInsights: async () => {
    const res = await api.get(`/agent/insights/${userId()}`)
    return res.data
  },
  createLearningPlan: async () => {
    const res = await api.post(`/agent/learning/plan/create/${userId()}`)
    return res.data
  },
  getLearningTasks: async () => {
    const res = await api.get(`/agent/learning/tasks/${userId()}`)
    return res.data
  },
  getDashboard: async () => {
    const res = await api.get(`/agent/dashboard/${userId()}`)
    return res.data
  },
  getNotifications: async (limit = 20) => {
    const res = await api.get(`/agent/notifications/${userId()}`, { params: { limit } })
    return res.data
  },
  markRead: async (notificationId) => {
    const res = await api.post(`/agent/notifications/${notificationId}/read`)
    return res.data
  },
  markAllRead: async () => {
    const res = await api.post(`/agent/notifications/${userId()}/read-all`)
    return res.data
  },
  checkNotifications: async () => {
    const res = await api.post(`/agent/notifications/check/${userId()}`)
    return res.data
  },
  getDailyTasks: async () => {
    const res = await api.get(`/ai-agent/daily-tasks/${userId()}`)
    return res.data
  },
  getSkillRecommendations: async () => {
    const res = await api.get(`/ai-agent/skill-recommendations/${userId()}`)
    return res.data
  },
  getApplicationPlan: async () => {
    const res = await api.get(`/ai-agent/application-plan/${userId()}`)
    return res.data
  },
  getInterviewPlan: async () => {
    const res = await api.get(`/ai-agent/interview-plan/${userId()}`)
    return res.data
  }
}

export const learningApi = {
  generatePlan: async (profileId, jobId) => {
    const res = await api.post(`/learning/generate/${profileId}/${jobId}`)
    return res.data
  },
  listPlans: async (profileId) => {
    const res = await api.get(`/learning/plans/${profileId}`)
    return res.data
  }
}

export const companyApi = {
  search: async (companyName) => {
    const res = await api.get(`/company/search/${companyName}`)
    return res.data
  },
  getById: async (companyId) => {
    const res = await api.get(`/company/${companyId}`)
    return res.data
  }
}

export const goalApi = {
  getGoals: async () => {
    const res = await api.get(`/goals/${userId()}`)
    return res.data
  },
  createGoal: async (data) => {
    const res = await api.post('/goals/create', null, { params: { user_id: userId(), ...data } })
    return res.data
  },
  updateGoal: async (goalId, data) => {
    const res = await api.put(`/goals/${goalId}`, null, { params: data })
    return res.data
  },
  deleteGoal: async (goalId) => {
    const res = await api.delete(`/goals/${goalId}`)
    return res.data
  },
  getTargetCompanies: async () => {
    const res = await api.get(`/companies/${userId()}`)
    return res.data
  },
  addTargetCompany: async (data) => {
    const res = await api.post('/companies', null, { params: { user_id: userId(), ...data } })
    return res.data
  },
  deleteTargetCompany: async (companyId) => {
    const res = await api.delete(`/companies/${companyId}`)
    return res.data
  },
  getPreferences: async () => {
    const res = await api.get(`/preferences/${userId()}`)
    return res.data
  },
  updatePreferences: async (data) => {
    const res = await api.put(`/preferences/${userId()}`, null, { params: data })
    return res.data
  },
  getProgress: async () => {
    const res = await api.get(`/progress/${userId()}`)
    return res.data
  },
  updateProgress: async (data) => {
    const res = await api.put(`/progress/${userId()}`, null, { params: data })
    return res.data
  }
}

export const gapApi = {
  analyze: async (profileId, jobId) => {
    const res = await api.get(`/gap-analysis/analyze/${profileId}/${jobId}`)
    return res.data
  },
  getHistory: async (profileId, jobId) => {
    const res = await api.get(`/gap-analysis/history/${profileId}/${jobId}`)
    return res.data
  }
}

export default api
