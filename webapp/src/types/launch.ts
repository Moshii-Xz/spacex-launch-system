export type LaunchStatus = 'success' | 'failed' | 'upcoming' | 'unknown'

export interface Launch {
  launch_id: string
  mission_name: string
  rocket_name: string
  launch_date: string
  status: LaunchStatus
  launchpad: string
  flight_number: string
  details: string
  payloads: string[]
  webcast_url: string
  article_url: string
  wikipedia_url: string
  patch_small: string
  patch_large: string
}

export interface LaunchFilters {
  status: LaunchStatus | 'all'
  search: string
  dateFrom: string
  dateTo: string
}

export interface LaunchStats {
  total: number
  success: number
  failed: number
  upcoming: number
  successRate: number
}
