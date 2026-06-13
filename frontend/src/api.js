import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Inject Bearer token from the default axios headers (set by auth store)
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

// On 401, clear auth and reload to show login
api.interceptors.response.use(null, err => {
  if (err.response?.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('is_admin')
    window.location.reload()
  }
  return Promise.reject(err)
})

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
