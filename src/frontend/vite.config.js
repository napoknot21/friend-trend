import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

const envDir = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

function envBool(value, fallback) {
  if (value === undefined || value === null || value === '') {
    return fallback
  }
  return ['1', 'true', 'yes', 'on'].includes(String(value).trim().toLowerCase())
}

function envInt(value, fallback) {
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '')

  return {
    envDir,
    plugins: [vue()],
    server: {
      host: env.VITE_DEV_HOST || '127.0.0.1',
      port: envInt(env.VITE_DEV_PORT, 5173),
      open: envBool(env.VITE_DEV_OPEN, true),
    },
  }
})
