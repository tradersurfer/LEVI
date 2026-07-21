const API_ROOT = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const DASHBOARD_ROUTES = [
  'summary', 'positions', 'trades', 'evidence', 'decisions', 'alerts', 'setup-status',
]

export async function fetchDashboard(userId, fetcher = fetch) {
  if (!userId || !/^[A-Za-z0-9_-]+$/.test(userId)) throw new Error('A path-safe user ID is required')
  const entries = await Promise.all(DASHBOARD_ROUTES.map(async route => {
    const response = await fetcher(`${API_ROOT}/api/dashboard/${route}?user_id=${encodeURIComponent(userId)}`)
    if (!response.ok) throw new Error(`Dashboard request failed: ${route}`)
    return [route.replace('-', '_'), await response.json()]
  }))
  return Object.fromEntries(entries)
}
