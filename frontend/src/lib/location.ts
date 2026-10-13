import { useEffect, useState } from 'react'
import type { View } from './types'
export function useLocationState() {
  const [search, setSearch] = useState(() => window.location.search)
  useEffect(() => {
    const pop = () => setSearch(window.location.search)
    window.addEventListener('popstate', pop)
    return () => window.removeEventListener('popstate', pop)
  }, [])
  const params = new URLSearchParams(search)
  const candidate = params.get('view') || 'overview'
  const view = (
    ['overview', 'analysis', 'ledger', 'data'].includes(candidate) ? candidate : 'overview'
  ) as View
  function update(patch: Record<string, string | null>, replace = false) {
    const next = new URLSearchParams(window.location.search)
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    const query = next.toString()
    window.history[replace ? 'replaceState' : 'pushState'](
      null,
      '',
      `${window.location.pathname}${query ? '?' + query : ''}`,
    )
    setSearch(window.location.search)
  }
  return { view, month: params.get('month') || '', params, update }
}
