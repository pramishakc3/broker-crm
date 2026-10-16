const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch { /* keep statusText */ }
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  dashboard: () => request('/dashboard'),
  listClients: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()
    return request(`/clients${qs ? `?${qs}` : ''}`)
  },
  getClient: (id) => request(`/clients/${id}`),
  createClient: (data) => request('/clients', { method: 'POST', body: JSON.stringify(data) }),
  updateClient: (id, data) => request(`/clients/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteClient: (id) => request(`/clients/${id}`, { method: 'DELETE' }),
  addNote: (id, body) => request(`/clients/${id}/notes`, { method: 'POST', body: JSON.stringify({ body }) }),
  addTask: (id, data) => request(`/clients/${id}/tasks`, { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (taskId, data) => request(`/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  aiSummary: (id) => request(`/clients/${id}/ai-summary`, { method: 'POST' }),
}

export const STAGES = ['lead', 'contacted', 'application', 'approved', 'settled', 'lost']
export const LOAN_TYPES = ['home_loan', 'refinance', 'investment', 'car_lease', 'equipment_finance', 'personal_loan']
export const label = (s) => s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const money = (n) =>
  Number(n || 0).toLocaleString('en-AU', { style: 'currency', currency: 'AUD', maximumFractionDigits: 0 })
