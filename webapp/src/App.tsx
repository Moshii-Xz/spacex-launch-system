import { useState } from 'react'
import { useLaunches } from '@/hooks/useLaunches'
import { StatsCards } from '@/components/StatsCards'
import { FilterBar } from '@/components/FilterBar'
import { LaunchTable } from '@/components/LaunchTable'
import { LaunchCharts } from '@/components/LaunchCharts'
import { LaunchTimeline } from '@/components/LaunchTimeline'

type Tab = 'table' | 'charts' | 'timeline'

function App() {
  const { launches, allLaunches, stats, filters, setFilters, loading, syncing, error, triggerSync } = useLaunches()
  const [activeTab, setActiveTab] = useState<Tab>('table')

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="header">
        <div className="header__brand">
          <span className="header__logo">🚀</span>
          <div>
            <h1 className="header__title">SpaceX Launch Tracker</h1>
            <p className="header__subtitle">Sistema de seguimiento de lanzamientos espaciales</p>
          </div>
        </div>
        <div className="header__meta">
          <span className="header__count">{allLaunches.length} lanzamientos en BD</span>
        </div>
      </header>

      <main className="main">
        {/* ── Error ──────────────────────────────────────────────────────── */}
        {error && (
          <div className="alert alert--error">
            ⚠️ {error}
          </div>
        )}

        {/* ── Stats ──────────────────────────────────────────────────────── */}
        {loading ? (
          <div className="skeleton-grid">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton-card" />
            ))}
          </div>
        ) : (
          <StatsCards stats={stats} />
        )}

        {/* ── Filtros ────────────────────────────────────────────────────── */}
        <FilterBar
          filters={filters}
          onChange={setFilters}
          onSync={triggerSync}
          syncing={syncing}
          total={launches.length}
        />

        {/* ── Tabs ───────────────────────────────────────────────────────── */}
        <div className="tabs">
          {(['table', 'charts', 'timeline'] as Tab[]).map((tab) => (
            <button
              key={tab}
              className={`tab ${activeTab === tab ? 'tab--active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'table' && '📋 Tabla'}
              {tab === 'charts' && '📊 Gráficos'}
              {tab === 'timeline' && '⏱ Línea de tiempo'}
            </button>
          ))}
        </div>

        {/* ── Contenido ──────────────────────────────────────────────────── */}
        <div className="content">
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner" />
              <p>Cargando lanzamientos...</p>
            </div>
          ) : (
            <>
              {activeTab === 'table' && <LaunchTable launches={launches} />}
              {activeTab === 'charts' && <LaunchCharts launches={allLaunches} />}
              {activeTab === 'timeline' && <LaunchTimeline launches={launches} />}
            </>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>Datos obtenidos de la <a href="https://github.com/r-spacex/SpaceX-API" target="_blank" rel="noreferrer">SpaceX API v4</a> · Desplegado en AWS ECS Fargate</p>
      </footer>
    </div>
  )
}

export default App
