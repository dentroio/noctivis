import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ScanSearch } from 'lucide-react'
import { EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge } from '@sgerhart/ux-framework'
import {
  enqueueAnalysis,
  errorDetail,
  getAnalysis,
  getInvestigation,
  listBinaries,
  listEvidence,
  queryKeys,
  type EvidenceRecord,
} from '../api'
import { panelClass, primaryButtonClass, statusLabel, statusTone } from '../ui'

const PURPOSE = 'The question this investigation is asking, and any findings recorded so far.'

function pendingStatus(status: string | undefined): number | false {
  return status === 'queued' || status === 'running' ? 2000 : false
}

export function InvestigationDetail() {
  const { investigationId = '' } = useParams()
  const queryClient = useQueryClient()
  const investigation = useQuery({
    queryKey: queryKeys.investigation(investigationId),
    queryFn: () => getInvestigation(investigationId),
    enabled: investigationId.length > 0,
    refetchInterval: (query) => pendingStatus(query.state.data?.status),
  })
  const analysis = useQuery({
    queryKey: queryKeys.analysis(investigationId),
    queryFn: () => getAnalysis(investigationId),
    enabled: investigationId.length > 0,
    refetchInterval: () => pendingStatus(investigation.data?.status),
  })
  const evidence = useQuery({
    queryKey: queryKeys.evidence(investigationId),
    queryFn: () => listEvidence(investigationId),
    enabled: investigationId.length > 0,
    refetchInterval: () => pendingStatus(investigation.data?.status),
  })
  const analyze = useMutation({
    mutationFn: () => enqueueAnalysis(investigationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.investigation(investigationId) })
      await queryClient.invalidateQueries({ queryKey: queryKeys.analysis(investigationId) })
      await queryClient.invalidateQueries({ queryKey: queryKeys.investigations })
    },
  })
  const binaries = useQuery({ queryKey: queryKeys.binaries, queryFn: listBinaries })
  const sample = binaries.data?.find((item) => item.id === investigation.data?.binary_id)

  if (investigation.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Investigation" purpose={PURPOSE} />
        <LoadingState message="Loading investigation…" />
      </div>
    )
  }

  if (investigation.isError || !investigation.data) {
    return (
      <div className="space-y-6">
        <PageHeader title="Investigation" purpose={PURPOSE} stateChip={{ label: 'Unavailable', variant: 'error' }} />
        <ErrorState
          title="Could not load this investigation"
          message="It may have been lost when the API restarted. Start again from the investigation list."
          detail={investigation.error ? errorDetail(investigation.error) : 'Missing investigation'}
          retryAction={{ label: 'Try again', onClick: () => void investigation.refetch() }}
        />
      </div>
    )
  }

  const record = investigation.data

  return (
    <div className="space-y-6">
      <PageHeader
        title={record.objective}
        purpose={PURPOSE}
        stateChip={{ label: statusLabel(record.status), variant: record.status === 'failed' ? 'error' : 'info' }}
      />
      <dl className={`grid gap-4 p-4 sm:grid-cols-2 ${panelClass}`}>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">Status</dt>
          <dd className="mt-1">
            <StatusBadge tone={statusTone(record.status)}>{statusLabel(record.status)}</StatusBadge>
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">Execution</dt>
          <dd className="mt-1">
            <StatusBadge tone={record.dynamic_execution ? 'danger' : 'neutral'}>
              {record.dynamic_execution ? 'Execution requested' : 'Not executed'}
            </StatusBadge>
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">Sample</dt>
          <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
            {sample ? (
              <Link to="/binaries" className="text-brand hover:underline">
                {sample.label}
              </Link>
            ) : (
              'This sample is no longer on the workstation.'
            )}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">Tool-call budget</dt>
          <dd className="mt-1 text-sm tabular-nums text-gray-900 dark:text-gray-100">{record.max_tool_calls}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">SHA-256</dt>
          <dd className="mt-1 font-mono text-xs break-all text-gray-900 dark:text-gray-100">{record.binary_id}</dd>
        </div>
      </dl>
      <StaticAnalysis
        format={sample?.format}
        jobStatus={analysis.data?.status}
        jobError={analysis.data?.error}
        evidence={evidence.data ?? []}
        busy={analyze.isPending || record.status === 'queued' || record.status === 'running'}
        actionError={analyze.isError ? errorDetail(analyze.error) : null}
        onAnalyze={() => analyze.mutate()}
      />
      {record.findings.length === 0 ? (
        <EmptyState
          icon={ScanSearch}
          title="No findings yet"
          description="A later review step writes findings. Static analysis evidence is listed above when a Ghidra job finishes."
        />
      ) : (
        <ul className="space-y-2">
          {record.findings.map((finding, index) => (
            <li key={index} className={`p-4 text-sm ${panelClass}`}>
              {JSON.stringify(finding)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function StaticAnalysis({
  format,
  jobStatus,
  jobError,
  evidence,
  busy,
  actionError,
  onAnalyze,
}: {
  format: string | undefined
  jobStatus: string | undefined
  jobError: string | undefined
  evidence: EvidenceRecord[]
  busy: boolean
  actionError: string | null
  onAnalyze: () => void
}) {
  const inventory = evidence.find((item) => item.kind === 'function_inventory')
  const decompilation = evidence.find((item) => item.kind === 'decompilation')
  const functions = inventory?.body.functions ?? []
  const canQueue = format === 'ELF' && !busy && jobStatus !== 'completed'

  return (
    <section className={`space-y-4 p-4 ${panelClass}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Static analysis</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-300">
            {inventory
              ? `Ghidra ${inventory.tool_version} read this sample and did not execute it.`
              : 'Queue a separate Ghidra process. The sample stays stored by hash and is not executed.'}
          </p>
        </div>
        {canQueue ? (
          <button type="button" className={primaryButtonClass} onClick={onAnalyze} disabled={busy}>
            Run static analysis
          </button>
        ) : null}
      </div>
      {format && format !== 'ELF' ? (
        <p className="text-sm text-gray-500 dark:text-gray-300">Static analysis currently accepts ELF samples.</p>
      ) : null}
      {busy ? <p className="text-sm text-gray-500 dark:text-gray-300">Ghidra is analyzing this sample.</p> : null}
      {jobStatus === 'failed' && jobError ? (
        <p className="text-sm text-red-700 dark:text-red-300">{jobError}</p>
      ) : null}
      {actionError ? <p className="text-sm text-red-700 dark:text-red-300">{actionError}</p> : null}
      {functions.length > 0 ? (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">
            Functions ({functions.length})
          </h3>
          <ul className="mt-2 divide-y divide-gray-200 dark:divide-[#163044]">
            {functions.map((item) => (
              <li key={`${item.name}-${item.entry}`} className="flex items-baseline justify-between gap-4 py-2 text-sm">
                <span className="font-medium text-gray-900 dark:text-gray-100">{item.name}</span>
                <span className="font-mono text-xs text-gray-500 dark:text-gray-300">{item.entry}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {decompilation?.body.text ? (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">
            Decompilation · {decompilation.body.name}
          </h3>
          <pre className="mt-2 max-h-80 overflow-auto rounded-md border border-gray-200 bg-[#030910] p-3 font-mono text-xs text-gray-100 dark:border-[#163044]">
            {decompilation.body.text}
          </pre>
        </div>
      ) : null}
    </section>
  )
}
