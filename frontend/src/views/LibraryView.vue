<template>
  <!-- Library always visible -->
  <div>
    <!-- Import bar -->
    <div class="mb-4">
      <div class="relative">
        <div class="absolute inset-0 rounded-xl bg-orange-500/10 border border-orange-500/40 pointer-events-none"
             :class="importFocused ? 'border-orange-400 bg-orange-500/15' : ''"></div>
        <div class="relative flex items-center gap-2 px-3 py-3">
          <svg class="w-5 h-5 text-orange-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          <input
            v-model="importUrl"
            type="url"
            placeholder="URL einfügen…"
            class="flex-1 min-w-0 bg-transparent text-sm text-white placeholder-orange-300/50 focus:outline-none"
            @focus="importFocused = true"
            @blur="importFocused = false"
            @keydown.enter="startImport"
            @paste="onPaste"
            ref="importInput"
          />
          <div v-if="importState === 'running'" class="flex items-center gap-2 text-orange-400 text-sm shrink-0">
            <div class="w-4 h-4 border-2 border-orange-400 border-t-transparent rounded-full animate-spin"></div>
            <span class="hidden sm:inline">{{ importStatusText }}</span>
          </div>
          <div v-else-if="importState === 'done'" class="text-green-400 text-sm shrink-0">✓</div>
          <div v-else-if="importState === 'duplicate'" class="text-orange-400 text-xs shrink-0 max-w-[8rem] truncate" :title="importError">{{ importError }}</div>
          <div v-else-if="importState === 'error'" class="text-red-400 text-xs shrink-0 max-w-[8rem] truncate" :title="importError">{{ importError }}</div>
          <button v-else-if="importUrl"
            @click="startImport"
            class="shrink-0 bg-orange-500 hover:bg-orange-400 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors">
            Import
          </button>
        </div>
      </div>
    </div>

    <!-- Search + filter bar -->
    <div class="flex flex-col sm:flex-row gap-2 mb-3">
      <div class="relative flex-1 min-w-0">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M17 11A6 6 0 111 11a6 6 0 0116 0z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Modelle suchen…"
          class="w-full bg-gray-900 border border-gray-700 rounded-lg pl-9 pr-4 py-2.5 text-sm focus:outline-none focus:border-orange-400"
          @input="onSearch"
        />
      </div>
      <div class="flex gap-2">
        <select v-model="filterPlatform" @change="load()"
          class="flex-1 sm:flex-none bg-gray-900 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400 text-gray-300">
          <option value="">Alle Plattformen</option>
          <option value="printables">Printables</option>
          <option value="thingiverse">Thingiverse</option>
          <option value="makerworld">MakerWorld</option>
        </select>
        <select v-model="sortOrder" @change="load()"
          class="flex-1 sm:flex-none bg-gray-900 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400 text-gray-300">
          <option value="date_desc">Neueste</option>
          <option value="date_asc">Älteste</option>
          <option value="title_asc">A → Z</option>
          <option value="title_desc">Z → A</option>
        </select>
      </div>
    </div>

    <!-- Active tag filter chip -->
    <div v-if="filterTag" class="flex items-center gap-2 mb-4">
      <span class="text-xs text-gray-500">Tag:</span>
      <span class="flex items-center gap-1 text-xs bg-orange-500/20 text-orange-300 border border-orange-500/40 pl-2.5 pr-1 py-1 rounded-full">
        {{ filterTag }}
        <button @click="clearTagFilter" class="text-orange-400 hover:text-white leading-none ml-0.5">×</button>
      </span>
    </div>

    <!-- Stats -->
    <p v-if="total > 0" class="text-sm text-gray-500 mb-4">{{ total }} Modell{{ total !== 1 ? 'e' : '' }}</p>

    <!-- Grid -->
    <div v-if="models.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
      <ModelCard v-for="m in models" :key="m.id" :model="m"
        @click="openDetail(m.id)"
        @tag-click="setTagFilter" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-24 text-center">
      <svg class="w-16 h-16 text-gray-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M20 7l-8-4-8 4m16 0v10l-8 4m-8-4V7m8 4v10"/>
      </svg>
      <p class="text-gray-500">
        {{ filterTag ? `Keine Modelle mit Tag „${filterTag}".` : searchQuery ? 'Keine Modelle gefunden.' : 'Noch keine Modelle. Füge oben eine URL ein!' }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="w-8 h-8 border-2 border-gray-700 border-t-orange-400 rounded-full animate-spin"></div>
    </div>

    <!-- Load more -->
    <div v-if="models.length < total && !loading" class="flex justify-center mt-8">
      <button @click="loadMore" class="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm">
        Mehr laden
      </button>
    </div>
  </div>

  <!-- Model detail modal -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="detailId"
           class="fixed inset-0 z-40 overflow-y-auto backdrop-blur-sm"
           style="background: rgba(0,0,0,0.82);"
           @click.self="closeDetail">
        <div class="min-h-full flex items-start justify-center p-4 sm:p-6">
          <div class="relative w-full max-w-5xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl my-4 sm:my-8 text-gray-100"
               @click.stop>
            <!-- Close button -->
            <button @click="closeDetail"
                    class="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center
                           bg-gray-800 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white transition-colors text-lg leading-none"
                    title="Schliessen (ESC)">
              ×
            </button>
            <div class="p-5 sm:p-8">
              <ModelDetailView :model-id="detailId"
                @back="closeDetail"
                @deleted="onDeleted"
                @filter-tag="onFilterTag" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, inject, watch } from 'vue'
import { listModels, importModel, pollJob } from '../api.js'
import ModelCard from '../components/ModelCard.vue'
import ModelDetailView from './ModelDetailView.vue'

const models = ref([])
const total = ref(0)
const loading = ref(false)
const detailId = ref(null)
const searchQuery = ref('')
const filterPlatform = ref('')
const filterTag = ref('')
const sortOrder = ref('date_desc')
let searchTimer = null

// Import state
const importUrl = ref('')
const importState = ref('idle')
const importError = ref('')
const importStatusText = ref('Importiere…')
const importFocused = ref(false)
const importInput = ref(null)

const pendingModelId = inject('pendingModelId', null)
if (pendingModelId) {
  watch(pendingModelId, (id) => {
    if (id) { openDetail(id); pendingModelId.value = null }
  })
}

function openDetail(id) {
  detailId.value = id
}

function closeDetail() {
  detailId.value = null
}

// Lock body scroll while modal is open, restore on close
watch(detailId, (id) => {
  document.body.style.overflow = id ? 'hidden' : ''
})

// ESC closes the modal
function onKeydown(e) {
  if (e.key === 'Escape' && detailId.value) closeDetail()
}

onMounted(() => {
  load()
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

async function startImport() {
  const url = importUrl.value.trim()
  if (!url || importState.value === 'running') return
  importState.value = 'running'
  importError.value = ''
  importStatusText.value = 'Importiere…'
  try {
    const job = await importModel(url)
    await waitForJob(job.job_id)
  } catch (e) {
    if (e.response?.status === 409) {
      importState.value = 'duplicate'
      importError.value = e.response.data.detail
      importUrl.value = ''
      setTimeout(() => { importState.value = 'idle' }, 4000)
    } else {
      importState.value = 'error'
      importError.value = e.response?.data?.detail || e.message || 'Import fehlgeschlagen'
    }
  }
}

async function waitForJob(jobId) {
  for (let i = 0; i < 60; i++) {
    await sleep(2000)
    const job = await pollJob(jobId)
    if (job.state === 'SUCCESS') {
      importState.value = 'done'
      importUrl.value = ''
      load()
      setTimeout(() => { importState.value = 'idle' }, 3000)
      return
    }
    if (job.state === 'FAILURE') {
      importState.value = 'error'
      importError.value = job.error || 'Unbekannter Fehler'
      return
    }
    if (job.result?.step === 'downloading') importStatusText.value = 'Lädt Dateien…'
  }
  importState.value = 'error'
  importError.value = 'Timeout'
}

function onPaste(e) {
  const text = e.clipboardData?.getData('text') || ''
  if (!text.trim().startsWith('http')) return
  importState.value = 'idle'
  importError.value = ''
  setTimeout(() => startImport(), 50)
}

async function load(reset = true) {
  loading.value = true
  if (reset) models.value = []
  const data = await listModels({
    q: searchQuery.value || undefined,
    platform: filterPlatform.value || undefined,
    tag: filterTag.value || undefined,
    sort: sortOrder.value !== 'date_desc' ? sortOrder.value : undefined,
    skip: reset ? 0 : models.value.length,
    limit: 48,
  })
  if (reset) {
    models.value = data.items
  } else {
    models.value.push(...data.items)
  }
  total.value = data.total
  loading.value = false
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(), 400)
}

async function loadMore() {
  await load(false)
}

function onDeleted() {
  closeDetail()
  load()
}

function setTagFilter(tag) {
  filterTag.value = tag
  load()
}

function clearTagFilter() {
  filterTag.value = ''
  load()
}

function onFilterTag(tag) {
  closeDetail()
  filterTag.value = tag
  load()
}

const sleep = ms => new Promise(r => setTimeout(r, ms))
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>
