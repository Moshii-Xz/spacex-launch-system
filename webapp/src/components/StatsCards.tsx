import type { LaunchStats } from '@/types/launch'

interface StatsCardProps {
  stats: LaunchStats
}

export function StatsCards({ stats }: StatsCardProps) {
  const cards = [
    { label: 'Total Lanzamientos', value: stats.total, color: 'card--blue', icon: '🚀' },
    { label: 'Exitosos', value: stats.success, color: 'card--green', icon: '✅' },
    { label: 'Fallidos', value: stats.failed, color: 'card--red', icon: '❌' },
    { label: 'Próximos', value: stats.upcoming, color: 'card--yellow', icon: '📅' },
    { label: 'Tasa de Éxito', value: `${stats.successRate}%`, color: 'card--purple', icon: '📊' },
  ]

  return (
    <div className="stats-grid">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card ${c.color}`}>
          <span className="stat-icon">{c.icon}</span>
          <span className="stat-value">{c.value}</span>
          <span className="stat-label">{c.label}</span>
        </div>
      ))}
    </div>
  )
}
