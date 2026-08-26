import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    // externalizeDeps is automatically handled here in v5+
  },
  preload: {
    // externalizeDeps is automatically handled here in v5+
  },
  renderer: {
    server: {
      port: 5173, // Your locked local port
      strictPort: true
    },
    plugins: [react()]
  }
})
