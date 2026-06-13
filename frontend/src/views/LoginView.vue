<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center p-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-orange-400">Overhang</h1>
        <p class="text-gray-500 text-sm mt-1">3D Model Library</p>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <!-- Tab toggle -->
        <div class="flex bg-gray-800 rounded-lg p-1 mb-6">
          <button
            v-for="t in ['login', 'register']" :key="t"
            @click="tab = t"
            class="flex-1 py-1.5 text-sm rounded-md transition-colors"
            :class="tab === t ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'"
          >
            {{ t === 'login' ? 'Anmelden' : 'Registrieren' }}
          </button>
        </div>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="text-xs text-gray-400 block mb-1">Benutzername</label>
            <input v-model="form.username" type="text" required autocomplete="username"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400" />
          </div>

          <div v-if="tab === 'register'">
            <label class="text-xs text-gray-400 block mb-1">E-Mail (optional)</label>
            <input v-model="form.email" type="email" autocomplete="email"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400" />
          </div>

          <div>
            <label class="text-xs text-gray-400 block mb-1">Passwort</label>
            <input v-model="form.password" type="password" required autocomplete="current-password"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400" />
            <p v-if="tab === 'register'" class="text-xs text-gray-600 mt-1">Mindestens 8 Zeichen</p>
          </div>

          <p v-if="error" class="text-red-400 text-sm">{{ error }}</p>

          <button type="submit" :disabled="loading"
            class="w-full bg-orange-500 hover:bg-orange-400 disabled:opacity-40 py-2.5 rounded-lg text-sm font-medium transition-colors">
            <span v-if="loading" class="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin align-middle mr-2"></span>
            {{ tab === 'login' ? 'Anmelden' : 'Account erstellen' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth.js'

const emit = defineEmits(['logged-in'])
const auth = useAuthStore()

const tab = ref('login')
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', email: '', password: '' })

async function submit() {
  error.value = ''
  loading.value = true
  try {
    let data
    if (tab.value === 'login') {
      const params = new URLSearchParams({ username: form.username, password: form.password })
      const r = await axios.post('/api/auth/login', params)
      data = r.data
    } else {
      const r = await axios.post('/api/auth/register', {
        username: form.username,
        password: form.password,
        email: form.email || undefined,
      })
      data = r.data
    }
    auth.setAuth(data)
    emit('logged-in')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Fehler beim Anmelden'
  } finally {
    loading.value = false
  }
}
</script>
