<template>
  <div class="profile-page">
    <div class="profile-card">
      <div class="profile-header">
        <div class="profile-avatar">{{ user?.full_name?.[0] || user?.phone?.slice(-1) || '👤' }}</div>
        <div class="profile-info">
          <h2 class="profile-name">{{ user?.full_name || '未设置姓名' }}</h2>
          <p class="profile-phone">{{ user?.phone || '未绑定手机号' }}</p>
        </div>
      </div>

      <div class="profile-section">
        <div class="section-title">个人信息</div>
        <div class="info-list">
          <div class="info-row">
            <span class="info-label">手机号</span>
            <span class="info-value">{{ user?.phone || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">姓名</span>
            <span class="info-value">{{ user?.full_name || '未设置' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">注册时间</span>
            <span class="info-value">{{ formatDate(user?.created_at) }}</span>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <div class="section-title">求职偏好</div>
        <div class="info-list">
          <div class="info-row">
            <span class="info-label">目标岗位</span>
            <span class="info-value">{{ preference?.target_role || '未设置' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">目标城市</span>
            <span class="info-value">{{ preference?.target_location || '未设置' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">目标行业</span>
            <span class="info-value">{{ preference?.target_industry || '未设置' }}</span>
          </div>
        </div>
        <router-link to="/goals" class="profile-link">
          管理职业目标
          <span class="link-arrow">→</span>
        </router-link>
      </div>

      <div class="profile-section">
        <div class="section-title">简历管理</div>
        <router-link to="/resume" class="profile-link">
          查看简历画像
          <span class="link-arrow">→</span>
        </router-link>
      </div>

      <div class="profile-section">
        <div class="section-title">求职工具</div>
        <router-link to="/interview" class="profile-link">
          面试教练
          <span class="link-arrow">→</span>
        </router-link>
        <router-link to="/agent" class="profile-link">
          AI 职业顾问
          <span class="link-arrow">→</span>
        </router-link>
        <router-link to="/learning" class="profile-link">
          学习路线
          <span class="link-arrow">→</span>
        </router-link>
        <router-link to="/company" class="profile-link">
          公司研究
          <span class="link-arrow">→</span>
        </router-link>
      </div>

      <div class="profile-actions">
        <button class="action-btn primary" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script>
import { authApi } from '../api/index.js'

export default {
  name: 'ProfileView',
  data() {
    return {
      user: null,
      preference: null
    }
  },
  async created() {
    await this.loadProfile()
  },
  methods: {
    async loadProfile() {
      try {
        this.user = await authApi.getMe()
      } catch (e) {
        console.error('加载用户信息失败', e)
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleDateString('zh-CN')
    },
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.profile-page {
  display: flex;
  justify-content: center;
  padding: 32px 24px 80px;
}

.profile-card {
  background: var(--bg-white);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow);
  max-width: 600px;
  width: 100%;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}

.profile-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--blue-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: var(--blue);
  flex-shrink: 0;
}

.profile-name {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}

.profile-phone {
  font-size: 15px;
  color: var(--text-secondary);
}

.profile-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}

.profile-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  margin-bottom: 14px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 15px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.profile-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 15px;
  color: var(--blue);
  text-decoration: none;
  border-bottom: 1px solid var(--border);
}

.profile-link:last-child { border-bottom: none; }
.profile-link:hover { opacity: 0.8; }

.link-arrow {
  font-size: 18px;
  color: var(--text-tertiary);
}

.profile-actions {
  margin-top: 24px;
}

.action-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.action-btn.primary {
  background: var(--bg);
  color: var(--red);
}

.action-btn.primary:hover {
  background: #ffeaea;
}
</style>
