<template>
  <div
    class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden cursor-pointer hover:border-orange-400/60 hover:shadow-lg hover:shadow-orange-900/20 transition-all group"
    @click="$emit('click', model)"
  >
    <div class="aspect-[4/3] bg-gray-800 relative overflow-hidden">
      <img
        v-if="model.preview_image"
        :src="model.preview_image"
        :alt="model.title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-600">
        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M20 7l-8-4-8 4m16 0v10l-8 4m-8-4V7m8 4v10" />
        </svg>
      </div>
      <span class="absolute top-2 right-2 bg-black/60 text-xs px-2 py-0.5 rounded-full text-gray-300">
        {{ platformLabel }}
      </span>
    </div>

    <div class="p-3">
      <h3 class="font-medium text-sm leading-tight line-clamp-2 group-hover:text-orange-300 transition-colors">
        {{ model.title }}
      </h3>
      <p v-if="model.author" class="text-xs text-gray-500 mt-1 truncate">{{ model.author }}</p>
      <div class="flex flex-wrap gap-1 mt-2">
        <span
          v-for="tag in model.tags.slice(0, 3)"
          :key="tag"
          class="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded hover:bg-orange-500/20 hover:text-orange-300 transition-colors"
          @click.stop="$emit('tag-click', tag)"
        >{{ tag }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ model: Object })
defineEmits(['click', 'tag-click'])

const platformLabel = computed(() => {
  const map = { printables: 'Printables', thingiverse: 'Thingiverse', makerworld: 'MakerWorld', cults3d: 'Cults3d' }
  return map[props.model.source_platform] || props.model.source_platform || '?'
})
</script>
