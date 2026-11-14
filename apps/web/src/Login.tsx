import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { ArrowRight, Lock, User } from 'lucide-react'
import { useAuth } from '@sgerhart/ux-framework/platform'
import lockup from '../../../noctivis-lockup.jpg'

export function Login() {
  const { login, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const requested = (location.state as { from?: string } | null)?.from
  const destination = requested && requested !== '/login' ? requested : '/'

  if (!isLoading && isAuthenticated) return <Navigate to={destination} replace />

  async function submit(event: FormEvent) {
    event.preventDefault()
    const name = username.trim()
    if (!name || !password) {
      setError('Enter your name and password.')
      return
    }
    setPending(true)
    setError(null)
    try {
      await login({ username: name, password } as never)
      navigate(destination, { replace: true })
    } catch (caught) {
      if (axios.isAxiosError(caught) && !caught.response) {
        setError('The local API is not responding.')
      } else {
        setError('That name or password is not valid.')
      }
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#030910] px-4 py-10">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,164,230,0.32),transparent_62%)]" />
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
          backgroundSize: '56px 56px',
        }}
      />
      <div className="relative w-full max-w-md">
        <section className="rounded-xl border border-[#00a6e8]/30 bg-[#071018]/90 px-8 py-10 shadow-[0_0_40px_rgba(0,166,232,0.12)]">
          <h1 className="sr-only">Sign in</h1>
          <img src={lockup} alt="Noctivis" className="mx-auto w-48 rounded-2xl" />
          <p className="mt-3 text-center text-[11px] font-medium tracking-[0.22em] text-[#7ec8e8] uppercase">
            Understand. Investigate. Defend.
          </p>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <label className="block text-sm font-medium text-slate-200">
              Username
              <span className="relative mt-1.5 block">
                <User className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-[#7ec8e8]" />
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  autoFocus
                  className="w-full rounded-md border border-[#1a4a66] bg-[#030910] py-2.5 pr-3 pl-10 text-sm text-white outline-none focus:border-[#00a6e8] focus:ring-1 focus:ring-[#00a6e8]"
                />
              </span>
            </label>
            <label className="block text-sm font-medium text-slate-200">
              Password
              <span className="relative mt-1.5 block">
                <Lock className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-[#7ec8e8]" />
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  className="w-full rounded-md border border-[#1a4a66] bg-[#030910] py-2.5 pr-3 pl-10 text-sm text-white outline-none focus:border-[#00a6e8] focus:ring-1 focus:ring-[#00a6e8]"
                />
              </span>
            </label>
            {error && (
              <p role="alert" className="text-sm text-red-300">
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={pending || isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#00a6e8] px-4 py-2.5 text-sm font-semibold text-[#041018] shadow-[0_0_24px_rgba(0,166,232,0.35)] hover:bg-[#1ec4ff] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {pending ? 'Signing in…' : 'Sign in'}
              {!pending && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>
        </section>
        <p className="mt-8 text-center text-sm text-[#7ec8e8]/80">Noctivis</p>
      </div>
    </main>
  )
}
