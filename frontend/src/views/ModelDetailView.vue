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
          <div
            v-for="img in images"
            :key="img.id"
            class="w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden cursor-pointer border-2 transition-colors"
            :class="activeImage === img.url ? 'border-orange-400' : 'border-transparent'"
            @click="activeImage = img.url"
          >
            <img :src="img.url" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>

      <!-- Metadata -->
      <div>
        <div class="flex items-start justify-between gap-3">
          <h1 class="text-xl font-bold leading-tight">{{ model.title }}</h1>
          <span class="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full flex-shrink-0">
            {{ platformLabel }}
          </span>
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
        <div v-if="model.tags?.length" class="flex flex-wrap gap-1.5 mt-4">
          <span v-for="tag in model.tags" :key="tag"
            class="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full">{{ tag }}</span>
        </div>

        <!-- Files -->
        <div class="mt-5">
          <h3 class="text-sm font-medium text-gray-400 mb-2">Dateien</h3>
          <div v-if="printFiles.length" class="space-y-2">
            <div v-for="f in printFiles" :key="f.id"
              class="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-xs font-mono text-orange-400 uppercase">{{ f.file_type }}</span>
                <span class="text-sm truncate">{{ f.filename }}</span>
                <span v-if="f.file_size" class="text-xs text-gray-500 flex-shrink-0">
                  {{ formatSize(f.file_size) }}
                </span>
              </div>
              <a :href="f.url" download class="ml-2 text-gray-400 hover:text-white flex-shrink-0" title="Herunterladen">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
              </a>
            </div>
          </div>
          <p v-else class="text-sm text-gray-600">
            Keine Dateien lokal gespeichert —
            <a :href="model.source_url" target="_blank" class="text-orange-400 hover:underline">
              auf {{ platformLabel }} herunterladen ↗
            </a>
          </p>
        </div>

        <!-- Delete -->
        <div class="mt-6 pt-4 border-t border-gray-800">
          <button v-if="!confirmDelete" @click="confirmDelete = true"
            class="text-sm text-red-500 hover:text-red-400">
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

  <div v-else class="flex items-center justify-center h-64 text-gray-600">
    <div class="w-8 h-8 border-2 border-gray-600 border-t-orange-400 rounded-full animate-spin"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getModel, deleteModel } from '../api.js'

const props = defineProps({ modelId: Number })
const emit = defineEmits(['back', 'deleted'])

const model = ref(null)
const activeImage = ref(null)
const confirmDelete = ref(false)

onMounted(async () => {
  model.value = await getModel(props.modelId)
  const primary = model.value.files?.find(f => f.is_primary_preview)
  activeImage.value = primary?.url || images.value[0]?.url || null
})

const images = computed(() => (model.value?.files || []).filter(f => f.file_type === 'image'))
const printFiles = computed(() => (model.value?.files || []).filter(f => f.file_type !== 'image'))

const platformLabel = computed(() => {
  const map = { printables: 'Printables', thingiverse: 'Thingiverse', makerworld: 'MakerWorld' }
  return map[model.value?.source_platform] || model.value?.source_platform || '?'
})

function formatSize(bytes) {
  if (bytes > 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(0) + ' KB'
}

async function doDelete() {
  await deleteModel(props.modelId)
  emit('deleted')
}
</script>
