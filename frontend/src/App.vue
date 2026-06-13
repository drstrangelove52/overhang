<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <template v-if="auth.isLoggedIn">
      <nav class="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-4">
        <span class="text-xl font-bold text-orange-400">Overhang</span>
        <div class="flex items-center gap-1 ml-2">
          <button @click="screen = 'library'"
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="screen === 'library' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'">
            Bibliothek
          </button>
          <button @click="screen = 'collections'"
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="screen === 'collections' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'">
            Sammlungen
          </button>
        </div>
        <div class="ml-auto flex items-center gap-3">
          <span class="text-sm text-gray-400 hidden sm:inline">{{ auth.username }}</span>
          <button @click="auth.logout()" class="text-sm text-gray-500 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-800">
            Abmelden
          </button>
        </div>
      </nav>
      <main class="p-6">
        <LibraryView v-if="screen === 'library'" @open-model="openModel" />
        <CollectionsView v-else-if="screen === 'collections'" @open-model="openModel" />
      </main>
    </template>

    <LoginView v-else @logged-in="() => {}" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from './stores/auth.js'
import LibraryView from './views/LibraryView.vue'
import CollectionsView from './views/CollectionsView.vue'
import LoginView from './views/LoginView.vue'

const auth = useAuthStore()
const screen = ref('library')

function openModel(id) {
  // Switch to library and open model detail
  screen.value = 'library'
  // LibraryView needs to handle this — emit via a shared approach
  // Simplest: use a global ref
  pendingModelId.value = id
}

// Simple cross-component communication
import { provide } from 'vue'
const pendingModelId = ref(null)
provide('pendingModelId', pendingModelId)
</script>
