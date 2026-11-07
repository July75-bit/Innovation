/**
 * 白话导读：开发服务器 + 打包工具的配置文件（Vite）。
 *
 * plugins: vue() 让 .vue 文件能被识别；vueDevTools() 只在 npm run dev 时挂上 Vue 调试面板。
 * resolve.alias: 把 "@/xxx" 映射成 "src/xxx"，跨目录导入不用写 ../../../。
 *
 * 注意：本项目不在这里配 dev proxy，后端地址完全走环境变量 VITE_API_BASE_URL（见 src/api/client.ts），
 * 所以本地跨域问题要靠后端 CORS 放行 5173，而不是在这儿改。
 * npm run build 产出的静态文件在 dist/，部署到 Render Static Site。
 */

import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
