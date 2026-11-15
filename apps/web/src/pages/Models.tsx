import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@sgerhart/ux-framework'
import {
  createConnector,
  deleteConnector,
  errorDetail,
  listConnectors,
  testConnector,
  updateConnector,
  type ConnectorRecord,
  type LlmConfig,
} from '../api'
import { inputClass, panelClass, primaryButtonClass } from '../ui'

const PURPOSE = 'Choose the hosted or local model later investigations will use. One provider is the default.'

const STATUS_LABEL: Record<string, string> = {
  unknown: 'Not tested',
  connected: 'Connected',
  unreachable: 'Unreachable',
  error: 'Error',
}

interface Draft {
  id: string | null
  name: string
  description: string
  provider: 'local' | 'hosted'
  model: string
  baseUrl: string
  apiKeyEnv: string
  isDefault: boolean
}

const EMPTY: Draft = {
  id: null,
  name: '',
  description: '',
  provider: 'local',
  model: '',
  baseUrl: 'http://127.0.0.1:11434',
  apiKeyEnv: '',
  isDefault: true,
}

function draftFrom(record: ConnectorRecord): Draft {
  return {
    id: record.id,
    name: record.name,
    description: record.description,
    provider: record.config.provider,
    model: record.config.model,
    baseUrl: record.config.base_url,
    apiKeyEnv: record.config.api_key_env ?? '',
    isDefault: record.is_default,
  }
}

function configFrom(draft: Draft): LlmConfig {
  const config: LlmConfig = {
    provider: draft.provider,
    model: draft.model.trim(),
    base_url: draft.baseUrl.trim(),
  }
  if (draft.provider === 'hosted') config.api_key_env = draft.apiKeyEnv.trim()
  return config
}

export function Models() {
  const queryClient = useQueryClient()
  const connectors = useQuery({ queryKey: ['connectors', 'llm'], queryFn: listConnectors })
  const [draft, setDraft] = useState<Draft | null>(null)
  const [formError, setFormError] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('')
  const [reply, setReply] = useState<string | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const records = connectors.data ?? []
  const enabled = records.filter((item) => item.enabled)
  const selected = records.find((item) => item.is_default) ?? null

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['connectors', 'llm'] })

  const save = useMutation({
    mutationFn: async (value: Draft) => {
      const body = {
        name: value.name.trim(),
        description: value.description.trim(),
        enabled: true,
        is_default: value.isDefault,
        config: configFrom(value),
      }
      if (value.id) return updateConnector(value.id, body)
      return createConnector(body)
    },
    onSuccess: async () => {
      setDraft(null)
      setFormError(null)
      await refresh()
    },
    onError: (error) => setFormError(errorDetail(error)),
  })

  const toggleDefault = useMutation({
    mutationFn: (record: ConnectorRecord) => updateConnector(record.id, { enabled: !record.enabled }),
    onSuccess: () => refresh(),
  })

  const remove = useMutation({
    mutationFn: (id: string) => deleteConnector(id),
    onSuccess: () => refresh(),
  })

  const probe = useMutation({
    mutationFn: () => {
      if (!selected) throw new Error('Choose a default provider first.')
      return testConnector(selected.id, prompt)
    },
    onSuccess: async (result) => {
      setReply(result.reply)
      setTestError(null)
      await refresh()
    },
    onError: (error) => {
      setReply(null)
      setTestError(errorDetail(error))
      void refresh()
    },
  })

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!draft) return
    setFormError(null)
    save.mutate(draft)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Models"
        purpose={PURPOSE}
        stateChip={
          connectors.isSuccess
            ? selected?.enabled
              ? { label: 'Default ready', variant: 'healthy' }
              : { label: 'No default', variant: 'unconfigured' }
            : undefined
        }
        actions={
          <>
            <button type="button" className={primaryButtonClass} onClick={() => { setDraft(EMPTY); setFormError(null) }}>
              Add provider
            </button>
            <button
              type="button"
              className="rounded-md border border-red-400/40 px-4 py-2 text-sm font-medium text-red-300 disabled:opacity-50"
              disabled={!selected || toggleDefault.isPending}
              onClick={() => selected && toggleDefault.mutate(selected)}
            >
              {selected?.enabled ? 'Disable' : 'Enable'}
            </button>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <section className={`${panelClass} p-4`}>
          <div className="text-xs font-semibold uppercase tracking-wide text-[#7ec8e8]">What this connection does</div>
          <p className="mt-2 text-sm text-gray-300">Connects this workstation to a local or hosted model. The model cannot start a tool or send a sample.</p>
        </section>
        <section className={`${panelClass} p-4`}>
          <div className="text-xs font-semibold uppercase tracking-wide text-[#7ec8e8]">Current status</div>
          <p className="mt-2 text-sm text-gray-300">
            {connectors.isSuccess
              ? `${enabled.length} of ${records.length} enabled. Default is ${selected ? selected.name : 'not set'}.`
              : 'Loading providers.'}
          </p>
        </section>
        <section className={`${panelClass} p-4`}>
          <div className="text-xs font-semibold uppercase tracking-wide text-[#7ec8e8]">Next action</div>
          <p className="mt-2 text-sm text-gray-300">Send a test prompt before relying on a hosted model. The prompt leaves this workstation only when you send it.</p>
        </section>
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-300">Providers</h2>
        {records.length === 0 && connectors.isSuccess && (
          <p className={`${panelClass} p-4 text-sm text-gray-300`}>No model providers yet. Add a local model or a hosted one.</p>
        )}
        {selected && (
          <p className="rounded-lg border border-[#00a6e8]/40 bg-[#00a6e8]/10 px-4 py-2 text-sm text-[#d7f3ff]">
            Default: {selected.name} · {selected.config.model}
          </p>
        )}
        {records.map((record) => (
          <article key={record.id} className={`${panelClass} flex flex-wrap items-center justify-between gap-3 p-4`}>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-gray-100">{record.name}</span>
                {record.is_default && <span className="rounded border border-[#00a6e8]/50 px-1.5 text-xs text-[#7ec8e8]">Default</span>}
                <span className="text-xs uppercase tracking-wide text-gray-400">{record.config.provider}</span>
                <span className={record.last_status === 'connected' ? 'text-xs text-emerald-300' : 'text-xs text-gray-400'}>
                  {record.enabled ? STATUS_LABEL[record.last_status] ?? record.last_status : 'Disabled'}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-400">
                Model {record.config.model}
                {record.last_checked_at ? ` · Last tested ${new Date(record.last_checked_at).toLocaleString()}` : ''}
              </p>
            </div>
            <div className="flex gap-2">
              <button type="button" className="rounded-md px-3 py-1.5 text-sm text-[#7ec8e8]" onClick={() => { setDraft(draftFrom(record)); setFormError(null) }}>
                Edit
              </button>
              <button type="button" className="rounded-md px-3 py-1.5 text-sm text-red-300" onClick={() => remove.mutate(record.id)}>
                Delete
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className={`${panelClass} p-4`}>
        <h2 className="text-sm font-semibold text-gray-100">Test prompt</h2>
        <p className="mt-1 text-sm text-gray-400">
          Send a short prompt using {selected ? selected.name : 'the default provider'}. Sample bytes are not included.
        </p>
        <form
          className="mt-3 flex flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault()
            setTestError(null)
            probe.mutate()
          }}
        >
          <label className="block flex-1 text-sm text-gray-200">
            Prompt
            <input className={`${inputClass} mt-1`} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask a short question" />
          </label>
          <button type="submit" className={`${primaryButtonClass} self-end`} disabled={!selected?.enabled || probe.isPending}>
            Send
          </button>
        </form>
        {testError && <p className="mt-3 text-sm text-red-300">{testError}</p>}
        {reply && <p className="mt-3 whitespace-pre-wrap text-sm text-gray-100">{reply}</p>}
      </section>

      <p className="text-sm text-gray-400">Agents will be listed in Connect after an investigation can run one. None are registered yet.</p>

      {draft && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-16" onMouseDown={(event) => event.target === event.currentTarget && setDraft(null)}>
          <form onSubmit={submit} className="w-full max-w-lg rounded-xl border border-[#163044] bg-[#071018] p-6 shadow-xl" role="dialog" aria-labelledby="provider-title">
            <h2 id="provider-title" className="text-lg font-semibold text-gray-100">{draft.id ? 'Edit provider' : 'Add provider'}</h2>
            <div className="mt-4 space-y-3">
              <label className="block text-sm text-gray-200">
                Name
                <input className={`${inputClass} mt-1`} value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} required />
              </label>
              <label className="block text-sm text-gray-200">
                Type
                <select
                  className={`${inputClass} mt-1`}
                  value={draft.provider}
                  onChange={(event) => setDraft({ ...draft, provider: event.target.value as Draft['provider'] })}
                >
                  <option value="local">Local</option>
                  <option value="hosted">Hosted</option>
                </select>
              </label>
              <label className="block text-sm text-gray-200">
                Description
                <input className={`${inputClass} mt-1`} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} />
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-200">
                <input type="checkbox" checked={draft.isDefault} onChange={(event) => setDraft({ ...draft, isDefault: event.target.checked })} />
                Set as default provider
              </label>
              <label className="block text-sm text-gray-200">
                Model name
                <input className={`${inputClass} mt-1`} value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} required />
              </label>
              <label className="block text-sm text-gray-200">
                Base URL
                <input className={`${inputClass} mt-1`} value={draft.baseUrl} onChange={(event) => setDraft({ ...draft, baseUrl: event.target.value })} required />
              </label>
              {draft.provider === 'hosted' && (
                <label className="block text-sm text-gray-200">
                  Environment variable for the key
                  <input className={`${inputClass} mt-1`} value={draft.apiKeyEnv} onChange={(event) => setDraft({ ...draft, apiKeyEnv: event.target.value })} placeholder="MODEL_API_KEY" required />
                </label>
              )}
            </div>
            {formError && <p className="mt-3 text-sm text-red-300">{formError}</p>}
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" className="rounded-md px-4 py-2 text-sm text-gray-300" onClick={() => setDraft(null)}>Cancel</button>
              <button type="submit" className={primaryButtonClass} disabled={save.isPending}>{draft.id ? 'Save provider' : 'Create provider'}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
