import { useState, useEffect, useCallback } from 'react'
import { launchService } from '@/services/launchService'
import { filterLaunches } from '@/utils/filterLaunches'
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
    setFiltered(filterLaunches(launches, filters))
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
