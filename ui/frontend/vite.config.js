import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { webcrypto } from 'node:crypto'

// Ensure crypto is available globally before Vite config is resolved
if (typeof globalThis.crypto === 'undefined' || !globalThis.crypto.getRandomValues) {
  globalThis.crypto = webcrypto
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  resolve: {
    alias: {
      // Ensure Vite uses Node's crypto
    }
  }
})

