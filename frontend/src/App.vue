<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <template v-if="auth.isLoggedIn">
      <!-- Top nav (tablet + desktop) -->
      <nav class="sticky top-0 z-30 bg-gray-900 border-b border-gray-800 px-4 py-3 flex items-center gap-4">
        <span class="text-xl font-bold text-orange-400">Overhang</span>
        <div class="hidden md:flex items-center gap-1 ml-2">
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
          <button @click="screen = 'settings'"
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="screen === 'settings' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'">
            Einstellungen
          </button>
        </div>
        <div class="ml-auto flex items-center gap-3">
          <span class="text-sm text-gray-400 hidden sm:inline">{{ auth.username }}</span>
          <button @click="auth.logout()" class="text-sm text-gray-500 hover:text-white transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-800">
            Abmelden
          </button>
        </div>
      </nav>

      <!-- Main content — extra bottom padding on mobile for bottom nav -->
      <main class="p-4 md:p-6 pb-24 md:pb-6 overflow-x-hidden">
        <LibraryView v-if="screen === 'library'" @open-model="openModel" />
        <CollectionsView v-else-if="screen === 'collections'" @open-model="openModel" />
        <SettingsView v-else-if="screen === 'settings'" />
      </main>

      <!-- Bottom nav (mobile only) -->
      <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800
                  flex items-stretch" style="padding-bottom: env(safe-area-inset-bottom);">
        <button v-for="item in navItems" :key="item.id"
          @click="screen = item.id"
          class="flex-1 flex flex-col items-center justify-center gap-1 py-3 text-xs transition-colors"
          :class="screen === item.id ? 'text-orange-400' : 'text-gray-500'">
          <component :is="item.icon" class="w-5 h-5" />
          {{ item.label }}
        </button>
      </nav>
    </template>

    <LoginView v-else @logged-in="() => {}" />
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { useAuthStore } from './stores/auth.js'
import LibraryView from './views/LibraryView.vue'
import CollectionsView from './views/CollectionsView.vue'
import SettingsView from './views/SettingsView.vue'
import LoginView from './views/LoginView.vue'

const auth = useAuthStore()
const screen = ref('library')

function openModel(id) {
  screen.value = 'library'
  pendingModelId.value = id
}

import { provide } from 'vue'
const pendingModelId = ref(null)
provide('pendingModelId', pendingModelId)

// Inline SVG icons for bottom nav
const IconLibrary = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2',
    d: 'M4 6h16M4 10h16M4 14h16M4 18h16' })
]) }
const IconCollections = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2',
    d: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' })
]) }
const IconSettings = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2',
    d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' }),
  h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M15 12a3 3 0 11-6 0 3 3 0 016 0' })
]) }

const navItems = [
  { id: 'library',     label: 'Bibliothek',  icon: IconLibrary },
  { id: 'collections', label: 'Sammlungen',  icon: IconCollections },
  { id: 'settings',    label: 'Einstellungen', icon: IconSettings },
]
</script>
