<template>
  <div class="app-container">
    <!-- Nav -->
    <nav class="app-nav">
      <router-link to="/home" class="nav-brand">AI 职业助手</router-link>
      <div class="nav-links">
        <router-link to="/home" :class="{ active: $route.path === '/home' }">首页</router-link>
        <router-link to="/resume" :class="{ active: $route.path === '/resume' }">简历</router-link>
        <router-link to="/jobs" :class="{ active: $route.path === '/jobs' }">岗位</router-link>
        <router-link to="/applications" :class="{ active: $route.path === '/applications' }">投递</router-link>
        <router-link to="/interview" :class="{ active: $route.path === '/interview' }">面试</router-link>
        <router-link to="/agent" :class="{ active: $route.path === '/agent' }">AI 顾问</router-link>
        <router-link to="/learning" :class="{ active: $route.path === '/learning' }">学习</router-link>
        <router-link to="/goals" :class="{ active: $route.path === '/goals' }">目标</router-link>
        <router-link to="/company" :class="{ active: $route.path === '/company' }">公司</router-link>
        <router-link to="/profile" :class="{ active: $route.path === '/profile' }">我的</router-link>
      </div>
      <button class="nav-logout" @click="handleLogout">退出</button>
    </nav>

    <!-- Page Content -->
    <router-view />
  </div>
</template>

<script setup>
import { authApi } from './api/index.js'
import router from './router'

async function handleLogout() {
  try { await authApi.logout() } catch (e) {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('profileId')
  router.push('/login')
}
</script>
