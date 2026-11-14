export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024

export const queryKeys = {
  health: ['health'] as const,
  capabilities: ['capabilities'] as const,
  binaries: ['binaries'] as const,
  investigations: ['investigations'] as const,
  investigation: (id: string) => ['investigation', id] as const,
}

export type InvestigationStatus = 'created' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Investigation {
  id: string
  binary_id: string
  objective: string
  status: InvestigationStatus
  max_tool_calls: number
  dynamic_execution: boolean
  findings: Record<string, unknown>[]
}

export interface BinaryRecord {
  id: string
  sha256: string
  label: string
  format: string
  size_bytes: number
}

export interface Capability {
  id: string
  description: string
  tools: string[]
  allows_execution: boolean
}

export interface Health {
  status: string
  platform: string
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function errorDetail(error: unknown): string {
  if (error instanceof ApiError) return `${error.status} ${error.detail}`
  if (error instanceof Error) return error.message
  return 'Unknown error'
}

async function parse<T>(response: Response): Promise<T> {
  if (response.ok) return (await response.json()) as T
  let detail = response.statusText || 'Request failed'
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const value = (body as { detail: unknown }).detail
      detail = typeof value === 'string' ? value : JSON.stringify(value)
    }
  } catch {
    // Non-JSON error bodies keep the HTTP status text.
  }
  throw new ApiError(response.status, detail)
}

export async function getHealth(): Promise<Health> {
  return parse<Health>(await fetch('/health'))
}

export async function listCapabilities(): Promise<Capability[]> {
  return parse<Capability[]>(await fetch('/api/v1/capabilities'))
}

export async function listBinaries(): Promise<BinaryRecord[]> {
  return parse<BinaryRecord[]>(await fetch('/api/v1/binaries'))
}

export async function uploadBinary(file: File): Promise<BinaryRecord> {
  const body = new FormData()
  body.append('file', file)
  return parse<BinaryRecord>(await fetch('/api/v1/binaries', { method: 'POST', body }))
}

export async function listInvestigations(): Promise<Investigation[]> {
  return parse<Investigation[]>(await fetch('/api/v1/investigations'))
}

export async function getInvestigation(id: string): Promise<Investigation> {
  return parse<Investigation>(await fetch(`/api/v1/investigations/${encodeURIComponent(id)}`))
}

export async function createInvestigation(binaryId: string, objective: string): Promise<Investigation> {
  return parse<Investigation>(
    await fetch('/api/v1/investigations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ binary_id: binaryId, objective, dynamic_execution: false }),
    }),
  )
}
