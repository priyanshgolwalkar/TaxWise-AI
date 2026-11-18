const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

type AuthPayload = { email: string; password: string; name?: string }
type TokenResponse = { access_token: string; token_type: string }

function handleUnauthorized(path: string, status: number) {
  if (status === 401 && !path.startsWith('/auth/')) {
    localStorage.removeItem('taxwise_access_token')
    window.location.assign('/login')
  }
}

async function parseResponse(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch (error) {
    if (error instanceof SyntaxError) return null
    throw error
  }
}

function responseError(body: unknown, fallback: string) {
  if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') {
    return body.detail
  }
  return fallback
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
  })
  const body = await parseResponse(response)
  handleUnauthorized(path, response.status)
  if (!response.ok) throw new Error(responseError(body, 'Something went wrong. Please try again.'))
  if (body === null) throw new Error('The server returned an invalid response.')
  return body as T
}

export function authenticate(payload: AuthPayload, register: boolean): Promise<TokenResponse> {
  return request<TokenResponse>(register ? '/auth/register' : '/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getProfile() { return request<{ id: number; name: string; email: string }>('/profile/me', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }

export function saveToken(token: string) { localStorage.setItem('taxwise_access_token', token) }
export function getToken() { return localStorage.getItem('taxwise_access_token') }

export function getLatestRecommendations() { return request<any>('/recommendations/latest', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }

export type TaxInput = {
  assessment_year: string
  annual_income: number
  deductions_80c: number
  deductions_80d: number
  home_loan_interest: number
  hra_exemption: number
}

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`${API_URL}/documents/upload`, { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` }, body: form })
  const body = await parseResponse(response)
  handleUnauthorized('/documents/upload', response.status)
  if (!response.ok) throw new Error(responseError(body, 'Document upload failed'))
  if (body === null) throw new Error('The server returned an invalid response.')
  return body
}

export function listDocuments() { return request<unknown[]>('/documents', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function compareTax(payload: TaxInput) { return request('/tax/compare', { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` }, body: JSON.stringify(payload) }) }
export function getDashboardSummary() { return request<any>('/dashboard/', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function getLatestTax() { return request<any>('/tax/latest', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function createRecommendations(payload: TaxInput & { regime: string; tax_result?: object }) { return request<any>('/recommendations/', { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` }, body: JSON.stringify(payload) }) }
export function getLatestReport() { return request<any>('/reports/latest', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function createReport() { return request<any>('/reports/', { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function listReports() { return request<any[]>('/reports/', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function getReport(id: number) { return request<any>(`/reports/${id}`, { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function listAssistantConversations() { return request<any[]>('/assistant/conversations', { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function createAssistantConversation() { return request<any>('/assistant/conversations', { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function getAssistantMessages(id: string) { return request<any[]>(`/assistant/conversations/${id}/messages`, { headers: { Authorization: `Bearer ${getToken() || ''}` } }) }
export function sendAssistantMessage(message: string, conversationId?: string) { return request<{answer:string;conversation_id:string;sources:any[]}>('/assistant/chat', { method: 'POST', headers: { Authorization: `Bearer ${getToken() || ''}` }, body: JSON.stringify({ message, conversation_id: conversationId }) }) }
