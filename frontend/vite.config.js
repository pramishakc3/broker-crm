import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, /api requests are proxied to the FastAPI backend.
// API_PROXY_TARGET lets docker-compose point at the backend container.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': process.env.API_PROXY_TARGET || 'http://localhost:8000',
    },
  },
})
