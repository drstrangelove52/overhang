import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

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
