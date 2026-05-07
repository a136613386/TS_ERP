import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getUserInfo, refreshToken, logout } from '@/api/auth'
import type { LoginForm, UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function loginAction(form: LoginForm) {
    const res = await login(form)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
  }

  async function getUserInfoAction() {
    const res = await getUserInfo()
    userInfo.value = res
    return res
  }

  async function refreshTokenAction() {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) {
      throw new Error('No refresh token')
    }
    const res = await refreshToken(refresh_token)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    return res
  }

  async function logoutAction() {
    await logout()
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    loginAction,
    getUserInfoAction,
    refreshTokenAction,
    logoutAction
  }
})
