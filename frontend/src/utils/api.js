import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unexpected error occurred.'
    return Promise.reject(new Error(msg))
  }
)

export const generateCaption = async (imageFile, beamSize = 3) => {
  const formData = new FormData()
  formData.append('file', imageFile)
  const res = await api.post(`/api/v1/generate-caption?beam_size=${beamSize}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const healthCheck = async () => {
  const res = await api.get('/api/v1/health')
  return res.data
}

export const getConfig = async () => {
  const res = await api.get('/api/v1/config')
  return res.data
}

export default api
