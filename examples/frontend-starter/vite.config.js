import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    '__BUILD_TIME__': JSON.stringify('20251108115259')
  }
})
