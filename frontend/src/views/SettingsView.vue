<template>
  <div class="max-w-xl mx-auto space-y-4">
    <h2 class="text-xl font-bold mb-6">Einstellungen</h2>

    <!-- Admin: User Management -->
    <div v-if="auth.isAdmin" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-medium">Benutzerverwaltung</h3>
        <button @click="showCreateUser = true"
          class="flex items-center gap-1.5 text-sm bg-orange-500 hover:bg-orange-400 px-3 py-1.5 rounded-lg font-medium transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          Benutzer anlegen
        </button>
      </div>

      <!-- User list -->
      <div v-if="users.length" class="divide-y divide-gray-800">
        <div v-for="u in users" :key="u.id" class="py-3 flex items-center gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-medium text-sm">{{ u.username }}</span>
              <span v-if="u.is_admin" class="text-xs bg-orange-500/20 text-orange-300 px-1.5 py-0.5 rounded">Admin</span>
              <span v-if="!u.is_active" class="text-xs bg-yellow-500/20 text-yellow-300 px-1.5 py-0.5 rounded">Ausstehend</span>
              <span v-if="u.id === auth.userId" class="text-xs text-gray-600">(du)</span>
            </div>
            <p v-if="u.email" class="text-xs text-gray-500 mt-0.5 truncate">{{ u.email }}</p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <!-- Approve -->
            <button v-if="!u.is_active"
              @click="approveUser(u)"
              class="text-xs text-green-400 hover:text-green-300 px-2 py-1 rounded hover:bg-gray-800 transition-colors">
              Freischalten
            </button>
            <!-- Actions menu -->
            <div class="relative" v-if="u.id !== auth.userId || true">
              <button @click="openMenu(u)" class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 5a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm0 7a1.5 1.5 0 110-3 1.5 1.5 0 010 3z"/>
                </svg>
              </button>
              <div v-if="menuUserId === u.id"
                class="absolute right-0 top-8 z-20 bg-gray-800 border border-gray-700 rounded-lg shadow-xl min-w-[160px] py-1"
                @click.stop>
                <button @click="startResetPassword(u)" class="w-full text-left text-sm px-3 py-2 hover:bg-gray-700 transition-colors">
                  Passwort setzen
                </button>
                <button v-if="!u.is_admin" @click="toggleAdmin(u, true)" class="w-full text-left text-sm px-3 py-2 hover:bg-gray-700 transition-colors">
                  Zum Admin machen
                </button>
                <button v-if="u.is_admin && u.id !== auth.userId" @click="toggleAdmin(u, false)" class="w-full text-left text-sm px-3 py-2 hover:bg-gray-700 transition-colors">
                  Admin-Rechte entziehen
                </button>
                <button v-if="u.is_active" @click="deactivateUser(u)" class="w-full text-left text-sm px-3 py-2 hover:bg-gray-700 transition-colors text-yellow-400">
                  Sperren
                </button>
                <button v-if="u.id !== auth.userId" @click="confirmDelete(u)" class="w-full text-left text-sm px-3 py-2 hover:bg-gray-700 transition-colors text-red-400">
                  Löschen
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p v-else-if="usersLoaded" class="text-sm text-gray-500">Keine Benutzer gefunden.</p>
      <div v-else class="flex justify-center py-4">
        <div class="w-6 h-6 border-2 border-gray-700 border-t-orange-400 rounded-full animate-spin"></div>
      </div>

      <!-- Password reset inline -->
      <div v-if="resetTarget" class="mt-4 bg-gray-800 rounded-lg p-4">
        <p class="text-sm font-medium mb-3">Passwort für <span class="text-orange-300">{{ resetTarget.username }}</span> setzen</p>
        <div class="flex gap-2">
          <input v-model="newPassword" type="password" placeholder="Neues Passwort (min. 8 Zeichen)"
            class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
          <button @click="doResetPassword" :disabled="newPassword.length < 8"
            class="bg-orange-500 hover:bg-orange-400 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium">
            Setzen
          </button>
          <button @click="resetTarget = null; newPassword = ''" class="text-sm text-gray-400 hover:text-white px-2">✕</button>
        </div>
        <p v-if="resetMsg" class="text-xs mt-2" :class="resetMsg.ok ? 'text-green-400' : 'text-red-400'">{{ resetMsg.text }}</p>
      </div>

      <!-- Delete confirm -->
      <div v-if="deleteTarget" class="mt-4 bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3 flex items-center gap-3">
        <span class="text-sm text-gray-300">Benutzer <strong class="text-white">{{ deleteTarget.username }}</strong> und alle seine Modelle löschen?</span>
        <button @click="doDelete" class="text-sm text-red-400 font-medium shrink-0">Ja, löschen</button>
        <button @click="deleteTarget = null" class="text-sm text-gray-500 shrink-0">Abbrechen</button>
      </div>

      <p v-if="adminMsg" class="mt-3 text-sm" :class="adminMsg.ok ? 'text-green-400' : 'text-red-400'">{{ adminMsg.text }}</p>
    </div>

    <!-- Create user modal -->
    <div v-if="showCreateUser" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showCreateUser = false">
      <div class="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6 text-gray-100">
        <h3 class="font-semibold mb-4">Neuen Benutzer anlegen</h3>
        <div class="space-y-3">
          <input v-model="createForm.username" type="text" placeholder="Benutzername"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
          <input v-model="createForm.email" type="email" placeholder="E-Mail (optional)"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
          <input v-model="createForm.password" type="password" placeholder="Passwort (min. 8 Zeichen)"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-400" />
          <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
            <input v-model="createForm.is_admin" type="checkbox" class="accent-orange-400" />
            Admin-Rechte
          </label>
        </div>
        <p v-if="createError" class="text-red-400 text-sm mt-3">{{ createError }}</p>
        <div class="flex gap-3 justify-end mt-4">
          <button @click="showCreateUser = false; createError = ''" class="text-sm text-gray-400 hover:text-white px-4 py-2">Abbrechen</button>
          <button @click="doCreateUser" :disabled="!createForm.username || createForm.password.length < 8"
            class="bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-sm px-4 py-2 rounded-lg font-medium">
            Anlegen
          </button>
        </div>
      </div>
    </div>

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
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 class="font-medium mb-1">Vertrauenswürdiges Zertifikat</h3>
      <p class="text-sm text-gray-500 mb-4">
        Installiere das Overhang-Zertifikat einmalig auf deinem Gerät. Danach funktionieren
        Downloads und der Slicer-Import ohne Warnungen.
      </p>

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

    <!-- Platform file download info -->
    <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-5 text-sm text-gray-500">
      <p class="font-medium text-gray-400 mb-1">MakerWorld, Printables & Cults3d</p>
      <p>Diese Plattformen erfordern einen Account für Datei-Downloads — ein automatischer Download ist nicht möglich.
        Dateien einfach auf der jeweiligen Plattform herunterladen und per
        <span class="text-gray-300">Drag & Drop</span> ins Modell ziehen.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { saveCredential, deleteCredential, testCredential, adminListUsers, adminCreateUser, adminUpdateUser, adminDeleteUser } from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// Admin user management
const users = ref([])
const usersLoaded = ref(false)
const menuUserId = ref(null)
const resetTarget = ref(null)
const newPassword = ref('')
const resetMsg = ref(null)
const deleteTarget = ref(null)
const adminMsg = ref(null)
const showCreateUser = ref(false)
const createError = ref('')
const createForm = reactive({ username: '', email: '', password: '', is_admin: false })

function openMenu(u) {
  menuUserId.value = menuUserId.value === u.id ? null : u.id
  resetTarget.value = null
  deleteTarget.value = null
}

// Close menu on outside click
if (typeof document !== 'undefined') {
  document.addEventListener('click', () => { menuUserId.value = null })
}

async function loadUsers() {
  try {
    users.value = await adminListUsers()
  } finally {
    usersLoaded.value = true
  }
}

async function approveUser(u) {
  menuUserId.value = null
  await adminUpdateUser(u.id, { is_active: true })
  u.is_active = true
  showAdminMsg(true, `${u.username} freigeschaltet`)
}

async function deactivateUser(u) {
  menuUserId.value = null
  await adminUpdateUser(u.id, { is_active: false })
  u.is_active = false
  showAdminMsg(true, `${u.username} gesperrt`)
}

async function toggleAdmin(u, val) {
  menuUserId.value = null
  await adminUpdateUser(u.id, { is_admin: val })
  u.is_admin = val
  showAdminMsg(true, val ? `${u.username} ist jetzt Admin` : `Admin-Rechte von ${u.username} entzogen`)
}

function startResetPassword(u) {
  menuUserId.value = null
  resetTarget.value = u
  newPassword.value = ''
  resetMsg.value = null
}

async function doResetPassword() {
  try {
    await adminUpdateUser(resetTarget.value.id, { password: newPassword.value })
    resetMsg.value = { ok: true, text: 'Passwort gesetzt' }
    newPassword.value = ''
    setTimeout(() => { resetTarget.value = null; resetMsg.value = null }, 2000)
  } catch (e) {
    resetMsg.value = { ok: false, text: e.response?.data?.detail || 'Fehler' }
  }
}

function confirmDelete(u) {
  menuUserId.value = null
  deleteTarget.value = u
}

async function doDelete() {
  try {
    await adminDeleteUser(deleteTarget.value.id)
    users.value = users.value.filter(u => u.id !== deleteTarget.value.id)
    deleteTarget.value = null
    showAdminMsg(true, 'Benutzer gelöscht')
  } catch (e) {
    showAdminMsg(false, e.response?.data?.detail || 'Fehler beim Löschen')
    deleteTarget.value = null
  }
}

async function doCreateUser() {
  createError.value = ''
  try {
    const u = await adminCreateUser({
      username: createForm.username,
      password: createForm.password,
      email: createForm.email || undefined,
      is_admin: createForm.is_admin,
    })
    users.value.push(u)
    showCreateUser.value = false
    Object.assign(createForm, { username: '', email: '', password: '', is_admin: false })
    showAdminMsg(true, `${u.username} angelegt`)
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Fehler'
  }
}

function showAdminMsg(ok, text) {
  adminMsg.value = { ok, text }
  setTimeout(() => { adminMsg.value = null }, 3000)
}

// Thingiverse
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
  if (auth.isAdmin) loadUsers()
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
