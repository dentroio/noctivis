import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ScanSearch } from 'lucide-react'
import { EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge } from '@sgerhart/ux-framework'
import { errorDetail, getInvestigation, listBinaries, queryKeys } from '../api'
import { statusLabel, statusTone } from '../ui'

const PURPOSE = 'The question this investigation is asking, and any findings recorded so far.'

export function InvestigationDetail() {
  const { investigationId = '' } = useParams()
  const investigation = useQuery({
    queryKey: queryKeys.investigation(investigationId),
    queryFn: () => getInvestigation(investigationId),
    enabled: investigationId.length > 0,
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
      <dl className="grid gap-4 rounded-lg border border-gray-200 bg-white p-4 sm:grid-cols-2 dark:border-gray-700 dark:bg-gray-800">
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
      {record.findings.length === 0 ? (
        <EmptyState
          icon={ScanSearch}
          title="No findings yet"
          description="This workstation only classifies the sample and records the question you asked."
        />
      ) : (
        <ul className="space-y-2">
          {record.findings.map((finding, index) => (
            <li key={index} className="rounded-lg border border-gray-200 bg-white p-4 text-sm dark:border-gray-700 dark:bg-gray-800">
              {JSON.stringify(finding)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
