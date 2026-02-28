import type { LaunchFilters } from '@/types/launch'

interface FilterBarProps {
  filters: LaunchFilters
  onChange: (filters: LaunchFilters) => void
  onSync: () => void
  syncing: boolean
  total: number
}

export function FilterBar({ filters, onChange, onSync, syncing, total }: FilterBarProps) {
  const update = (patch: Partial<LaunchFilters>) => onChange({ ...filters, ...patch })

  return (
    <div className="filter-bar">
      <div className="filter-bar__left">
        <input
          type="text"
          className="filter-input"
          placeholder="🔍 Buscar misión, cohete, plataforma..."
          value={filters.search}
          onChange={(e) => update({ search: e.target.value })}
        />

        <select
          className="filter-select"
          value={filters.status}
          onChange={(e) => update({ status: e.target.value as LaunchFilters['status'] })}
        >
          <option value="all">Todos los estados</option>
          <option value="success">✅ Exitosos</option>
          <option value="failed">❌ Fallidos</option>
          <option value="upcoming">📅 Próximos</option>
        </select>

        <input
          type="date"
          className="filter-input filter-input--date"
          value={filters.dateFrom}
          onChange={(e) => update({ dateFrom: e.target.value })}
          title="Desde"
        />
        <input
          type="date"
          className="filter-input filter-input--date"
          value={filters.dateTo}
          onChange={(e) => update({ dateTo: e.target.value })}
          title="Hasta"
        />

        {(filters.search || filters.status !== 'all' || filters.dateFrom || filters.dateTo) && (
          <button
            className="btn btn--ghost"
            onClick={() => onChange({ status: 'all', search: '', dateFrom: '', dateTo: '' })}
          >
            ✕ Limpiar
          </button>
        )}
      </div>

      <div className="filter-bar__right">
        <span className="filter-count">{total} resultado{total !== 1 ? 's' : ''}</span>
        <button className="btn btn--primary" onClick={onSync} disabled={syncing}>
          {syncing ? '⏳ Sincronizando...' : '🔄 Sincronizar API'}
        </button>
      </div>
    </div>
  )
}
