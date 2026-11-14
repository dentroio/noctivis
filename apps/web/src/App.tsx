import { useMemo } from 'react'
import { Route, Routes, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Binary, Files, Gauge, Moon, ScanSearch } from 'lucide-react'
import {
  AppShell,
  Banner,
  CommandPalette,
  EmptyState,
  type NavSection,
  type SearchProvider,
} from '@sgerhart/ux-framework'
import { listBinaries, listInvestigations, queryKeys } from './api'
import { Binaries } from './pages/Binaries'
import { Capabilities } from './pages/Capabilities'
import { InvestigationDetail } from './pages/InvestigationDetail'
import { Investigations } from './pages/Investigations'
import { Overview } from './pages/Overview'

const NAV: NavSection[] = [
  { items: [{ name: 'Overview', href: '/', icon: Gauge }] },
  {
    label: 'Investigate',
    items: [
      { name: 'Investigations', href: '/investigations', icon: ScanSearch },
      { name: 'Binaries', href: '/binaries', icon: Binary },
    ],
  },
  {
    label: 'Understand',
    items: [{ name: 'Capabilities', href: '/capabilities', icon: Files }],
  },
]

function NotFound() {
  return (
    <EmptyState
      icon={Moon}
      title="Page not found"
      description="That page is not part of this console."
      action={{ label: 'Back to overview', href: '/' }}
    />
  )
}

export function App() {
  const navigate = useNavigate()
  const healthTone = useQuery({
    queryKey: queryKeys.health,
    queryFn: async () => {
      const response = await fetch('/health')
      if (!response.ok) throw new Error(`Health check failed (${response.status})`)
      return response.json() as Promise<{ status: string }>
    },
  })
  const binaries = useQuery({ queryKey: queryKeys.binaries, queryFn: listBinaries })
  const investigations = useQuery({ queryKey: queryKeys.investigations, queryFn: listInvestigations })

  const providers = useMemo<SearchProvider[]>(
    () => [
      {
        label: 'Investigations',
        icon: ScanSearch,
        search: (query) =>
          (investigations.data ?? [])
            .filter((item) => item.objective.toLowerCase().includes(query.toLowerCase()))
            .map((item) => ({
              id: item.id,
              label: item.objective,
              sub: item.status,
              href: `/investigations/${item.id}`,
            })),
      },
      {
        label: 'Samples',
        icon: Binary,
        search: (query) =>
          (binaries.data ?? [])
            .filter((item) => `${item.label} ${item.format} ${item.sha256}`.toLowerCase().includes(query.toLowerCase()))
            .map((item) => ({
              id: item.id,
              label: item.label,
              sub: item.format,
              href: '/binaries',
            })),
      },
    ],
    [binaries.data, investigations.data],
  )

  const status = healthTone.isLoading
    ? { tone: 'loading' as const, label: 'Checking the local API' }
    : healthTone.isError
      ? { tone: 'critical' as const, label: 'API unreachable' }
      : { tone: 'healthy' as const, label: 'Local API responding' }

  return (
    <AppShell
      nav={NAV}
      brand={
        <button type="button" onClick={() => navigate('/')} className="flex items-center gap-2 text-lg font-bold tracking-wide text-brand dark:text-gray-100">
          <Moon className="h-5 w-5" />
          NOCTIVIS
        </button>
      }
      status={status}
      storageKey="noctivis"
      breadcrumb={{
        labels: {
          '': 'Overview',
          investigations: 'Investigations',
          binaries: 'Binaries',
          capabilities: 'Capabilities',
        },
      }}
      headerActions={<CommandPalette providers={providers} placeholder="Search investigations and samples…" />}
      banners={
        <Banner tone="warning">
          This console has no sign-in. It talks only to the API on this machine. Samples are classified and deleted, never executed.
        </Banner>
      }
    >
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:investigationId" element={<InvestigationDetail />} />
        <Route path="/binaries" element={<Binaries />} />
        <Route path="/capabilities" element={<Capabilities />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  )
}
