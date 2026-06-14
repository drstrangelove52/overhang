<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85" @click.self="$emit('close')">
    <div class="relative w-full max-w-4xl bg-gray-950 rounded-2xl overflow-hidden"
         style="height: min(80vh, 700px);">

      <!-- Header -->
      <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3
                  bg-gradient-to-b from-black/60 to-transparent pointer-events-none">
        <span class="text-sm text-gray-300 font-mono">{{ filename }}</span>
        <button class="pointer-events-auto text-gray-400 hover:text-white w-8 h-8 flex items-center justify-center
                       bg-black/40 rounded-full transition-colors"
                @click="$emit('close')">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Canvas -->
      <canvas ref="canvas" class="w-full h-full block" />

      <!-- Loading -->
      <div v-if="state === 'loading'"
           class="absolute inset-0 flex flex-col items-center justify-center gap-3 text-gray-400">
        <div class="w-8 h-8 border-2 border-gray-600 border-t-orange-400 rounded-full animate-spin"></div>
        <span class="text-sm">Lade Modell…</span>
      </div>

      <!-- Error -->
      <div v-if="state === 'error'"
           class="absolute inset-0 flex flex-col items-center justify-center gap-2 text-gray-500">
        <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        </svg>
        <span class="text-sm">{{ errorMsg }}</span>
      </div>

      <!-- Controls hint -->
      <div v-if="state === 'ready'"
           class="absolute bottom-3 left-1/2 -translate-x-1/2 text-xs text-gray-600 pointer-events-none select-none">
        Ziehen = Drehen &nbsp;·&nbsp; Scrollen = Zoom &nbsp;·&nbsp; Rechtsklick = Verschieben
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'

const props = defineProps({
  url: { type: String, required: true },
  filename: { type: String, required: true },
})
defineEmits(['close'])

const canvas = ref(null)
const state = ref('loading')
const errorMsg = ref('')

let renderer, scene, camera, controls, animFrameId, resizeObs

onMounted(async () => {
  const ext = props.filename.split('.').pop().toLowerCase()
  if (!['stl', '3mf', 'obj'].includes(ext)) {
    errorMsg.value = `Vorschau für .${ext} nicht verfügbar`
    state.value = 'error'
    return
  }

  const w = canvas.value.clientWidth
  const h = canvas.value.clientHeight

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(w, h)
  renderer.outputColorSpace = THREE.SRGBColorSpace

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0d1117)

  // Grid floor
  const grid = new THREE.GridHelper(300, 30, 0x222222, 0x1a1a1a)
  scene.add(grid)

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dir1 = new THREE.DirectionalLight(0xffffff, 1.2)
  dir1.position.set(1, 2, 1.5)
  scene.add(dir1)
  const dir2 = new THREE.DirectionalLight(0x8888ff, 0.4)
  dir2.position.set(-1, -1, -1)
  scene.add(dir2)

  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 10000)
  camera.position.set(0, 50, 150)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.minDistance = 1
  controls.maxDistance = 5000

  try {
    const object = await loadModel(ext, props.url)
    scene.add(object)

    // Center + fit camera
    const box = new THREE.Box3().setFromObject(object)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())
    object.position.sub(center)
    grid.position.y = -size.y / 2

    const maxDim = Math.max(size.x, size.y, size.z)
    camera.near = maxDim * 0.001
    camera.far = maxDim * 100
    camera.position.set(maxDim * 1.2, maxDim * 0.8, maxDim * 1.5)
    camera.updateProjectionMatrix()
    controls.target.set(0, 0, 0)
    controls.update()

    state.value = 'ready'
  } catch (e) {
    errorMsg.value = `Fehler beim Laden: ${e.message || 'Unbekannter Fehler'}`
    state.value = 'error'
    return
  }

  // Resize
  resizeObs = new ResizeObserver(() => {
    const w = canvas.value?.clientWidth
    const h = canvas.value?.clientHeight
    if (!w || !h) return
    renderer.setSize(w, h)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
  })
  resizeObs.observe(canvas.value.parentElement)

  // Animate
  const animate = () => {
    animFrameId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animFrameId)
  resizeObs?.disconnect()
  renderer?.dispose()
})

async function loadModel(ext, url) {
  if (ext === 'stl') {
    const loader = new STLLoader()
    const geometry = await new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject)
    })
    const mat = new THREE.MeshStandardMaterial({ color: 0xf97316, roughness: 0.6, metalness: 0.1 })
    return new THREE.Mesh(geometry, mat)
  }

  if (ext === 'obj') {
    const loader = new OBJLoader()
    const group = await new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject)
    })
    const mat = new THREE.MeshStandardMaterial({ color: 0xf97316, roughness: 0.6, metalness: 0.1 })
    group.traverse(child => {
      if (child.isMesh) child.material = mat
    })
    return group
  }

  if (ext === '3mf') {
    // ThreeMFLoader is loaded dynamically to avoid bundling issues
    const { ThreeMFLoader } = await import('three/examples/jsm/loaders/3MFLoader.js')
    const loader = new ThreeMFLoader()
    const group = await new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject)
    })
    return group
  }

  throw new Error(`Nicht unterstütztes Format: .${ext}`)
}
</script>
