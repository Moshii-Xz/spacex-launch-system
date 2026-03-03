import type { LaunchStats } from '@/types/launch'

interface StatsCardProps {
  stats: LaunchStats
}

export function StatsCards({ stats }: StatsCardProps) {
  const safeTotal = stats.total || 1

  const cards = [
    {
      label: 'Total Lanzamientos',
      value: stats.total,
      color: 'card--blue',
      icon: '🚀',
      barWidth: 100,
    },
    {
      label: 'Exitosos',
      value: stats.success,
      color: 'card--green',
      icon: '✅',
      barWidth: Math.round((stats.success / safeTotal) * 100),
    },
    {
      label: 'Fallidos',
      value: stats.failed,
      color: 'card--red',
      icon: '❌',
      barWidth: Math.round((stats.failed / safeTotal) * 100),
    },
    {
      label: 'Próximos',
      value: stats.upcoming,
      color: 'card--yellow',
      icon: '📅',
      barWidth: Math.round((stats.upcoming / safeTotal) * 100),
    },
    {
      label: 'Tasa de Éxito',
      value: `${stats.successRate}%`,
      color: 'card--purple',
      icon: '📊',
      barWidth: stats.successRate,
    },
  ]

  return (
    <div className="stats-grid">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card ${c.color}`}>
          <span className="stat-icon">{c.icon}</span>
          <span className="stat-value">{c.value}</span>
          <span className="stat-label">{c.label}</span>
          <div className="stat-bar">
            <div className="stat-bar__fill" style={{ width: `${c.barWidth}%` }} />
          </div>
        </div>
      ))}
    </div>
  )
}
