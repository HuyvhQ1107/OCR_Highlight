const API_BASE = '/api/v1'

export function getToken(): string | null {
  return localStorage.getItem('dvtt_token')
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem('dvtt_token', token)
  } else {
    localStorage.removeItem('dvtt_token')
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers || {})

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 204) {
    return undefined as T
  }

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      typeof data?.detail === 'string'
        ? data.detail
        : `Lỗi máy chủ (${res.status})`
    throw new Error(message)
  }

  return data as T
}
