import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

api.interceptors.response.use(null, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('is_admin')
    window.location.reload()
  }
  return Promise.reject(err)
})

// Models
export async function importModel(url) {
  const r = await api.post('/models/import', { url })
  return r.data
}
export async function pollJob(jobId) {
  const r = await api.get(`/models/jobs/${jobId}`)
  return r.data
}
export async function listModels(params = {}) {
  const r = await api.get('/models', { params })
  return r.data
}
export async function getModel(id) {
  const r = await api.get(`/models/${id}`)
  return r.data
}
export async function deleteModel(id) {
  await api.delete(`/models/${id}`)
}
export async function setModelTags(modelId, tags) {
  await api.patch(`/models/${modelId}/tags`, { tags })
}
export async function setModelNotes(modelId, notes) {
  await api.patch(`/models/${modelId}/notes`, { notes })
}

// Tags
export async function listTags() {
  const r = await api.get('/tags')
  return r.data
}

// Collections
export async function listCollections() {
  const r = await api.get('/collections')
  return r.data
}
export async function createCollection(name, description = '') {
  const r = await api.post('/collections', { name, description })
  return r.data
}
export async function getCollection(id) {
  const r = await api.get(`/collections/${id}`)
  return r.data
}
export async function updateCollection(id, name, description) {
  await api.patch(`/collections/${id}`, { name, description })
}
export async function deleteCollection(id) {
  await api.delete(`/collections/${id}`)
}
export async function addModelToCollection(colId, modelId) {
  await api.post(`/collections/${colId}/models/${modelId}`)
}
export async function removeModelFromCollection(colId, modelId) {
  await api.delete(`/collections/${colId}/models/${modelId}`)
}
