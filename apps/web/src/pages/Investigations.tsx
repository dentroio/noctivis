import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ScanSearch } from 'lucide-react'
import { DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, useToast, type Column } from '@sgerhart/ux-framework'
import {
  createInvestigation,
  errorDetail,
  listBinaries,
  listInvestigations,
  queryKeys,
  type Investigation,
} from '../api'
import { inputClass, primaryButtonClass, statusLabel, statusTone } from '../ui'

const PURPOSE = 'Questions you have asked about a classified sample. The sample itself is not executed.'

export function Investigations() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const binaries = useQuery({ queryKey: queryKeys.binaries, queryFn: listBinaries })
  const investigations = useQuery({ queryKey: queryKeys.investigations, queryFn: listInvestigations })
  const [binaryId, setBinaryId] = useState('')
  const [objective, setObjective] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const selectedId = binaryId || binaries.data?.[0]?.id || ''

  const create = useMutation({
    mutationFn: (input: { binaryId: string; objective: string }) => createInvestigation(input.binaryId, input.objective),
    onSuccess: async (investigation) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.investigations })
      setObjective('')
      setFormError(null)
      toast.success('Investigation created')
      navigate(`/investigations/${investigation.id}`)
    },
    onError: (error) => setFormError(errorDetail(error)),
  })

  const columns: Column<Investigation>[] = [
    {
      id: 'objective',
      header: 'Objective',
      cell: (row) => <span className="font-medium">{row.objective}</span>,
    },
    {
      id: 'status',
      header: 'Status',
      cell: (row) => <StatusBadge tone={statusTone(row.status)}>{statusLabel(row.status)}</StatusBadge>,
    },
    {
      id: 'sample',
      header: 'Sample',
      cell: (row) => {
        const sample = binaries.data?.find((item) => item.id === row.binary_id)
        return sample ? sample.label : <span className="font-mono text-xs">{row.binary_id.slice(0, 12)}</span>
      },
    },
  ]

  function submit(event: FormEvent) {
    event.preventDefault()
    const text = objective.trim()
    if (!selectedId) {
      setFormError('Classify a sample before starting an investigation.')
      return
    }
    if (text.length < 3) {
      setFormError('Describe the objective in at least a few words.')
      return
    }
    if (text.length > 2000) {
      setFormError('The objective must be 2000 characters or fewer.')
      return
    }
    setFormError(null)
    create.mutate({ binaryId: selectedId, objective: text })
  }

  const failed = binaries.isError ? binaries : investigations.isError ? investigations : null

  return (
    <div className="space-y-6">
      <PageHeader title="Investigations" purpose={PURPOSE} />
      {(binaries.isLoading || investigations.isLoading) && <LoadingState message="Loading investigations…" />}
      {failed && (
        <ErrorState
          title="Could not load investigations"
          message="The local API did not return investigations. Try again."
          detail={errorDetail(failed.error)}
          retryAction={{
            label: 'Try again',
            onClick: () => {
              void binaries.refetch()
              void investigations.refetch()
            },
          }}
        />
      )}
      {binaries.isSuccess && investigations.isSuccess && binaries.data.length === 0 && (
        <EmptyState
          icon={ScanSearch}
          title="No samples to investigate"
          description="Classify a sample first. Investigations stay tied to that classification."
          action={{ label: 'Classify a sample', href: '/binaries' }}
        />
      )}
      {binaries.isSuccess && investigations.isSuccess && binaries.data.length > 0 && (
        <form onSubmit={submit} className="space-y-3 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
            Sample
            <select className={`${inputClass} mt-1`} value={selectedId} onChange={(event) => setBinaryId(event.target.value)}>
              {binaries.data.map((binary) => (
                <option key={binary.id} value={binary.id}>
                  {binary.label} · {binary.format} · {binary.sha256.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
            Objective
            <textarea
              className={`${inputClass} mt-1`}
              rows={3}
              value={objective}
              maxLength={2000}
              onChange={(event) => setObjective(event.target.value)}
              placeholder="What do you want to learn about this sample?"
            />
          </label>
          <button type="submit" className={primaryButtonClass} disabled={create.isPending}>
            {create.isPending ? 'Creating…' : 'Start investigation'}
          </button>
        </form>
      )}
      {formError && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {formError}
        </p>
      )}
      {investigations.isSuccess && binaries.isSuccess && binaries.data.length > 0 && investigations.data.length === 0 && (
        <EmptyState
          icon={ScanSearch}
          title="No investigations yet"
          description="Describe what you want to learn about a sample. The sample is not executed."
        />
      )}
      {investigations.isSuccess && investigations.data.length > 0 && (
        <DataTable
          columns={columns}
          rows={investigations.data}
          rowKey={(row) => row.id}
          columnStorageKey="noctivis-investigations"
          caption="Investigations"
          onRowClick={(row) => navigate(`/investigations/${row.id}`)}
        />
      )}
    </div>
  )
}
