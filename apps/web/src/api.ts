export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024

export const queryKeys = {
  health: ['health'] as const,
  capabilities: ['capabilities'] as const,
  binaries: ['binaries'] as const,
  investigations: ['investigations'] as const,
  investigation: (id: string) => ['investigation', id] as const,
  analysis: (id: string) => ['analysis', id] as const,
  evidence: (id: string) => ['evidence', id] as const,
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

import { tokens } from './auth'

export function errorDetail(error: unknown): string {
  if (error instanceof ApiError) return `${error.status} ${error.detail}`
  if (error instanceof Error) return error.message
  return 'Unknown error'
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)
  const token = tokens.getAccess()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(path, { ...init, headers })
  if (response.status === 401 && window.location.pathname !== '/login') {
    tokens.clear()
    window.location.assign('/login')
  }
  return response
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
  return parse<Capability[]>(await send('/api/v1/capabilities'))
}

export async function listBinaries(): Promise<BinaryRecord[]> {
  return parse<BinaryRecord[]>(await send('/api/v1/binaries'))
}

export async function uploadBinary(file: File): Promise<BinaryRecord> {
  const body = new FormData()
  body.append('file', file)
  return parse<BinaryRecord>(await send('/api/v1/binaries', { method: 'POST', body }))
}

export async function listInvestigations(): Promise<Investigation[]> {
  return parse<Investigation[]>(await send('/api/v1/investigations'))
}

export async function getInvestigation(id: string): Promise<Investigation> {
  return parse<Investigation>(await send(`/api/v1/investigations/${encodeURIComponent(id)}`))
}

export interface AnalysisJob {
  id: string
  investigation_id: string
  binary_id: string
  sha256: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  error: string
}

export interface AnalysisFunction {
  name: string
  entry: string
}

export interface EvidenceRecord {
  id: string
  investigation_id: string
  binary_id: string
  job_id: string
  sha256: string
  tool: string
  tool_version: string
  kind: 'function_inventory' | 'decompilation'
  body: {
    functions?: AnalysisFunction[]
    name?: string
    entry?: string
    text?: string
  }
}

export async function getAnalysis(id: string): Promise<AnalysisJob | null> {
  try {
    return await parse<AnalysisJob>(await send(`/api/v1/investigations/${encodeURIComponent(id)}/analysis`))
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  }
}

export async function enqueueAnalysis(id: string): Promise<AnalysisJob> {
  return parse<AnalysisJob>(
    await send(`/api/v1/investigations/${encodeURIComponent(id)}/analysis`, { method: 'POST' }),
  )
}

export async function listEvidence(id: string): Promise<EvidenceRecord[]> {
  return parse<EvidenceRecord[]>(await send(`/api/v1/investigations/${encodeURIComponent(id)}/evidence`))
}

export interface LlmConfig {
  provider: 'local' | 'hosted'
  model: string
  base_url: string
  api_key_env?: string
}

export interface ConnectorRecord {
  id: string
  kind: string
  name: string
  description: string
  enabled: boolean
  is_default: boolean
  config: LlmConfig
  last_checked_at: string | null
  last_status: string
}

export async function listConnectors(): Promise<ConnectorRecord[]> {
  return parse<ConnectorRecord[]>(await send('/api/v1/connectors?kind=llm'))
}

export async function createConnector(body: {
  name: string
  description: string
  enabled: boolean
  is_default: boolean
  config: LlmConfig
}): Promise<ConnectorRecord> {
  return parse<ConnectorRecord>(
    await send('/api/v1/connectors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}

export async function updateConnector(
  id: string,
  body: Partial<{ name: string; description: string; enabled: boolean; is_default: boolean; config: LlmConfig }>,
): Promise<ConnectorRecord> {
  return parse<ConnectorRecord>(
    await send(`/api/v1/connectors/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}

export async function deleteConnector(id: string): Promise<void> {
  await parse(await send(`/api/v1/connectors/${encodeURIComponent(id)}`, { method: 'DELETE' }))
}

export async function testConnector(id: string, prompt: string): Promise<{ reply: string; connector: ConnectorRecord }> {
  return parse(await send(`/api/v1/connectors/${encodeURIComponent(id)}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  }))
}

export async function createInvestigation(binaryId: string, objective: string): Promise<Investigation> {
  return parse<Investigation>(
    await send('/api/v1/investigations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ binary_id: binaryId, objective, dynamic_execution: false }),
    }),
  )
}
