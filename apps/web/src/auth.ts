import { createApiClient, createBearerAdapter, createTokenStore } from '@sgerhart/ux-framework/platform'

export const tokens = createTokenStore('noctivis')

export const api = createApiClient({
  tokens,
  loginPath: '/login',
})

export const authAdapter = createBearerAdapter({
  api,
  tokens,
  loginPath: '/api/v1/auth/login',
  mePath: '/api/v1/auth/me',
  logoutPath: '/api/v1/auth/logout',
})
