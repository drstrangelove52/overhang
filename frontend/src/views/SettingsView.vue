<template>
  <div class="max-w-2xl mx-auto">
    <h2 class="text-xl font-bold mb-6">Einstellungen</h2>

    <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 class="font-medium mb-1">Plattform-Logins</h3>
      <p class="text-sm text-gray-500 mb-5">
        Zugangsdaten werden AES-256-verschlüsselt auf deinem Server gespeichert und nur für Datei-Downloads verwendet.
      </p>

      <div class="space-y-4">
        <div v-for="p in platforms" :key="p.id" class="border border-gray-800 rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm">{{ p.label }}</span>
              <span v-if="saved[p.id]" class="text-xs text-green-500">✓ Gespeichert</span>
            </div>
            <div class="flex items-center gap-2">
              <button v-if="saved[p.id]" @click="testPlatform(p.id)"
                :disabled="testing[p.id]"
                class="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-800 disabled:opacity-50">
                {{ testing[p.id] ? 'Teste…' : 'Testen' }}
              </button>
              <button v-if="saved[p.id]" @click="removePlatform(p.id)"
                class="text-xs text-red-500 hover:text-red-400 px-2 py-1 rounded hover:bg-gray-800">
                Entfernen
              </button>
            </div>
          </div>

          <!-- Test result -->
          <div v-if="testResult[p.id]" class="mb-3 text-xs px-3 py-2 rounded-lg"
            :class="testResult[p.id].ok ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'">
            {{ testResult[p.id].message }}
          </div>

          <div class="space-y-2">
            <div>
              <label class="text-xs text-gray-500 block mb-1">{{ p.userLabel }}</label>
              <input v-model="forms[p.id].username" :type="p.userLabel === 'API Token' ? 'password' : 'text'"
                :placeholder="p.userPlaceholder"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
            </div>
            <div v-if="p.hasPassword">
              <label class="text-xs text-gray-500 block mb-1">Passwort</label>
              <input v-model="forms[p.id].password" type="password" placeholder="••••••••"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
            </div>
          </div>

          <button @click="savePlatform(p.id)" :disabled="!canSave(p)"
            class="mt-3 bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-sm px-4 py-1.5 rounded-lg font-medium transition-colors">
            Speichern
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listCredentials, saveCredential, deleteCredential, testCredential } from '../api.js'

const platforms = [
  {
    id: 'makerworld',
    label: 'MakerWorld (Bambu Lab)',
    userLabel: 'E-Mail',
    userPlaceholder: 'you@example.com',
    hasPassword: true,
  },
  {
    id: 'thingiverse',
    label: 'Thingiverse',
    userLabel: 'API Token',
    userPlaceholder: 'Token aus thingiverse.com/developers',
    hasPassword: false,
  },
  {
    id: 'printables',
    label: 'Printables',
    userLabel: 'E-Mail',
    userPlaceholder: 'you@example.com',
    hasPassword: true,
  },
]

const forms = ref(Object.fromEntries(platforms.map(p => [p.id, { username: '', password: '' }])))
const saved = ref({})
const testing = ref({})
const testResult = ref({})

onMounted(async () => {
  const creds = await listCredentials()
  for (const c of creds) {
    saved.value[c.platform] = true
    forms.value[c.platform] = { username: c.username, password: '••••••••' }
  }
})

function canSave(p) {
  const f = forms.value[p.id]
  if (!f.username.trim()) return false
  if (p.hasPassword && (!f.password.trim() || f.password === '••••••••')) {
    // Allow save if username changed (password already set)
    return saved.value[p.id] ? f.username !== '' : false
  }
  return true
}

async function savePlatform(id) {
  const p = platforms.find(x => x.id === id)
  const f = forms.value[id]
  const pw = f.password === '••••••••' ? '' : f.password
  await saveCredential(id, f.username, pw || f.username) // for token-only: username=token, password=token
  saved.value[id] = true
  testResult.value[id] = null
}

async function removePlatform(id) {
  await deleteCredential(id)
  saved.value[id] = false
  forms.value[id] = { username: '', password: '' }
  testResult.value[id] = null
}

async function testPlatform(id) {
  testing.value[id] = true
  testResult.value[id] = null
  try {
    const r = await testCredential(id)
    testResult.value[id] = r
  } catch (e) {
    testResult.value[id] = { ok: false, message: e.response?.data?.detail || 'Fehler beim Testen' }
  } finally {
    testing.value[id] = false
  }
}
</script>
