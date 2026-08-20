<template>
  <div class="main-layout">
    <!-- Top Navigation -->
    <nav class="main-nav">
      <router-link to="/home" class="nav-brand">🎯 AI 职业助手</router-link>
      <div class="nav-links">
        <router-link to="/home" :class="{ active: $route.path === '/home' }">首页</router-link>
        <router-link to="/resume" :class="{ active: $route.path.startsWith('/resume') }">简历</router-link>
        <router-link to="/jobs" :class="{ active: $route.path.startsWith('/jobs') }">岗位</router-link>
        <router-link to="/applications" :class="{ active: $route.path.startsWith('/applications') }">投递</router-link>
        <router-link to="/interview" :class="{ active: $route.path.startsWith('/interview') }">面试</router-link>
        <router-link to="/agent" :class="{ active: $route.path.startsWith('/agent') }">AI 顾问</router-link>
        <router-link to="/learning" :class="{ active: $route.path.startsWith('/learning') }">学习</router-link>
        <router-link to="/goals" :class="{ active: $route.path.startsWith('/goals') }">目标</router-link>
        <router-link to="/company" :class="{ active: $route.path.startsWith('/company') }">公司</router-link>
        <router-link to="/profile" :class="{ active: $route.path.startsWith('/profile') }">我的</router-link>
      </div>
      <div class="nav-right">
        <div class="nav-user" v-if="userStore.isLoggedIn">
          <span class="nav-username">{{ userStore.userName }}</span>
        </div>
        <button class="nav-logout" @click="handleLogout">退出</button>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useUserStore } from '../stores/user.js'
import router from '../router/index.js'
import { authApi } from '../api/index.js'

const userStore = useUserStore()

async function handleLogout() {
  try { await authApi.logout() } catch (e) {}
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 32px;
  height: 64px;
  background: var(--bg-white);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  text-decoration: none;
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  gap: 4px;
  flex: 1;
  overflow-x: auto;
}

.nav-links a {
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 980px;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-links a:hover {
  background: var(--bg);
  color: var(--text-primary);
}

.nav-links a.active {
  background: var(--blue-light);
  color: var(--blue);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-username {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.nav-logout {
  font-size: 14px;
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px 14px;
  border-radius: 980px;
  transition: all 0.2s ease;
  font-family: inherit;
}

.nav-logout:hover {
  background: var(--bg);
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  background: var(--bg);
}

@media (max-width: 734px) {
  .main-nav {
    padding: 0 16px;
    gap: 12px;
  }
  .nav-links a {
    padding: 6px 10px;
    font-size: 13px;
  }
}
</style>
