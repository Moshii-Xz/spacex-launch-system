import { useState } from 'react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import type { Launch } from '@/types/launch'

interface LaunchTableProps {
  launches: Launch[]
}

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  success:  { label: '✅ Exitoso',  cls: 'badge--green'  },
  failed:   { label: '❌ Fallido',  cls: 'badge--red'    },
  upcoming: { label: '📅 Próximo',  cls: 'badge--yellow' },
  unknown:  { label: '❓ Desconocido', cls: 'badge--gray' },
}

type SortKey = 'launch_date' | 'mission_name' | 'flight_number' | 'status'

export function LaunchTable({ launches }: LaunchTableProps) {
  const [page, setPage] = useState(1)
  const [sortKey, setSortKey] = useState<SortKey>('launch_date')
  const [sortAsc, setSortAsc] = useState(false)

  const PER_PAGE = 15

  const sorted = [...launches].sort((a, b) => {
    let va = a[sortKey] ?? ''
    let vb = b[sortKey] ?? ''
    if (sortKey === 'launch_date') {
      va = new Date(va).getTime().toString()
      vb = new Date(vb).getTime().toString()
    }
    return sortAsc
      ? String(va).localeCompare(String(vb))
      : String(vb).localeCompare(String(va))
  })

  const total = sorted.length
  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE))
  const slice = sorted.slice((page - 1) * PER_PAGE, page * PER_PAGE)

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(true) }
    setPage(1)
  }

  const arrow = (key: SortKey) =>
    sortKey === key ? (sortAsc ? ' ▲' : ' ▼') : ' ⇅'

  const formatDate = (iso: string) => {
    try { return format(new Date(iso), 'dd MMM yyyy', { locale: es }) }
    catch { return iso }
  }

  if (launches.length === 0) {
    return <div className="empty-state">No se encontraron lanzamientos con los filtros actuales.</div>
  }

  return (
    <div className="table-wrapper">
      <table className="launch-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('flight_number')} className="sortable">
              # {arrow('flight_number')}
            </th>
            <th className="th-patch"></th>
            <th onClick={() => handleSort('mission_name')} className="sortable">
              Misión {arrow('mission_name')}
            </th>
            <th>Cohete</th>
            <th onClick={() => handleSort('launch_date')} className="sortable">
              Fecha {arrow('launch_date')}
            </th>
            <th onClick={() => handleSort('status')} className="sortable">
              Estado {arrow('status')}
            </th>
            <th>Plataforma</th>
            <th>Links</th>
          </tr>
        </thead>
        <tbody>
          {slice.map((l) => {
            const badge = STATUS_BADGE[l.status] ?? STATUS_BADGE.unknown
            return (
              <tr key={l.launch_id}>
                <td className="td-num">{l.flight_number}</td>
                <td className="td-patch">
                  {l.patch_small && (
                    <img src={l.patch_small} alt={l.mission_name} className="patch-img" />
                  )}
                </td>
                <td>
                  <span className="mission-name">{l.mission_name}</span>
                  {l.details && (
                    <span className="mission-details" title={l.details}>
                      {l.details.slice(0, 60)}{l.details.length > 60 ? '…' : ''}
                    </span>
                  )}
                </td>
                <td>{l.rocket_name || '—'}</td>
                <td className="td-date">{formatDate(l.launch_date)}</td>
                <td><span className={`badge ${badge.cls}`}>{badge.label}</span></td>
                <td className="td-pad">{l.launchpad || '—'}</td>
                <td className="td-links">
                  {l.webcast_url && <a href={l.webcast_url} target="_blank" rel="noreferrer" title="Ver webcast">▶</a>}
                  {l.wikipedia_url && <a href={l.wikipedia_url} target="_blank" rel="noreferrer" title="Wikipedia">📖</a>}
                  {l.article_url && <a href={l.article_url} target="_blank" rel="noreferrer" title="Artículo">📰</a>}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setPage(1)} disabled={page === 1}>«</button>
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>‹</button>
          <span>{page} / {totalPages}</span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages}>›</button>
          <button onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
        </div>
      )}
    </div>
  )
}
