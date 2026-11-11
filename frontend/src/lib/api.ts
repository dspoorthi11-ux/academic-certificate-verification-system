import axios from 'axios'

export const tokenKey = 'certichain-access-token'
export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'
export const apiOrigin = new URL(apiBaseUrl).origin

const api = axios.create({
  baseURL: apiBaseUrl,
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(tokenKey)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export type ApiUser = {
  id: string
  email: string
  full_name: string
  role: 'university' | 'student' | 'verifier' | 'admin'
  is_active: boolean
}

export type ApiVerification = {
  certificate_id: string
  result: string
  message: string
  institution: string | null
  issuer_authentication: string
  document_integrity: string
  blockchain_status: string
  blockchain_reference: string | null
  ai_analysis: {
    analysis_status: string
    role: string
    risk_score: number | null
    fraud_probability: number | null
    risk_category: string
    detected_anomalies: string[]
    explanation: string
    recommended_action: string
  }
  attestation: {
    verification_id: string
    public_url: string
    signature_algorithm: string
    key_id: string
  } | null
}

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    return error.message || 'The service could not complete the request.'
  }
  return 'The service could not complete the request.'
}

export default api
