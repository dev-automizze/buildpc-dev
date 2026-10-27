import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // host: true makes the dev server reachable from another machine on the
    // LAN (useful when the backend/frontend runs on your Ubuntu home server).
    host: true,
    port: 5173,
  },
})
