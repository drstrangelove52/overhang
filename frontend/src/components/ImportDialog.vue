<template>
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6">
      <h2 class="text-lg font-semibold mb-4">Modell importieren</h2>

      <div v-if="state === 'idle'">
        <label class="text-sm text-gray-400 block mb-1">URL (Printables, Thingiverse, …)</label>
        <input
          v-model="url"
          type="url"
          placeholder="https://www.printables.com/model/..."
          class="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-orange-400"
          @keydown.enter="startImport"
        />
        <p v-if="error" class="text-red-400 text-sm mt-2">{{ error }}</p>
        <div class="flex gap-3 mt-4 justify-end">
          <button @click="$emit('close')" class="px-4 py-2 text-sm text-gray-400 hover:text-white">Abbrechen</button>
          <button @click="startImport" :disabled="!url" class="px-4 py-2 bg-orange-500 hover:bg-orange-400 disabled:opacity-40 rounded-lg text-sm font-medium">
            Importieren
          </button>
        </div>
      </div>

      <div v-else-if="state === 'running'" class="text-center py-6">
        <div class="inline-block w-10 h-10 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p class="text-gray-300 text-sm">{{ statusText }}</p>
        <p class="text-gray-500 text-xs mt-1">Bilder und Dateien werden heruntergeladen…</p>
      </div>

      <div v-else-if="state === 'done'" class="text-center py-4">
        <div class="text-4xl mb-3">✅</div>
        <p class="font-medium">{{ result.title }}</p>
        <p class="text-gray-400 text-sm mt-1">Modell wurde importiert</p>
        <div class="flex gap-3 mt-5 justify-center">
          <button @click="$emit('close')" class="px-4 py-2 text-sm text-gray-400 hover:text-white">Schließen</button>
          <button @click="$emit('open-model', result.model_id)" class="px-4 py-2 bg-orange-500 hover:bg-orange-400 rounded-lg text-sm font-medium">
            Anzeigen
          </button>
        </div>
      </div>

      <div v-else-if="state === 'error'" class="py-4">
        <p class="text-red-400 font-medium mb-2">Import fehlgeschlagen</p>
        <p class="text-gray-400 text-sm">{{ error }}</p>
        <div class="flex gap-3 mt-4 justify-end">
          <button @click="reset" class="px-4 py-2 text-sm text-gray-400 hover:text-white">Zurück</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { importModel, pollJob } from '../api.js'

const emit = defineEmits(['close', 'done', 'open-model'])

const url = ref('')
const state = ref('idle')
const error = ref('')
const result = ref(null)
const statusText = ref('Scraping läuft…')

async function startImport() {
  if (!url.value) return
  error.value = ''
  state.value = 'running'
  try {
    const job = await importModel(url.value)
    await waitForJob(job.job_id)
  } catch (e) {
    state.value = 'error'
    error.value = e.response?.data?.detail || e.message
  }
}

async function waitForJob(jobId) {
  for (let i = 0; i < 60; i++) {
    await sleep(2000)
    const job = await pollJob(jobId)
    if (job.state === 'SUCCESS') {
      result.value = job.result
      state.value = 'done'
      emit('done')
      return
    }
    if (job.state === 'FAILURE') {
      state.value = 'error'
      error.value = job.error || 'Unbekannter Fehler'
      return
    }
    if (job.result?.step === 'downloading') {
      statusText.value = 'Dateien werden heruntergeladen…'
    }
  }
  state.value = 'error'
  error.value = 'Timeout — Import dauert zu lange'
}

function reset() {
  state.value = 'idle'
  error.value = ''
  url.value = ''
}

const sleep = ms => new Promise(r => setTimeout(r, ms))
</script>
