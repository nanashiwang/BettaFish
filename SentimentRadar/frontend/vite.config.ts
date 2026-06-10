import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// dev 用 '/' 配合 Vite 自带 SPA fallback；build 产物由 Flask /static/radar/ 服务
export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === 'build' ? '/static/radar/' : '/',
  build: {
    outDir: '../../static/radar',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5000',
    },
  },
}))
