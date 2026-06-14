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

      <!-- Step 1: Download -->
      <div class="mb-5">
        <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Schritt 1 — Zertifikat herunterladen</p>
        <p class="text-sm text-gray-400 mb-3">
          Öffne diese Adresse direkt in der Adressleiste deines Browsers
          (funktioniert auch wenn die Seite noch als unsicher angezeigt wird):
        </p>
        <div class="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2">
          <code class="text-sm text-orange-400 flex-1 select-all">{{ certDownloadUrl }}</code>
          <button @click="copyCertUrl" class="text-xs text-gray-500 hover:text-white flex-shrink-0 transition-colors">
            {{ copied ? 'Kopiert ✓' : 'Kopieren' }}
          </button>
        </div>
        <p class="text-xs text-gray-600 mt-2">
          Oder wenn du bereits auf dieser Seite bist:
          <a :href="caUrl" download="overhang-ca.crt" class="text-orange-400 hover:underline">direkt herunterladen ↓</a>
        </p>
      </div>

      <!-- Steps 2-4: Install -->
      <div>
        <p class="text-xs text-gray-500 uppercase tracking-wide mb-2">Schritt 2 — Zertifikat installieren</p>
        <ol class="space-y-2 text-sm text-gray-400">
          <li class="flex gap-3">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">1</span>
            <span>Doppelklick auf die heruntergeladene <code class="text-orange-400">overhang-ca.crt</code></span>
          </li>
          <li class="flex gap-3">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">2</span>
            <span><em>Zertifikat installieren</em> → <em>Lokaler Computer</em> → Weiter</span>
          </li>
          <li class="flex gap-3">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">3</span>
            <span><strong class="text-gray-300">Alle Zertifikate in folgendem Speicher speichern</strong> → Durchsuchen → <strong class="text-gray-300">Vertrauenswürdige Stammzertifizierungsstellen</strong> → OK → Weiter → Fertig stellen → Ja</span>
          </li>
          <li class="flex gap-3">
            <span class="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-gray-300 text-xs flex items-center justify-center font-medium">4</span>
            <span>Browser neu starten → <strong class="text-gray-300">fertig</strong></span>
          </li>
        </ol>
      </div>
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
import { ref, onMounted } from 'vue'
import { saveCredential, deleteCredential, testCredential } from '../api.js'

const caUrl = '/overhang-ca.crt'
const certDownloadUrl = `http://${window.location.hostname}/overhang-ca.crt`
const copied = ref(false)
function copyCertUrl() {
  navigator.clipboard.writeText(certDownloadUrl)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

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
