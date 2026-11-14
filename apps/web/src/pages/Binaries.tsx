import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Binary } from 'lucide-react'
import { DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, useToast, type Column } from '@sgerhart/ux-framework'
import { errorDetail, listBinaries, MAX_UPLOAD_BYTES, queryKeys, uploadBinary, type BinaryRecord } from '../api'
import { formatBytes, inputClass, panelClass, primaryButtonClass } from '../ui'

const PURPOSE = 'Samples classified on this workstation. The file is hashed and then deleted. Nothing is executed.'

export function Binaries() {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const binaries = useQuery({ queryKey: queryKeys.binaries, queryFn: listBinaries })
  const [file, setFile] = useState<File | null>(null)
  const [inputKey, setInputKey] = useState(0)
  const [formError, setFormError] = useState<string | null>(null)
  const upload = useMutation({
    mutationFn: uploadBinary,
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.binaries })
      setFile(null)
      setInputKey((key) => key + 1)
      setFormError(null)
      toast.success(`${record.label} classified as ${record.format}`)
    },
    onError: (error) => setFormError(errorDetail(error)),
  })

  const columns: Column<BinaryRecord>[] = [
    { id: 'label', header: 'Name', cell: (row) => <span className="font-medium">{row.label}</span> },
    { id: 'format', header: 'Format', cell: (row) => <StatusBadge tone="neutral">{row.format}</StatusBadge> },
    { id: 'size', header: 'Size', numeric: true, cell: (row) => formatBytes(row.size_bytes) },
    {
      id: 'sha',
      header: 'SHA-256',
      cell: (row) => <span className="font-mono text-xs break-all">{row.sha256}</span>,
    },
  ]

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!file) {
      setFormError('Choose a sample to classify.')
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setFormError('That sample is over the 20 MB limit.')
      return
    }
    setFormError(null)
    upload.mutate(file)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Binaries" purpose={PURPOSE} />
      <form onSubmit={submit} className={`flex flex-col gap-3 p-4 sm:flex-row sm:items-end ${panelClass}`}>
        <label className="block flex-1 text-sm font-medium text-gray-700 dark:text-gray-200">
          Sample file
          <input
            key={inputKey}
            type="file"
            className={`${inputClass} mt-1`}
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null)
              setFormError(null)
            }}
          />
        </label>
        <button type="submit" className={primaryButtonClass} disabled={upload.isPending}>
          {upload.isPending ? 'Classifying…' : 'Classify sample'}
        </button>
      </form>
      {formError && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {formError}
        </p>
      )}
      {binaries.isLoading && <LoadingState message="Loading samples…" />}
      {binaries.isError && (
        <ErrorState
          title="Could not load samples"
          message="The local API did not return the sample list. Try again."
          detail={errorDetail(binaries.error)}
          retryAction={{ label: 'Try again', onClick: () => void binaries.refetch() }}
        />
      )}
      {binaries.isSuccess && binaries.data.length === 0 && (
        <EmptyState
          icon={Binary}
          title="No samples yet"
          description="Choose a file above. It is classified from its header, then deleted. Nothing is executed."
        />
      )}
      {binaries.isSuccess && binaries.data.length > 0 && (
        <DataTable columns={columns} rows={binaries.data} rowKey={(row) => row.id} columnStorageKey="noctivis-binaries" caption="Classified samples" />
      )}
    </div>
  )
}
