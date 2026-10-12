import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Forwards API calls to the FastAPI server during local development.
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
