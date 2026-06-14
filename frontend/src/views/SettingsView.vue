<template>
  <div class="max-w-xl mx-auto">
    <h2 class="text-xl font-bold mb-6">Einstellungen</h2>

    <!-- Thingiverse -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="font-medium">Thingiverse API Token</h3>
        <span v-if="configured" class="text-xs text-green-500">✓ Verbunden</span>
      </div>
      <p class="text-sm text-gray-500 mb-4">
        Mit einem API Token werden Dateien beim Import automatisch heruntergeladen.<br>
        Token erstellen unter
        <a href="https://www.thingiverse.com/developers/apps" target="_blank" class="text-orange-400 hover:underline">
          thingiverse.com/developers/apps ↗
        </a>
      </p>

      <div class="flex gap-2">
        <input v-model="token" type="password" placeholder="Token einfügen…"
          class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
        <button @click="save" :disabled="!token.trim()"
          class="bg-orange-500 hover:bg-orange-400 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          Speichern
        </button>
      </div>

      <div v-if="result" class="mt-3 text-sm px-3 py-2 rounded-lg"
        :class="result.ok ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'">
        {{ result.message }}
      </div>

      <div v-if="configured" class="mt-3 flex gap-3">
        <button @click="test" :disabled="testing"
          class="text-sm text-gray-400 hover:text-white disabled:opacity-50">
          {{ testing ? 'Teste…' : 'Verbindung testen' }}
        </button>
        <button @click="remove" class="text-sm text-red-500 hover:text-red-400">
          Entfernen
        </button>
      </div>
    </div>

    <!-- SSL Certificate -->
    <div class="mt-4 bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 class="font-medium mb-1">Vertrauenswürdiges Zertifikat</h3>
      <p class="text-sm text-gray-500 mb-4">
        Installiere das Overhang-Zertifikat einmalig auf deinem Gerät. Danach funktionieren
        Downloads und der Slicer-Import ohne Warnungen.
      </p>

      <a :href="caUrl" download="overhang-ca.crt"
        class="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-400 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
        </svg>
        Zertifikat herunterladen
      </a>

      <ol class="mt-5 space-y-3 text-sm text-gray-400">
        <li class="flex gap-3">
          <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">1</span>
          <span>Zertifikat herunterladen (Button oben)</span>
        </li>
        <li class="flex gap-3">
          <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">2</span>
          <span>Doppelklick auf die heruntergeladene <code class="text-orange-400">overhang-ca.crt</code></span>
        </li>
        <li class="flex gap-3">
          <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">3</span>
          <span>→ <em>Zertifikat installieren</em> → <em>Lokaler Computer</em> → <em>Zertifikate in folgendem Speicher</em> → <strong class="text-gray-300">Vertrauenswürdige Stammzertifizierungsstellen</strong> → Fertig stellen</span>
        </li>
        <li class="flex gap-3">
          <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">4</span>
          <span>Browser neu starten — fertig</span>
        </li>
      </ol>
    </div>

    <!-- MakerWorld / Printables info -->
    <div class="mt-4 bg-gray-900/50 border border-gray-800 rounded-xl p-5 text-sm text-gray-500">
      <p class="font-medium text-gray-400 mb-1">MakerWorld & Printables</p>
      <p>Diese Plattformen verwenden 2FA — ein automatischer Login ist nicht möglich.
        Dateien einfach auf der jeweiligen Plattform herunterladen und per
        <span class="text-gray-300">Drag & Drop</span> ins Modell ziehen.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { saveCredential, deleteCredential, testCredential } from '../api.js'

// CA cert is served over HTTP so it can be downloaded before cert is trusted
const caUrl = computed(() => `http://${window.location.hostname}/overhang-ca.crt`)

const token = ref('')
const configured = ref(false)
const testing = ref(false)
const result = ref(null)

onMounted(async () => {
  // Use the simplified endpoint
  try {
    const r = await fetch('/api/credentials/thingiverse', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    if (r.ok) {
      const d = await r.json()
      configured.value = d.configured
    }
  } catch {}
})

async function save() {
  result.value = null
  // For Thingiverse: token goes as both username and password field
  await saveCredential('thingiverse', token.value, token.value)
  configured.value = true
  token.value = ''
  result.value = { ok: true, message: 'Token gespeichert' }
  setTimeout(() => { result.value = null }, 3000)
}

async function test() {
  testing.value = true
  result.value = null
  try {
    result.value = await testCredential('thingiverse')
  } catch (e) {
    result.value = { ok: false, message: e.response?.data?.detail || 'Fehler' }
  } finally {
    testing.value = false
  }
}

async function remove() {
  await deleteCredential('thingiverse')
  configured.value = false
  result.value = null
}
</script>
