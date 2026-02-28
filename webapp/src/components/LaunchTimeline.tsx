import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import type { Launch } from '@/types/launch'

interface LaunchTimelineProps {
  launches: Launch[]
}

const STATUS_COLOR: Record<string, string> = {
  success:  '#22c55e',
  failed:   '#ef4444',
  upcoming: '#f59e0b',
  unknown:  '#94a3b8',
}

const STATUS_ICON: Record<string, string> = {
  success:  '✅',
  failed:   '❌',
  upcoming: '📅',
  unknown:  '❓',
}

export function LaunchTimeline({ launches }: LaunchTimelineProps) {
  if (launches.length === 0) {
    return <div className="empty-state">No hay lanzamientos para mostrar en la línea de tiempo.</div>
  }

  // Mostrar máximo 40 en el timeline para no saturar
  const items = [...launches]
    .sort((a, b) => new Date(b.launch_date).getTime() - new Date(a.launch_date).getTime())
    .slice(0, 40)

  const formatDate = (iso: string) => {
    try { return format(new Date(iso), 'dd MMM yyyy HH:mm', { locale: es }) }
    catch { return iso }
  }

  return (
    <div className="timeline">
      {items.map((l, idx) => (
        <div key={l.launch_id} className={`timeline-item ${idx % 2 === 0 ? 'timeline-item--left' : 'timeline-item--right'}`}>
          <div
            className="timeline-dot"
            style={{ backgroundColor: STATUS_COLOR[l.status] ?? STATUS_COLOR.unknown }}
          >
            {STATUS_ICON[l.status] ?? STATUS_ICON.unknown}
          </div>

          <div className="timeline-card">
            <div className="timeline-card__header">
              {l.patch_small && (
                <img src={l.patch_small} alt={l.mission_name} className="timeline-patch" />
              )}
              <div>
                <h3 className="timeline-mission">{l.mission_name}</h3>
                <span className="timeline-date">{formatDate(l.launch_date)}</span>
              </div>
            </div>

            <div className="timeline-card__body">
              <p className="timeline-rocket">🚀 {l.rocket_name || 'Cohete desconocido'}</p>
              {l.launchpad && <p className="timeline-pad">📍 {l.launchpad}</p>}
              {l.details && (
                <p className="timeline-details">
                  {l.details.slice(0, 100)}{l.details.length > 100 ? '…' : ''}
                </p>
              )}
            </div>

            {(l.webcast_url || l.wikipedia_url) && (
              <div className="timeline-card__links">
                {l.webcast_url && (
                  <a href={l.webcast_url} target="_blank" rel="noreferrer" className="timeline-link">
                    ▶ Webcast
                  </a>
                )}
                {l.wikipedia_url && (
                  <a href={l.wikipedia_url} target="_blank" rel="noreferrer" className="timeline-link">
                    📖 Wikipedia
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
