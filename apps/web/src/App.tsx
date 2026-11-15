import { useMemo } from 'react'
import { Route, Routes, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Binary, Cpu, Files, Gauge, Moon, ScanSearch } from 'lucide-react'
import {
  AppShell,
  Banner,
  CommandPalette,
  EmptyState,
  type NavSection,
  type SearchProvider,
} from '@sgerhart/ux-framework'
import { PrivateRoute, useAuth } from '@sgerhart/ux-framework/platform'
import headerMark from '../../../left_header_pic.png'
import { listBinaries, listInvestigations, queryKeys } from './api'
import { Login } from './Login'
import { Binaries } from './pages/Binaries'
import { Capabilities } from './pages/Capabilities'
import { InvestigationDetail } from './pages/InvestigationDetail'
import { Investigations } from './pages/Investigations'
import { Models } from './pages/Models'
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
  {
    label: 'Connect',
    items: [{ name: 'Models', href: '/models', icon: Cpu }],
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

export function Console() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
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
        <button type="button" onClick={() => navigate('/')} className="flex items-center">
          <img src={headerMark} alt="Noctivis" className="h-14 w-auto" />
        </button>
      }
      user={user ? { name: user.name, role: 'Operator' } : null}
      onLogout={() => void logout()}
      status={status}
      storageKey="noctivis"
      breadcrumb={{
        labels: {
          '': 'Overview',
          investigations: 'Investigations',
          binaries: 'Binaries',
          capabilities: 'Capabilities',
          models: 'Models',
        },
      }}
      headerActions={<CommandPalette providers={providers} placeholder="Search investigations and samples…" />}
      banners={
        <Banner tone="warning">
          This session is one local operator. Samples are stored by hash and never executed.
        </Banner>
      }
    >
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:investigationId" element={<InvestigationDetail />} />
        <Route path="/binaries" element={<Binaries />} />
        <Route path="/capabilities" element={<Capabilities />} />
        <Route path="/models" element={<Models />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  )
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Console />
          </PrivateRoute>
        }
      />
    </Routes>
  )
}
