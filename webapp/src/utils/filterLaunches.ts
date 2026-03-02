import type { Launch, LaunchFilters } from '@/types/launch'

/**
 * Filtra y ordena una lista de lanzamientos según los criterios dados.
 * Función pura: no produce efectos secundarios.
 */
export function filterLaunches(launches: Launch[], filters: LaunchFilters): Launch[] {
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

  return result
}
