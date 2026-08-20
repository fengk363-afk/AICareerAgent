import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/index.js'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || '{}'))
  const isLoggedIn = ref(!!localStorage.getItem('token'))

  // Getters
  const userId = computed(() => userInfo.value.id || null)
  const userName = computed(() => userInfo.value.full_name || userInfo.value.phone || '同学')
  const userPhone = computed(() => userInfo.value.phone || '')
  const userAvatar = computed(() => {
    const name = userInfo.value.full_name || ''
    return name ? name.charAt(0).toUpperCase() : 'U'
  })

  // Actions
  async function login(res) {
    token.value = res.access_token
    userInfo.value = { id: res.user_id, phone: res.phone, full_name: res.full_name || '' }
    isLoggedIn.value = true
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify({ id: res.user_id, phone: res.phone, full_name: res.full_name || '' }))
  }

  async function fetchProfile() {
    try {
      const data = await authApi.getMe()
      userInfo.value = { ...userInfo.value, ...data }
      localStorage.setItem('user', JSON.stringify(userInfo.value))
    } catch (e) {
      console.error('Failed to fetch profile', e)
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = {}
    isLoggedIn.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('profileId')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    userId,
    userName,
    userPhone,
    userAvatar,
    login,
    fetchProfile,
    logout
  }
})
