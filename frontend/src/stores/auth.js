import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isAdmin = ref(localStorage.getItem('is_admin') === 'true')

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(data) {
    token.value = data.access_token
    username.value = data.username
    isAdmin.value = data.is_admin
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('is_admin', String(data.is_admin))
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
  }

  function logout() {
    token.value = ''
    username.value = ''
    isAdmin.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('is_admin')
    delete axios.defaults.headers.common['Authorization']
  }

  // Restore axios header on app start
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  return { token, username, isAdmin, isLoggedIn, setAuth, logout }
})
