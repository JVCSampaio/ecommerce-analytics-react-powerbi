import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// O build vai para ../docs, que o GitHub Pages publica direto da branch main (Settings → Pages → /docs).
// base relativo: funciona em https://<user>.github.io/<repo>/ sem configurar o nome do repo.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../docs',
    emptyOutDir: true,
    chunkSizeWarningLimit: 700,
  },
})
