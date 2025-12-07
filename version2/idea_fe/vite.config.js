import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/contract-gen',
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/apcontract': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: '../idea_be/static',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['framer-motion'],
          markdown: ['react-markdown', 'remark-gfm'],
        }
      }
    }
  },
  css: {
    postcss: './postcss.config.js',
  },
})
