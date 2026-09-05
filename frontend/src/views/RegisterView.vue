<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <h1 class="auth-title">AI 职业助手</h1>
        <p class="auth-subtitle">智能简历解析 · 精准岗位匹配</p>
      </div>

      <div class="auth-card">
        <div class="auth-form">
          <h2 class="auth-form-title">注册</h2>
          <div class="form-group">
            <label class="form-label">手机号</label>
            <div class="phone-row">
              <input
                v-model="form.phone"
                type="tel"
                maxlength="11"
                class="form-input phone-input"
                placeholder="请输入手机号"
              />
              <button
                class="code-btn"
                @click="handleSendCode"
                :disabled="codeSending || codeCountdown > 0"
              >
                {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">验证码</label>
            <input
              ref="verificationCodeInput"
              v-model="form.code"
              type="text"
              maxlength="6"
              class="form-input"
              placeholder="请输入6位验证码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <input
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="请设置6位以上密码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">姓名（可选）</label>
            <input
              v-model="form.fullName"
              type="text"
              class="form-input"
              placeholder="请输入您的姓名"
            />
          </div>
          <button
            class="auth-btn"
            @click="handleRegister"
            :disabled="registerLoading"
          >
            {{ registerLoading ? '注册中...' : '注册' }}
          </button>
          <p class="auth-switch">
            已有账号？
            <span class="auth-link" @click="$router.push('/login')">去登录</span>
          </p>
          <p v-if="errorMsg" class="auth-error">{{ errorMsg }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'
import { authApi } from '../api/index.js'

const router = useRouter()
const userStore = useUserStore()

const form = ref({ phone: '', code: '', password: '', fullName: '' })
const verificationCodeInput = ref(null)
const registerLoading = ref(false)
const codeSending = ref(false)
const codeCountdown = ref(0)
const errorMsg = ref('')

async function handleRegister() {
  errorMsg.value = ''
  if (!form.value.phone || !form.value.code || !form.value.password) {
    errorMsg.value = '请填写完整信息'
    return
  }
  if (!/^1[3-9]\d{9}$/.test(form.value.phone)) {
    errorMsg.value = '请输入正确的手机号'
    return
  }
  if (form.value.password.length < 6) {
    errorMsg.value = '密码至少6位'
    return
  }
  if (!/^\d{6}$/.test(form.value.code)) {
    errorMsg.value = '请输入6位验证码'
    return
  }
  registerLoading.value = true
  try {
    await authApi.register({
      phone: form.value.phone,
      password: form.value.password,
      verify_code: form.value.code,
      full_name: form.value.fullName || null
    })
    // 注册成功后自动登录
    const res = await authApi.login({ phone: form.value.phone, password: form.value.password })
    await userStore.login(res)
    router.push('/home')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '注册失败，请重试'
  } finally {
    registerLoading.value = false
  }
}

async function handleSendCode() {
  errorMsg.value = ''
  if (!/^1[3-9]\d{9}$/.test(form.value.phone)) {
    errorMsg.value = '请输入正确的手机号'
    return
  }
  codeSending.value = true
  try {
    const res = await authApi.sendCode(form.value.phone)
    const code = String(res?.code || '')
    console.log('[VERIFY] API response:', JSON.stringify(res))
    console.log('[VERIFY] code:', code)
    form.value.code = code
    console.log('[VERIFY] form.code before DOM:', form.value.code)
    console.log('[VERIFY] input ref:', verificationCodeInput.value)
    await nextTick()
    if (verificationCodeInput.value) {
      const inputEl = verificationCodeInput.value
      console.log('[VERIFY] DOM value before:', inputEl.value)
      HTMLInputElement.prototype.value.set.call(inputEl, code)
      inputEl.dispatchEvent(new Event('input', { bubbles: true }))
      console.log('[VERIFY] DOM value after:', inputEl.value)
      console.log('[VERIFY] form.code after:', form.value.code)
    } else {
      console.warn('[VERIFY] input ref is null!')
    }
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '发送失败，请重试'
  } finally {
    codeSending.value = false
  }
}
</script>
