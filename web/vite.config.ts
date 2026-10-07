/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Permite que o container E2E acesse via hostname "web" (rede Docker)
    allowedHosts: ['web', 'localhost'],
    watch: {
      // O Docker Desktop no Windows não propaga eventos de inotify para
      // bind mounts; sem polling, o Vite nunca percebe um arquivo mudado.
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/tests/setup.ts'],
    // Exclui specs do Playwright — rodados separadamente via npx playwright test
    exclude: ['e2e/**', 'node_modules/**'],
  },
})
