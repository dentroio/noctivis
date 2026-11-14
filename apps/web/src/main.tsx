import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary, ThemeProvider, ToastProvider } from '@sgerhart/ux-framework'
import { AuthProvider } from '@sgerhart/ux-framework/platform'
import mark from '../../../noctivis.png'
import { App } from './App'
import { authAdapter } from './auth'
import './index.css'

const icon = document.createElement('link')
icon.rel = 'icon'
icon.type = 'image/png'
icon.href = mark
document.head.appendChild(icon)

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false } },
})

const root = document.getElementById('root')
if (!root) throw new Error('Root element is missing')

createRoot(root).render(
  <StrictMode>
    <ErrorBoundary onError={(error) => console.error(error)}>
      <ThemeProvider storageKey="noctivis-theme">
        <ToastProvider>
          <QueryClientProvider client={queryClient}>
            <AuthProvider adapter={authAdapter} roles={['operator']}>
              <BrowserRouter>
                <App />
              </BrowserRouter>
            </AuthProvider>
          </QueryClientProvider>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
)
