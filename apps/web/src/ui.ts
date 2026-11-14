import type { BadgeTone } from '@sgerhart/ux-framework'
import type { InvestigationStatus } from './api'

export const inputClass =
  'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100'

export const primaryButtonClass =
  'rounded-md bg-brand px-4 py-2 text-sm font-medium text-brand-fg hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-50'

const STATUS_TONE: Record<InvestigationStatus, BadgeTone> = {
  created: 'info',
  queued: 'info',
  running: 'warning',
  completed: 'success',
  failed: 'danger',
  cancelled: 'neutral',
}

const STATUS_LABEL: Record<InvestigationStatus, string> = {
  created: 'Created',
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

export function statusTone(status: InvestigationStatus): BadgeTone {
  return STATUS_TONE[status]
}

export function statusLabel(status: InvestigationStatus): string {
  return STATUS_LABEL[status]
}

export function formatBytes(size: number): string {
  return `${size.toLocaleString()} bytes`
}
