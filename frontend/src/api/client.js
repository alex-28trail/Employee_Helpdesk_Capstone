import axios from 'axios'

// Backend URL comes from frontend/.env (VITE_API_URL); defaults to the local FastAPI server.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 90000, // AI analysis on a laptop CPU can take a while
})

// ---- Tickets ----
export const listTickets = (params = {}) => {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  return api.get('/api/tickets', { params: clean }).then((r) => r.data)
}
export const getTicket = (id) => api.get(`/api/tickets/${id}`).then((r) => r.data)
export const createTicket = (data) => api.post('/api/tickets', data).then((r) => r.data)
export const updateTicket = (id, data) => api.patch(`/api/tickets/${id}`, data).then((r) => r.data)
export const getHistory = (id) => api.get(`/api/tickets/${id}/history`).then((r) => r.data)

// ---- Workflow ----
export const changeStatus = (id, status, note) =>
  api.patch(`/api/tickets/${id}/status`, { status, note: note || null }).then((r) => r.data)
export const addComment = (id, comment, author = 'Support Staff') =>
  api.post(`/api/tickets/${id}/comments`, { comment, author }).then((r) => r.data)

// ---- AI ----
export const runAnalysis = (id) => api.post(`/api/tickets/${id}/ai-analysis`).then((r) => r.data)
export const getSuggestions = (id) => api.get(`/api/tickets/${id}/ai-suggestions`).then((r) => r.data)
export const sendFeedback = (suggestionId, data) =>
  api.post(`/api/ai-suggestions/${suggestionId}/feedback`, data).then((r) => r.data)

// ---- Misc ----
export const getSummary = () => api.get('/api/dashboard/summary').then((r) => r.data)
export const getRequesters = () => api.get('/api/requesters').then((r) => r.data)
export const getHealth = () => api.get('/health').then((r) => r.data)

/** One human-readable message for any API error (FastAPI sends {"detail": ...}). */
export function errorMessage(err) {
  if (!err?.response) {
    if (err?.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
    return `Cannot reach the backend at ${api.defaults.baseURL}. Is the FastAPI server running?`
  }
  const detail = err.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join('; ')
  return `Request failed (HTTP ${err.response.status}).`
}

/** FastAPI 422 errors as { fieldName: message } so forms can show them beside each field. */
export function fieldErrors(err) {
  const detail = err?.response?.data?.detail
  if (err?.response?.status !== 422 || !Array.isArray(detail)) return {}
  const out = {}
  for (const d of detail) {
    const field = d.loc?.at(-1)
    if (field && !out[field]) out[field] = d.msg.replace(/^Value error, /, '')
  }
  return out
}
