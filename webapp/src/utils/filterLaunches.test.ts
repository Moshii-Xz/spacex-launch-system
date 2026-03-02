import { describe, it, expect } from 'vitest'
import { filterLaunches } from './filterLaunches'
import type { Launch, LaunchFilters } from '@/types/launch'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const makeLaunch = (overrides: Partial<Launch> = {}): Launch => ({
  launch_id:    'id-001',
  mission_name: 'Default Mission',
  rocket_name:  'Falcon 9',
  launch_date:  '2024-06-15T10:00:00.000Z',
  status:       'success',
  launchpad:    'KSC LC-39A',
  flight_number:'1',
  details:      '',
  payloads:     [],
  webcast_url:  '',
  article_url:  '',
  wikipedia_url:'',
  patch_small:  '',
  patch_large:  '',
  ...overrides,
})

const noFilter: LaunchFilters = { status: 'all', search: '', dateFrom: '', dateTo: '' }

const LAUNCHES: Launch[] = [
  makeLaunch({ launch_id: '1', status: 'success',  mission_name: 'Starlink 1',   launch_date: '2024-03-01T00:00:00.000Z', rocket_name: 'Falcon 9',  launchpad: 'KSC' }),
  makeLaunch({ launch_id: '2', status: 'failed',   mission_name: 'FalconSat',    launch_date: '2006-03-24T00:00:00.000Z', rocket_name: 'Falcon 1',  launchpad: 'Omelek' }),
  makeLaunch({ launch_id: '3', status: 'upcoming', mission_name: 'Crew Dragon 9',launch_date: '2026-05-01T00:00:00.000Z', rocket_name: 'Falcon 9',  launchpad: 'KSC LC-39B' }),
  makeLaunch({ launch_id: '4', status: 'success',  mission_name: 'Starlink 2',   launch_date: '2024-08-20T00:00:00.000Z', rocket_name: 'Starship',  launchpad: 'Boca Chica' }),
]

// ── Sin filtros ───────────────────────────────────────────────────────────────

describe('filterLaunches', () => {
  it('retorna todos los lanzamientos sin filtros activos', () => {
    expect(filterLaunches(LAUNCHES, noFilter)).toHaveLength(4)
  })

  it('ordena por fecha descendente', () => {
    const result = filterLaunches(LAUNCHES, noFilter)
    expect(result[0].launch_id).toBe('3') // 2026 es el más reciente
    expect(result[3].launch_id).toBe('2') // 2006 es el más antiguo
  })

  // ── Filtro por estado ────────────────────────────────────────────────────────

  it('filtra por estado success', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, status: 'success' })
    expect(result).toHaveLength(2)
    expect(result.every((l) => l.status === 'success')).toBe(true)
  })

  it('filtra por estado failed', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, status: 'failed' })
    expect(result).toHaveLength(1)
    expect(result[0].launch_id).toBe('2')
  })

  it('filtra por estado upcoming', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, status: 'upcoming' })
    expect(result).toHaveLength(1)
    expect(result[0].launch_id).toBe('3')
  })

  it('retorna vacío si ningún lanzamiento tiene el estado buscado', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, status: 'unknown' })
    expect(result).toHaveLength(0)
  })

  // ── Filtro por búsqueda de texto ─────────────────────────────────────────────

  it('busca por nombre de misión (case-insensitive)', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, search: 'starlink' })
    expect(result).toHaveLength(2)
  })

  it('busca por nombre de cohete', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, search: 'starship' })
    expect(result).toHaveLength(1)
    expect(result[0].launch_id).toBe('4')
  })

  it('busca por nombre de plataforma', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, search: 'omelek' })
    expect(result).toHaveLength(1)
    expect(result[0].launch_id).toBe('2')
  })

  it('retorna vacío si búsqueda no coincide con nada', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, search: 'xyz-no-match' })
    expect(result).toHaveLength(0)
  })

  // ── Filtro por fecha ─────────────────────────────────────────────────────────

  it('filtra desde dateFrom (inclusive)', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, dateFrom: '2024-01-01T00:00:00.000Z' })
    // lanzamientos en 2024 (2) + upcoming 2026 (1) = 3
    expect(result).toHaveLength(3)
  })

  it('filtra hasta dateTo (inclusive)', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, dateTo: '2006-12-31T23:59:59.000Z' })
    expect(result).toHaveLength(1)
    expect(result[0].launch_id).toBe('2')
  })

  it('combina dateFrom y dateTo como rango', () => {
    const result = filterLaunches(LAUNCHES, {
      ...noFilter,
      dateFrom: '2024-01-01T00:00:00.000Z',
      dateTo:   '2024-12-31T23:59:59.000Z',
    })
    expect(result).toHaveLength(2) // solo los de 2024
  })

  // ── Filtros combinados ────────────────────────────────────────────────────────

  it('combina status y search correctamente', () => {
    const result = filterLaunches(LAUNCHES, { ...noFilter, status: 'success', search: 'starlink' })
    expect(result).toHaveLength(2)
  })

  it('no muta el array original', () => {
    const original = [...LAUNCHES]
    filterLaunches(LAUNCHES, { ...noFilter, status: 'failed' })
    expect(LAUNCHES).toEqual(original)
  })
})
