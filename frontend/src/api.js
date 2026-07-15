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

// File upload / delete
export async function setPrimaryImage(modelId, fileId) {
  await api.patch(`/models/${modelId}/files/${fileId}/primary`)
}
export async function deleteFiles(modelId, fileIds) {
  await api.delete(`/models/${modelId}/files`, { data: { file_ids: fileIds } })
}
export async function uploadFile(modelId, file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post(`/models/${modelId}/files`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  })
  return r.data
}

// Credentials (Thingiverse only)
export async function saveCredential(_platform, _username, token) {
  await api.put('/credentials/thingiverse', { token })
}
export async function deleteCredential(_platform) {
  await api.delete('/credentials/thingiverse')
}
export async function testCredential(_platform) {
  const r = await api.post('/credentials/thingiverse/test')
  return r.data
}

// Auth
export async function changePassword(currentPassword, newPassword) {
  await api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword })
}

// Admin
export async function adminListUsers() {
  const r = await api.get('/admin/users')
  return r.data
}
export async function adminCreateUser(data) {
  const r = await api.post('/admin/users', data)
  return r.data
}
export async function adminUpdateUser(id, data) {
  const r = await api.patch(`/admin/users/${id}`, data)
  return r.data
}
export async function adminDeleteUser(id) {
  await api.delete(`/admin/users/${id}`)
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
