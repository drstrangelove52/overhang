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
           class="absolute bottom-3 left-1/2 -translate-x-1/2 text-xs text-gray-600 pointer-events-none select-none whitespace-nowrap">
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

const MAT = () => new THREE.MeshStandardMaterial({ color: 0xf97316, roughness: 0.55, metalness: 0.05 })

let renderer, scene, camera, controls, animFrameId, resizeObs

onMounted(async () => {
  const ext = props.filename.split('.').pop().toLowerCase()
  if (!['stl', '3mf', 'obj'].includes(ext)) {
    errorMsg.value = `Vorschau für .${ext} nicht verfügbar`
    state.value = 'error'
    return
  }

  const w = canvas.value.clientWidth || 800
  const h = canvas.value.clientHeight || 600

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.outputColorSpace = THREE.SRGBColorSpace

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0d1117)

  const grid = new THREE.GridHelper(300, 30, 0x1e2530, 0x161b22)
  scene.add(grid)

  scene.add(new THREE.AmbientLight(0xffffff, 0.7))
  const sun = new THREE.DirectionalLight(0xffffff, 1.4)
  sun.position.set(1, 2, 1.5)
  scene.add(sun)
  const fill = new THREE.DirectionalLight(0x8899cc, 0.35)
  fill.position.set(-1, -0.5, -1)
  scene.add(fill)

  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 10000)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08

  try {
    const object = await loadModel(ext, props.url)
    scene.add(object)
    fitCamera(object)
    state.value = 'ready'
  } catch (e) {
    console.error('3D viewer error:', e)
    errorMsg.value = e.message || 'Unbekannter Fehler'
    state.value = 'error'
    return
  }

  resizeObs = new ResizeObserver(() => {
    const el = canvas.value?.parentElement
    if (!el) return
    const w = el.clientWidth
    const h = el.clientHeight
    renderer.setSize(w, h)
    camera.aspect = w / h
    camera.updateProjectionMatrix()
  })
  resizeObs.observe(canvas.value.parentElement)

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
  controls?.dispose()
  renderer?.dispose()
})

function fitCamera(object) {
  const box = new THREE.Box3().setFromObject(object)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  object.position.sub(center)

  const maxDim = Math.max(size.x, size.y, size.z) || 100
  camera.near = maxDim * 0.001
  camera.far = maxDim * 200
  camera.position.set(maxDim * 1.2, maxDim * 0.9, maxDim * 1.8)
  camera.updateProjectionMatrix()
  controls.target.set(0, 0, 0)
  controls.minDistance = maxDim * 0.05
  controls.maxDistance = maxDim * 20
  controls.update()

  // Lower grid to model bottom
  scene.children
    .filter(c => c.isGridHelper)
    .forEach(g => { g.position.y = -size.y / 2 })
}

async function loadModel(ext, url) {
  if (ext === 'stl') {
    const loader = new STLLoader()
    const geometry = await new Promise((resolve, reject) =>
      loader.load(url, resolve, undefined, e => reject(new Error('STL konnte nicht geladen werden')))
    )
    return new THREE.Mesh(geometry, MAT())
  }

  if (ext === 'obj') {
    const loader = new OBJLoader()
    const group = await new Promise((resolve, reject) =>
      loader.load(url, resolve, undefined, e => reject(new Error('OBJ konnte nicht geladen werden')))
    )
    group.traverse(child => { if (child.isMesh) child.material = MAT() })
    return group
  }

  if (ext === '3mf') {
    return load3MF(url)
  }

  throw new Error(`Format .${ext} nicht unterstützt`)
}

// Custom 3MF parser — bypasses ThreeMFLoader which crashes on files
// containing <object type="other"> (common in Bambu Studio / Printables exports).
// 3MF is a ZIP archive containing a 3D/3dmodel.model XML file.
async function load3MF(url) {
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`HTTP ${resp.status} beim Laden der Datei`)
  const buffer = new Uint8Array(await resp.arrayBuffer())

  const { unzipSync } = await import('three/examples/jsm/libs/fflate.module.js')
  let files
  try {
    files = unzipSync(buffer)
  } catch {
    throw new Error('3MF-Datei ist kein gültiges ZIP-Archiv')
  }

  // Locate the main model file
  let modelBytes = files['3D/3dmodel.model']
  if (!modelBytes) {
    const key = Object.keys(files).find(k => k.endsWith('.model'))
    if (key) modelBytes = files[key]
  }
  if (!modelBytes) throw new Error('Kein 3D-Modell in der 3MF-Datei gefunden')

  const xml = new DOMParser().parseFromString(
    new TextDecoder().decode(modelBytes), 'text/xml'
  )
  if (xml.querySelector('parsererror')) throw new Error('3MF XML konnte nicht geparst werden')

  // Build a vertex lookup from the <resources> section
  const objectMap = {}
  for (const obj of xml.querySelectorAll('resources > object')) {
    const id = obj.getAttribute('id')
    const type = obj.getAttribute('type') || 'model'
    if (type !== 'model') continue
    const meshEl = obj.querySelector('mesh')
    if (!meshEl) continue
    objectMap[id] = meshEl
  }

  // Build THREE meshes
  const group = new THREE.Group()
  const mat = MAT()
  let totalTriangles = 0

  // Process build items — resolve components recursively
  const buildItems = xml.querySelectorAll('build > item')
  const processedIds = new Set()

  function addMeshFromObject(id) {
    if (processedIds.has(id)) return
    processedIds.add(id)

    const meshEl = objectMap[id]
    if (!meshEl) {
      // May be a component referencing other objects
      const objEl = xml.querySelector(`resources > object[id="${id}"]`)
      if (objEl) {
        for (const comp of objEl.querySelectorAll('components > component')) {
          addMeshFromObject(comp.getAttribute('objectid'))
        }
      }
      return
    }

    const vertexEls = meshEl.querySelectorAll('vertices > vertex')
    const triEls = meshEl.querySelectorAll('triangles > triangle')
    if (!vertexEls.length || !triEls.length) return

    const positions = new Float32Array(vertexEls.length * 3)
    for (let i = 0; i < vertexEls.length; i++) {
      positions[i * 3]     = parseFloat(vertexEls[i].getAttribute('x'))
      positions[i * 3 + 1] = parseFloat(vertexEls[i].getAttribute('y'))
      positions[i * 3 + 2] = parseFloat(vertexEls[i].getAttribute('z'))
    }

    const indices = new Uint32Array(triEls.length * 3)
    for (let i = 0; i < triEls.length; i++) {
      indices[i * 3]     = parseInt(triEls[i].getAttribute('v1'))
      indices[i * 3 + 1] = parseInt(triEls[i].getAttribute('v2'))
      indices[i * 3 + 2] = parseInt(triEls[i].getAttribute('v3'))
    }

    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setIndex(new THREE.BufferAttribute(indices, 1))
    geo.computeVertexNormals()
    group.add(new THREE.Mesh(geo, mat))
    totalTriangles += triEls.length
  }

  if (buildItems.length > 0) {
    for (const item of buildItems) {
      addMeshFromObject(item.getAttribute('objectid'))
    }
  } else {
    // No build section — load all mesh objects directly
    for (const id of Object.keys(objectMap)) {
      addMeshFromObject(id)
    }
  }

  if (totalTriangles === 0) throw new Error('Keine Geometrie in der 3MF-Datei gefunden')
  return group
}
</script>
