import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      '.replit.dev',
      'localhost',
      '1460ab31-41da-45fa-91a9-9ffd94c55221-00-137nqi7ct3ozo.riker.replit.dev'
    ],
    hmr: {
      host: '0.0.0.0'
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
      },
    },
  },
})