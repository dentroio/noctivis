import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ErrorState, LoadingState, PageHeader } from '@sgerhart/ux-framework'
import { errorDetail, getHealth, listBinaries, listCapabilities, listInvestigations, queryKeys } from '../api'
import { panelClass } from '../ui'

const PURPOSE = 'What is on this workstation, and whether the local API is responding.'

export function Overview() {
  const health = useQuery({ queryKey: queryKeys.health, queryFn: getHealth })
  const binaries = useQuery({ queryKey: queryKeys.binaries, queryFn: listBinaries })
  const investigations = useQuery({ queryKey: queryKeys.investigations, queryFn: listInvestigations })
  const capabilities = useQuery({ queryKey: queryKeys.capabilities, queryFn: listCapabilities })
  const queries = [health, binaries, investigations, capabilities]
  const failed = queries.find((query) => query.isError)
  const updatedAt = Math.max(...queries.map((query) => query.dataUpdatedAt))

  if (queries.some((query) => query.isLoading)) {
    return (
      <div className="space-y-6">
        <PageHeader title="Overview" purpose={PURPOSE} />
        <LoadingState message="Loading this workstation…" />
      </div>
    )
  }

  if (failed) {
    return (
      <div className="space-y-6">
        <PageHeader title="Overview" purpose={PURPOSE} stateChip={{ label: 'API unreachable', variant: 'error' }} />
        <ErrorState
          title="Could not reach the local API"
          message="Start the API on this machine, then try again."
          detail={errorDetail(failed.error)}
          retryAction={{
            label: 'Try again',
            onClick: () => {
              void health.refetch()
              void binaries.refetch()
              void investigations.refetch()
              void capabilities.refetch()
            },
          }}
        />
      </div>
    )
  }

  const cards = [
    ['Samples', String(binaries.data?.length ?? 0), 'Classified and then deleted', '/binaries'],
    ['Investigations', String(investigations.data?.length ?? 0), 'Questions recorded against a sample', '/investigations'],
    ['Capabilities', String(capabilities.data?.length ?? 0), 'Analysis this workstation can run', '/capabilities'],
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Overview"
        purpose={PURPOSE}
        stateChip={{ label: 'Local API responding', variant: 'healthy' }}
        lastUpdated={updatedAt > 0 ? new Date(updatedAt) : null}
      />
      <div className="grid gap-4 sm:grid-cols-3">
        {cards.map(([label, value, hint, href]) => (
          <Link
            key={href}
            to={href}
            className={`${panelClass} p-4 hover:border-brand`}
          >
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300">{label}</div>
            <div className="mt-1 text-3xl font-bold tabular-nums text-gray-900 dark:text-gray-100">{value}</div>
            <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">{hint}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
