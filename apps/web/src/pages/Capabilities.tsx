import { useQuery } from '@tanstack/react-query'
import { DataTable, ErrorState, LoadingState, PageHeader, StatusBadge, type Column } from '@sgerhart/ux-framework'
import { errorDetail, listCapabilities, queryKeys, type Capability } from '../api'

const PURPOSE = 'Which analysis this workstation can run, and whether any of it executes a sample.'

export function Capabilities() {
  const capabilities = useQuery({ queryKey: queryKeys.capabilities, queryFn: listCapabilities })
  const columns: Column<Capability>[] = [
    { id: 'id', header: 'Capability', cell: (row) => <span className="font-medium">{row.id}</span> },
    { id: 'description', header: 'What it does', cell: (row) => row.description },
    {
      id: 'tools',
      header: 'Tools',
      cell: (row) => <span className="font-mono text-xs">{row.tools.join(', ')}</span>,
    },
    {
      id: 'execution',
      header: 'Execution',
      cell: (row) => (
        <StatusBadge tone={row.allows_execution ? 'danger' : 'neutral'}>
          {row.allows_execution ? 'Executes samples' : 'Does not execute'}
        </StatusBadge>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Capabilities"
        purpose={PURPOSE}
        stateChip={
          capabilities.isSuccess
            ? capabilities.data.some((item) => item.allows_execution)
              ? { label: 'Execution enabled', variant: 'warning' }
              : { label: 'Execution off', variant: 'healthy' }
            : undefined
        }
      />
      {capabilities.isLoading && <LoadingState message="Loading capabilities…" />}
      {capabilities.isError && (
        <ErrorState
          title="Could not load capabilities"
          message="The local API did not return the capability list. Try again."
          detail={errorDetail(capabilities.error)}
          retryAction={{ label: 'Try again', onClick: () => void capabilities.refetch() }}
        />
      )}
      {capabilities.isSuccess && (
        <DataTable
          columns={columns}
          rows={capabilities.data}
          rowKey={(row) => row.id}
          columnStorageKey="noctivis-capabilities"
          caption="Capabilities"
          empty={{ title: 'No capabilities registered', description: 'This workstation has no analysis packages loaded.' }}
        />
      )}
    </div>
  )
}
