<template>
  <div v-if="!detailId">

    <!-- Import bar -->
    <div class="mb-6">
      <div class="relative">
        <div class="absolute inset-0 rounded-xl bg-orange-500/10 border border-orange-500/40 pointer-events-none"
             :class="importFocused ? 'border-orange-400 bg-orange-500/15' : ''"></div>
        <div class="relative flex items-center gap-3 px-4 py-3">
          <svg class="w-5 h-5 text-orange-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          <input
            v-model="importUrl"
            type="url"
            placeholder="URL von Printables, MakerWorld, Thingiverse einfügen und Enter drücken…"
            class="flex-1 bg-transparent text-sm text-white placeholder-orange-300/50 focus:outline-none"
            @focus="importFocused = true"
            @blur="importFocused = false"
            @keydown.enter="startImport"
            @paste.once="onPaste"
            ref="importInput"
          />
          <div v-if="importState === 'running'" class="flex items-center gap-2 text-orange-400 text-sm shrink-0">
            <div class="w-4 h-4 border-2 border-orange-400 border-t-transparent rounded-full animate-spin"></div>
            {{ importStatusText }}
          </div>
          <div v-else-if="importState === 'done'" class="text-green-400 text-sm shrink-0">✓ Importiert</div>
          <div v-else-if="importState === 'error'" class="text-red-400 text-sm shrink-0 max-w-xs truncate" :title="importError">{{ importError }}</div>
          <button v-else-if="importUrl"
            @click="startImport"
            class="shrink-0 bg-orange-500 hover:bg-orange-400 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors">
            Importieren
          </button>
        </div>
      </div>
    </div>

    <!-- Search + filter bar -->
    <div class="flex gap-3 mb-6">
      <div class="relative flex-1">
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
      <select v-model="filterPlatform" @change="load()"
        class="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-orange-400 text-gray-300">
        <option value="">Alle Plattformen</option>
        <option value="printables">Printables</option>
        <option value="thingiverse">Thingiverse</option>
        <option value="makerworld">MakerWorld</option>
      </select>
    </div>

    <!-- Stats -->
    <p v-if="total > 0" class="text-sm text-gray-500 mb-4">{{ total }} Modell{{ total !== 1 ? 'e' : '' }}</p>

    <!-- Grid -->
    <div v-if="models.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
      <ModelCard v-for="m in models" :key="m.id" :model="m" @click="openDetail(m.id)" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-24 text-center">
      <svg class="w-16 h-16 text-gray-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M20 7l-8-4-8 4m16 0v10l-8 4m-8-4V7m8 4v10"/>
      </svg>
      <p class="text-gray-500">
        {{ searchQuery ? 'Keine Modelle gefunden.' : 'Noch keine Modelle. Füge oben eine URL ein!' }}
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

  <!-- Detail view -->
  <ModelDetailView v-else :model-id="detailId" @back="detailId = null" @deleted="onDeleted" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listModels, importModel, pollJob } from '../api.js'
import ModelCard from '../components/ModelCard.vue'
import ModelDetailView from './ModelDetailView.vue'

const models = ref([])
const total = ref(0)
const loading = ref(false)
const detailId = ref(null)
const searchQuery = ref('')
const filterPlatform = ref('')
let searchTimer = null

// Import state
const importUrl = ref('')
const importState = ref('idle') // idle | running | done | error
const importError = ref('')
const importStatusText = ref('Importiere…')
const importFocused = ref(false)
const importInput = ref(null)

onMounted(() => load())

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
    importState.value = 'error'
    importError.value = e.response?.data?.detail || e.message || 'Import fehlgeschlagen'
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
    if (job.result?.step === 'downloading') {
      importStatusText.value = 'Lädt Dateien…'
    }
  }
  importState.value = 'error'
  importError.value = 'Timeout'
}

function onPaste() {
  setTimeout(() => {
    if (importUrl.value.trim().startsWith('http')) startImport()
  }, 50)
}

async function load(reset = true) {
  loading.value = true
  if (reset) models.value = []
  const data = await listModels({
    q: searchQuery.value || undefined,
    platform: filterPlatform.value || undefined,
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

function openDetail(id) {
  detailId.value = id
}

function onDeleted() {
  detailId.value = null
  load()
}

const sleep = ms => new Promise(r => setTimeout(r, ms))
</script>
