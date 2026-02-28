import { useState, useEffect, useCallback } from 'react'
import { launchService } from '@/services/launchService'
import type { Launch, LaunchFilters, LaunchStats } from '@/types/launch'

const DEFAULT_FILTERS: LaunchFilters = {
  status: 'all',
  search: '',
  dateFrom: '',
  dateTo: '',
}

export function useLaunches() {
  const [launches, setLaunches] = useState<Launch[]>([])
  const [filtered, setFiltered] = useState<Launch[]>([])
  const [stats, setStats] = useState<LaunchStats>({ total: 0, success: 0, failed: 0, upcoming: 0, successRate: 0 })
  const [filters, setFilters] = useState<LaunchFilters>(DEFAULT_FILTERS)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchLaunches = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await launchService.getAllLaunches()
      setLaunches(data)
      setStats(launchService.computeStats(data))
    } catch (err) {
      setError('Error al cargar los lanzamientos. Verifica la conexión.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  const triggerSync = useCallback(async () => {
    try {
      setSyncing(true)
      await launchService.triggerSync()
      await fetchLaunches()
    } catch (err) {
      setError('Error al sincronizar datos con SpaceX API.')
      console.error(err)
    } finally {
      setSyncing(false)
    }
  }, [fetchLaunches])

  // Aplicar filtros cada vez que cambian launches o filters
  useEffect(() => {
    let result = [...launches]

    if (filters.status !== 'all') {
      result = result.filter((l) => l.status === filters.status)
    }
    if (filters.search) {
      const q = filters.search.toLowerCase()
      result = result.filter(
        (l) =>
          l.mission_name.toLowerCase().includes(q) ||
          l.rocket_name.toLowerCase().includes(q) ||
          l.launchpad.toLowerCase().includes(q),
      )
    }
    if (filters.dateFrom) {
      result = result.filter((l) => l.launch_date >= filters.dateFrom)
    }
    if (filters.dateTo) {
      result = result.filter((l) => l.launch_date <= filters.dateTo)
    }

    // Ordenar por fecha descendente
    result.sort((a, b) => new Date(b.launch_date).getTime() - new Date(a.launch_date).getTime())
    setFiltered(result)
  }, [launches, filters])

  useEffect(() => {
    fetchLaunches()
  }, [fetchLaunches])

  return {
    launches: filtered,
    allLaunches: launches,
    stats,
    filters,
    setFilters,
    loading,
    syncing,
    error,
    refetch: fetchLaunches,
    triggerSync,
  }
}
