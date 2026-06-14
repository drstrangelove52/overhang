<template>
  <!-- Detail view of one collection -->
  <div v-if="activeColId">
    <button @click="activeColId = null" class="flex items-center gap-2 text-gray-400 hover:text-white mb-6 text-sm">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Alle Sammlungen
    </button>

    <div v-if="activeCol">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold">{{ activeCol.name }}</h2>
          <p v-if="activeCol.description" class="text-sm text-gray-500 mt-1">{{ activeCol.description }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="editingCol = true" class="text-sm text-gray-400 hover:text-white px-3 py-1.5 rounded-lg hover:bg-gray-800">
            Bearbeiten
          </button>
          <button @click="confirmDeleteCol = true" class="text-sm text-red-500 hover:text-red-400 px-3 py-1.5 rounded-lg hover:bg-gray-800">
            Löschen
          </button>
        </div>
      </div>

      <!-- Edit modal -->
      <div v-if="editingCol" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="editingCol = false">
        <div class="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6">
          <h3 class="font-semibold mb-4">Sammlung bearbeiten</h3>
          <input v-model="editName" type="text" placeholder="Name"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:border-orange-400" />
          <textarea v-model="editDesc" rows="3" placeholder="Beschreibung (optional)"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:border-orange-400 resize-none" />
          <div class="flex gap-3 justify-end">
            <button @click="editingCol = false" class="text-sm text-gray-400 hover:text-white px-4 py-2">Abbrechen</button>
            <button @click="saveEdit" class="bg-orange-500 hover:bg-orange-400 text-sm px-4 py-2 rounded-lg font-medium">Speichern</button>
          </div>
        </div>
      </div>

      <!-- Delete confirm -->
      <div v-if="confirmDeleteCol" class="mb-4 flex items-center gap-3 bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3">
        <span class="text-sm text-gray-300">Sammlung wirklich löschen?</span>
        <button @click="doDeleteCol" class="text-sm text-red-400 font-medium">Ja, löschen</button>
        <button @click="confirmDeleteCol = false" class="text-sm text-gray-500">Abbrechen</button>
      </div>

      <div v-if="activeCol.models?.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
        <ModelCard v-for="m in activeCol.models" :key="m.id" :model="m" @click="openDetail(m.id)" />
      </div>
      <p v-else class="text-gray-500 text-sm py-12 text-center">
        Noch keine Modelle. Füge Modelle über die Modell-Detailansicht hinzu.
      </p>
    </div>
    <div v-else class="flex justify-center py-12">
      <div class="w-8 h-8 border-2 border-gray-700 border-t-orange-400 rounded-full animate-spin"></div>
    </div>
  </div>

  <!-- Collection list -->
  <div v-else>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold">Sammlungen</h2>
      <button @click="showCreate = true"
        class="flex items-center gap-2 bg-orange-500 hover:bg-orange-400 px-4 py-2 rounded-lg text-sm font-medium">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Neue Sammlung
      </button>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" @click.self="showCreate = false">
      <div class="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md p-6">
        <h3 class="font-semibold mb-4">Neue Sammlung</h3>
        <input v-model="newName" type="text" placeholder="Name der Sammlung"
          class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:border-orange-400"
          @keydown.enter="doCreate" />
        <textarea v-model="newDesc" rows="3" placeholder="Beschreibung (optional)"
          class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:border-orange-400 resize-none" />
        <div class="flex gap-3 justify-end">
          <button @click="showCreate = false" class="text-sm text-gray-400 hover:text-white px-4 py-2">Abbrechen</button>
          <button @click="doCreate" :disabled="!newName.trim()"
            class="bg-orange-500 hover:bg-orange-400 disabled:opacity-40 text-sm px-4 py-2 rounded-lg font-medium">
            Erstellen
          </button>
        </div>
      </div>
    </div>

    <div v-if="collections.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="col in collections" :key="col.id"
        @click="openCollection(col.id)"
        class="bg-gray-900 border border-gray-800 hover:border-orange-500/50 rounded-xl p-4 cursor-pointer transition-colors">
        <!-- Preview images -->
        <div class="grid grid-cols-2 gap-1 mb-3 aspect-video rounded-lg overflow-hidden bg-gray-800">
          <template v-if="col.previews?.length">
            <img v-for="(url, i) in col.previews.slice(0, 4)" :key="i" :src="url"
              class="w-full h-full object-cover" :class="col.previews.length === 1 ? 'col-span-2 row-span-2' : ''" />
          </template>
          <div v-else class="col-span-2 flex items-center justify-center text-gray-700">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
          </div>
        </div>
        <h3 class="font-medium truncate">{{ col.name }}</h3>
        <p v-if="col.description" class="text-sm text-gray-500 truncate mt-0.5">{{ col.description }}</p>
        <p class="text-xs text-gray-600 mt-1">{{ col.model_count }} Modell{{ col.model_count !== 1 ? 'e' : '' }}</p>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-24 text-center">
      <p class="text-gray-500">Noch keine Sammlungen.</p>
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
            <button @click="closeDetail"
                    class="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center
                           bg-gray-800 hover:bg-gray-700 rounded-full text-gray-400 hover:text-white transition-colors text-lg leading-none"
                    title="Schliessen (ESC)">
              ×
            </button>
            <div class="p-5 sm:p-8">
              <ModelDetailView :model-id="detailId"
                @back="closeDetail"
                @deleted="onDeleted" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { listCollections, createCollection, getCollection, updateCollection, deleteCollection } from '../api.js'
import ModelCard from '../components/ModelCard.vue'
import ModelDetailView from './ModelDetailView.vue'

const collections = ref([])
const activeColId = ref(null)
const activeColData = ref(null)
const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')
const editingCol = ref(false)
const editName = ref('')
const editDesc = ref('')
const confirmDeleteCol = ref(false)
const detailId = ref(null)

const activeCol = computed(() => activeColData.value)

onMounted(() => {
  load()
  document.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

watch(detailId, (id) => {
  document.body.style.overflow = id ? 'hidden' : ''
})

function onKeydown(e) {
  if (e.key === 'Escape' && detailId.value) closeDetail()
}

function openDetail(id) {
  detailId.value = id
}

function closeDetail() {
  detailId.value = null
}

async function load() {
  collections.value = await listCollections()
}

async function openCollection(id) {
  activeColId.value = id
  activeColData.value = await getCollection(id)
  editName.value = activeColData.value.name
  editDesc.value = activeColData.value.description || ''
}

async function doCreate() {
  if (!newName.value.trim()) return
  const col = await createCollection(newName.value.trim(), newDesc.value.trim())
  collections.value.push({ ...col, previews: [] })
  newName.value = ''
  newDesc.value = ''
  showCreate.value = false
}

async function saveEdit() {
  await updateCollection(activeColId.value, editName.value, editDesc.value)
  activeColData.value.name = editName.value
  activeColData.value.description = editDesc.value
  const col = collections.value.find(c => c.id === activeColId.value)
  if (col) { col.name = editName.value; col.description = editDesc.value }
  editingCol.value = false
}

async function doDeleteCol() {
  await deleteCollection(activeColId.value)
  collections.value = collections.value.filter(c => c.id !== activeColId.value)
  activeColId.value = null
  activeColData.value = null
  confirmDeleteCol.value = false
}

function onDeleted() {
  closeDetail()
  if (activeColId.value) openCollection(activeColId.value)
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>
