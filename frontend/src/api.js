const configuredApiBaseUrl =
  typeof import.meta.env !== 'undefined' ? import.meta.env.VITE_API_BASE_URL : ''

export function createApiUrl(path, baseUrl = '') {
  const base = baseUrl.trim().replace(/\/+$/, '')
  const route = path.startsWith('/') ? path : `/${path}`
  return `${base}${route}`
}

export const apiUrl = (path) => createApiUrl(path, configuredApiBaseUrl || '')
