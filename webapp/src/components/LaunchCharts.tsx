import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { format } from 'date-fns'
import type { Launch } from '@/types/launch'

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Title, Tooltip, Legend,
)

interface LaunchChartsProps {
  launches: Launch[]
}

export function LaunchCharts({ launches }: LaunchChartsProps) {
  // ── Doughnut: distribución por estado ──────────────────────────────────────
  const statusCounts = launches.reduce(
    (acc, l) => { acc[l.status] = (acc[l.status] || 0) + 1; return acc },
    {} as Record<string, number>,
  )

  const doughnutData = {
    labels: ['Exitosos', 'Fallidos', 'Próximos', 'Desconocidos'],
    datasets: [{
      data: [
        statusCounts['success'] || 0,
        statusCounts['failed'] || 0,
        statusCounts['upcoming'] || 0,
        statusCounts['unknown'] || 0,
      ],
      backgroundColor: ['#22c55e', '#ef4444', '#f59e0b', '#94a3b8'],
      borderWidth: 2,
      borderColor: '#1e293b',
    }],
  }

  // ── Bar: lanzamientos por año ──────────────────────────────────────────────
  const byYear: Record<string, { success: number; failed: number; upcoming: number }> = {}
  launches.forEach((l) => {
    const year = l.launch_date ? new Date(l.launch_date).getFullYear().toString() : 'N/A'
    if (!byYear[year]) byYear[year] = { success: 0, failed: 0, upcoming: 0 }
    if (l.status === 'success') byYear[year].success++
    else if (l.status === 'failed') byYear[year].failed++
    else if (l.status === 'upcoming') byYear[year].upcoming++
  })

  const years = Object.keys(byYear).sort()
  const barData = {
    labels: years,
    datasets: [
      { label: 'Exitosos', data: years.map((y) => byYear[y].success), backgroundColor: '#22c55e' },
      { label: 'Fallidos', data: years.map((y) => byYear[y].failed), backgroundColor: '#ef4444' },
      { label: 'Próximos', data: years.map((y) => byYear[y].upcoming), backgroundColor: '#f59e0b' },
    ],
  }

  // ── Line: acumulado de lanzamientos exitosos en el tiempo ──────────────────
  const successByMonth = launches
    .filter((l) => l.status === 'success' && l.launch_date)
    .sort((a, b) => new Date(a.launch_date).getTime() - new Date(b.launch_date).getTime())

  let cumulative = 0
  const lineLabels: string[] = []
  const lineData: number[] = []
  successByMonth.forEach((l) => {
    try {
      lineLabels.push(format(new Date(l.launch_date), 'MMM yy'))
      lineData.push(++cumulative)
    } catch { /* skip invalid dates */ }
  })

  const lineChartData = {
    labels: lineLabels,
    datasets: [{
      label: 'Acumulado de éxitos',
      data: lineData,
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.15)',
      fill: true,
      tension: 0.4,
      pointRadius: 2,
    }],
  }

  const darkOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8' } },
      title: { display: true, text: title, color: '#e2e8f0', font: { size: 14 } },
    },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
      y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
    },
  })

  return (
    <div className="charts-grid">
      <div className="chart-card chart-card--sm">
        <Doughnut
          data={doughnutData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom', labels: { color: '#94a3b8' } },
              title: { display: true, text: 'Distribución por estado', color: '#e2e8f0', font: { size: 14 } },
            },
          }}
        />
      </div>

      <div className="chart-card chart-card--lg">
        <Bar
          data={barData}
          options={{
            ...darkOptions('Lanzamientos por año'),
            scales: {
              x: { stacked: true, ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
              y: { stacked: true, ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
            },
          }}
        />
      </div>

      <div className="chart-card chart-card--full">
        <Line data={lineChartData} options={darkOptions('Acumulado de lanzamientos exitosos')} />
      </div>
    </div>
  )
}
