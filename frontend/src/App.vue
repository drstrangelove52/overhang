<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <template v-if="auth.isLoggedIn">
      <nav class="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-3">
        <span class="text-xl font-bold text-orange-400">Overhang</span>
        <span class="text-gray-600 text-sm hidden sm:inline">3D Model Library</span>
        <div class="ml-auto flex items-center gap-3">
          <span class="text-sm text-gray-400 hidden sm:inline">{{ auth.username }}</span>
          <button @click="logout" class="text-sm text-gray-500 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-800">
            Abmelden
          </button>
        </div>
      </nav>
      <main class="p-6">
        <LibraryView />
      </main>
    </template>

    <LoginView v-else @logged-in="() => {}" />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth.js'
import LibraryView from './views/LibraryView.vue'
import LoginView from './views/LoginView.vue'

const auth = useAuthStore()

function logout() {
  auth.logout()
}
</script>
