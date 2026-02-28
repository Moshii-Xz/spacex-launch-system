import axios from 'axios'
import type { Launch, LaunchStats } from '@/types/launch'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export const launchService = {
  /** Obtiene todos los lanzamientos desde el backend/API Gateway */
  async getAllLaunches(): Promise<Launch[]> {
    const { data } = await api.get<Launch[]>('/launches')
    return data
  },

  /** Invoca la Lambda manualmente para refrescar los datos */
  async triggerSync(): Promise<{ total_fetched: number; inserted: number; updated: number }> {
    const { data } = await api.post('/trigger')
    return data
  },

  /** Calcula estadísticas localmente a partir del array de lanzamientos */
  computeStats(launches: Launch[]): LaunchStats {
    const total = launches.length
    const success = launches.filter((l) => l.status === 'success').length
    const failed = launches.filter((l) => l.status === 'failed').length
    const upcoming = launches.filter((l) => l.status === 'upcoming').length
    const successRate = total > 0 ? Math.round((success / (success + failed)) * 100) : 0
    return { total, success, failed, upcoming, successRate }
  },
}
