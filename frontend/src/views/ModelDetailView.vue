<template>
  <div v-if="model" class="max-w-5xl mx-auto">
    <button @click="$emit('back')" class="flex items-center gap-2 text-gray-400 hover:text-white mb-6 text-sm">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
      </svg>
      Zurück
    </button>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Image gallery -->
      <div>
        <div class="aspect-[4/3] bg-gray-800 rounded-xl overflow-hidden">
          <img v-if="activeImage" :src="activeImage" :alt="model.title" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-600">
            <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M20 7l-8-4-8 4m16 0v10l-8 4m-8-4V7m8 4v10"/>
            </svg>
          </div>
        </div>
        <div v-if="images.length > 1" class="flex gap-2 mt-2 overflow-x-auto pb-1">
          <div v-for="img in images" :key="img.id"
            class="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden cursor-pointer border-2 transition-colors"
            :class="activeImage === img.url ? 'border-orange-400' : 'border-transparent'"
            @click="activeImage = img.url">
            <img :src="img.url" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>

      <!-- Metadata -->
      <div>
        <div class="flex items-start justify-between gap-3">
          <h1 class="text-xl font-bold leading-tight">{{ model.title }}</h1>
          <span class="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full flex-shrink-0">{{ platformLabel }}</span>
        </div>

        <div class="mt-3 space-y-2 text-sm">
          <div v-if="model.author" class="flex gap-2">
            <span class="text-gray-500 w-20 flex-shrink-0">Autor</span>
            <a v-if="model.author_url" :href="model.author_url" target="_blank"
               class="text-orange-400 hover:underline truncate">{{ model.author }}</a>
            <span v-else>{{ model.author }}</span>
          </div>
          <div v-if="model.license" class="flex gap-2">
            <span class="text-gray-500 w-20 flex-shrink-0">Lizenz</span>
            <span class="text-gray-300">{{ model.license }}</span>
          </div>
          <div v-if="model.source_url" class="flex gap-2">
            <span class="text-gray-500 w-20 flex-shrink-0">Quelle</span>
            <a :href="model.source_url" target="_blank" class="text-orange-400 hover:underline truncate">
              Original ansehen ↗
            </a>
          </div>
        </div>

        <!-- Tags -->
        <div class="mt-4">
          <div class="flex flex-wrap gap-1.5 items-center">
            <span v-for="tag in editTags" :key="tag"
              class="flex items-center gap-1 text-xs bg-gray-800 text-gray-300 pl-2 pr-1 py-1 rounded-full">
              {{ tag }}
              <button @click="removeTag(tag)" class="text-gray-500 hover:text-red-400 leading-none">×</button>
            </span>
            <div v-if="addingTag" class="flex items-center gap-1">
              <input ref="tagInput" v-model="newTagText" type="text" placeholder="Tag…"
                class="bg-gray-800 border border-orange-400 rounded-full px-2 py-0.5 text-xs w-24 focus:outline-none"
                @keydown.enter="confirmTag" @keydown.escape="addingTag = false" @blur="confirmTag" />
            </div>
            <button v-else @click="startAddTag"
              class="text-xs text-gray-500 hover:text-orange-400 border border-dashed border-gray-700 hover:border-orange-400 px-2 py-0.5 rounded-full transition-colors">
              + Tag
            </button>
          </div>
        </div>

        <!-- Collections -->
        <div class="mt-4">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-xs text-gray-500">Sammlungen</span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="col in modelCollections" :key="col.id"
              class="flex items-center gap-1 text-xs bg-indigo-900/50 text-indigo-300 border border-indigo-700/50 pl-2 pr-1 py-1 rounded-full">
              {{ col.name }}
              <button @click="removeFromCollection(col.id)" class="text-indigo-500 hover:text-red-400 leading-none">×</button>
            </span>
            <div class="relative" ref="colDropdown">
              <button @click="colPickerOpen = !colPickerOpen"
                class="text-xs text-gray-500 hover:text-indigo-400 border border-dashed border-gray-700 hover:border-indigo-500 px-2 py-0.5 rounded-full transition-colors">
                + Sammlung
              </button>
              <div v-if="colPickerOpen"
                class="absolute top-7 left-0 z-20 bg-gray-900 border border-gray-700 rounded-xl shadow-xl py-1 min-w-48">
                <div v-if="availableCollections.length === 0" class="px-3 py-2 text-xs text-gray-500">
                  Keine Sammlungen vorhanden
                </div>
                <button v-for="col in availableCollections" :key="col.id"
                  @click="addToCollection(col.id)"
                  class="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-800 text-gray-300">
                  {{ col.name }}
                </button>
                <div class="border-t border-gray-800 mt-1 pt-1">
                  <button @click="createAndAdd" class="w-full text-left px-3 py-1.5 text-sm text-orange-400 hover:bg-gray-800">
                    + Neue Sammlung…
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="mt-4">
          <div class="flex items-center justify-between mb-1">
            <span class="text-xs text-gray-500">Notizen</span>
            <span v-if="notesSaved" class="text-xs text-green-500">Gespeichert</span>
          </div>
          <textarea v-model="notesText" rows="3" placeholder="Eigene Notizen zum Modell…"
            class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-orange-400 resize-none"
            @blur="saveNotes" />
        </div>

        <!-- Files -->
        <div class="mt-4">
          <h3 class="text-sm font-medium text-gray-400 mb-2">Dateien</h3>
          <div v-if="printFiles.length" class="space-y-2">
            <div v-for="f in printFiles" :key="f.id"
              class="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-xs font-mono text-orange-400 uppercase">{{ f.file_type }}</span>
                <span class="text-sm truncate">{{ f.filename }}</span>
                <span v-if="f.file_size" class="text-xs text-gray-500 flex-shrink-0">{{ formatSize(f.file_size) }}</span>
              </div>
              <a :href="f.url" download class="ml-2 text-gray-400 hover:text-white flex-shrink-0">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
              </a>
            </div>
          </div>
          <p v-else class="text-sm text-gray-600">
            Keine Dateien lokal —
            <a :href="model.source_url" target="_blank" class="text-orange-400 hover:underline">
              auf {{ platformLabel }} herunterladen ↗
            </a>
          </p>
        </div>

        <!-- File drop zone -->
        <div class="mt-4">
          <div
            @dragover.prevent="dropActive = true"
            @dragleave="dropActive = false"
            @drop.prevent="onDrop"
            class="border-2 border-dashed rounded-xl px-4 py-5 text-center text-sm transition-colors cursor-pointer"
            :class="dropActive ? 'border-orange-400 bg-orange-500/10 text-orange-300' : 'border-gray-700 text-gray-600 hover:border-gray-600'"
            @click="$refs.fileInput.click()"
          >
            <span v-if="uploading">Lädt hoch…</span>
            <span v-else>STL / 3MF / ZIP hier ablegen oder klicken</span>
          </div>
          <input ref="fileInput" type="file" multiple accept=".stl,.3mf,.zip" class="hidden" @change="onFileInput" />
          <p v-if="uploadError" class="text-red-400 text-xs mt-1">{{ uploadError }}</p>
        </div>

        <!-- Delete -->
        <div class="mt-6 pt-4 border-t border-gray-800">
          <button v-if="!confirmDelete" @click="confirmDelete = true" class="text-sm text-red-500 hover:text-red-400">
            Modell löschen
          </button>
          <div v-else class="flex items-center gap-3">
            <span class="text-sm text-gray-400">Wirklich löschen?</span>
            <button @click="doDelete" class="text-sm text-red-500 hover:text-red-400 font-medium">Ja, löschen</button>
            <button @click="confirmDelete = false" class="text-sm text-gray-500 hover:text-white">Abbrechen</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Description -->
    <div v-if="model.description" class="mt-8">
      <h3 class="text-sm font-medium text-gray-400 mb-3">Beschreibung</h3>
      <div class="prose prose-invert prose-sm max-w-none text-gray-300 bg-gray-900 rounded-xl p-4 border border-gray-800"
        v-html="model.description" />
    </div>
  </div>

  <div v-else class="flex items-center justify-center h-64">
    <div class="w-8 h-8 border-2 border-gray-600 border-t-orange-400 rounded-full animate-spin"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import {
  getModel, deleteModel, setModelTags, setModelNotes, uploadFile,
  listCollections, addModelToCollection, removeModelFromCollection, createCollection
} from '../api.js'

const props = defineProps({ modelId: Number })
const emit = defineEmits(['back', 'deleted'])

const model = ref(null)
const activeImage = ref(null)
const confirmDelete = ref(false)

// Tags
const editTags = ref([])
const addingTag = ref(false)
const newTagText = ref('')
const tagInput = ref(null)

// Collections
const allCollections = ref([])
const modelCollections = ref([])
const colPickerOpen = ref(false)
const colDropdown = ref(null)
const notesSaved = ref(false)
const notesText = ref('')
const dropActive = ref(false)
const uploading = ref(false)
const uploadError = ref('')

onMounted(async () => {
  model.value = await getModel(props.modelId)
  const primary = model.value.files?.find(f => f.is_primary_preview)
  activeImage.value = primary?.url || images.value[0]?.url || null
  editTags.value = [...(model.value.tags || [])]
  notesText.value = model.value.notes || ''
  allCollections.value = await listCollections()
  refreshModelCollections()
  document.addEventListener('click', onOutsideClick)
})

onBeforeUnmount(() => document.removeEventListener('click', onOutsideClick))

function onOutsideClick(e) {
  if (colDropdown.value && !colDropdown.value.contains(e.target)) colPickerOpen.value = false
}

function refreshModelCollections() {
  modelCollections.value = allCollections.value.filter(c =>
    c.models?.some(m => m.id === props.modelId) ||
    // fallback: re-check after add/remove via reload
    false
  )
}

const images = computed(() => (model.value?.files || []).filter(f => f.file_type === 'image'))
const printFiles = computed(() => (model.value?.files || []).filter(f => f.file_type !== 'image'))
const platformLabel = computed(() => {
  const map = { printables: 'Printables', thingiverse: 'Thingiverse', makerworld: 'MakerWorld' }
  return map[model.value?.source_platform] || model.value?.source_platform || '?'
})
const availableCollections = computed(() =>
  allCollections.value.filter(c => !modelCollections.value.find(mc => mc.id === c.id))
)

// Tags
async function startAddTag() {
  addingTag.value = true
  await nextTick()
  tagInput.value?.focus()
}
async function confirmTag() {
  const t = newTagText.value.trim().toLowerCase()
  if (t && !editTags.value.includes(t)) {
    editTags.value.push(t)
    await setModelTags(props.modelId, editTags.value)
  }
  newTagText.value = ''
  addingTag.value = false
}
async function removeTag(tag) {
  editTags.value = editTags.value.filter(t => t !== tag)
  await setModelTags(props.modelId, editTags.value)
}

// Collections
async function addToCollection(colId) {
  await addModelToCollection(colId, props.modelId)
  allCollections.value = await listCollections()
  const col = allCollections.value.find(c => c.id === colId)
  if (col && !modelCollections.value.find(c => c.id === colId)) {
    modelCollections.value.push(col)
  }
  colPickerOpen.value = false
}
async function removeFromCollection(colId) {
  await removeModelFromCollection(colId, props.modelId)
  modelCollections.value = modelCollections.value.filter(c => c.id !== colId)
}
async function createAndAdd() {
  const name = prompt('Name der neuen Sammlung:')
  if (!name?.trim()) return
  const col = await createCollection(name.trim())
  allCollections.value.push(col)
  await addToCollection(col.id)
}

// Notes
async function saveNotes() {
  await setModelNotes(props.modelId, notesText.value)
  notesSaved.value = true
  setTimeout(() => { notesSaved.value = false }, 2000)
}

function formatSize(bytes) {
  if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(0) + ' KB'
}

async function onDrop(e) {
  dropActive.value = false
  await uploadFiles(Array.from(e.dataTransfer.files))
}
async function onFileInput(e) {
  await uploadFiles(Array.from(e.target.files))
  e.target.value = ''
}
async function uploadFiles(files) {
  uploading.value = true
  uploadError.value = ''
  for (const file of files) {
    try {
      const result = await uploadFile(props.modelId, file)
      // ZIP response: { extracted, files: [...] }
      if (result.extracted !== undefined) {
        for (const mf of result.files) {
          model.value.files.push({ ...mf, is_primary_preview: false })
        }
        if (result.extracted === 0) {
          uploadError.value = `${file.name}: Keine unterstützten Dateien in ZIP gefunden`
        }
      } else {
        model.value.files.push({ ...result, is_primary_preview: false })
      }
    } catch (e) {
      uploadError.value = e.response?.data?.detail || `Upload fehlgeschlagen: ${file.name}`
    }
  }
  uploading.value = false
}

async function doDelete() {
  await deleteModel(props.modelId)
  emit('deleted')
}
</script>
