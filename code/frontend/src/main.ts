/**
 * 白话导读：整个前端的总入口（入口文件），浏览器最终加载的就是它。
 *
 * 执行顺序：浏览器读 index.html → 看到 <script src="/src/main.ts"> → 运行这个文件
 *   1) 引入全局样式（CSS 变量、字体、配色都定义在 assets/main.css）；
 *   2) createApp(App)：把 App.vue 变成 Vue 应用；
 *   3) app.use(router)：装上路由（见 router/index.ts），URL 才能切换页面；
 *   4) mount("#app")：把界面渲染进 index.html 里那个空的 <div id="app">。
 *
 * 想找东西：页面加/删 → router/index.ts；改外壳布局 → App.vue；改全局配色 → assets/main.css。
 */

import './assets/main.css'

import { createApp } from 'vue'
import { API_BASE_URL } from './api/client'
import App from './App.vue'
import router from './router'
import { initTheme } from './composables/useTheme'
import { initGlassGlow } from './composables/useGlassGlow'

// 主题：index.html 已内联设置过一次（防闪），这里同步内存状态并处理"没存过"的情况
initTheme()
// 液态玻璃：桌面指针跟随高光（触屏/减少动效环境下自动不启用）
initGlassGlow()

/**
 * 连接预热：首屏就把到后端域名的 DNS/TLS 建好（跨域接口首包能省 0.2–0.6s，视网络）。
 * 后端地址来自 VITE_API_BASE_URL，没配置就跳过。
 */
function warmUpApiOrigin(): void {
  if (!API_BASE_URL || typeof document === 'undefined') return
  for (const rel of ['preconnect', 'dns-prefetch']) {
    const link = document.createElement('link')
    link.rel = rel
    link.href = API_BASE_URL
    link.crossOrigin = 'anonymous'
    document.head.appendChild(link)
  }
}

/**
 * 空闲预取：首屏稳定后把其余页面的 JS/CSS 分包下好（每个 3–20KB），
 * 切页时不用再等下载。requestIdleCallback 不可用时退回 1.2s 延时。
 */
function prefetchRouteChunks(): void {
  const warm = () => {
    void import('./views/PlayerDetailView.vue')
    void import('./views/PositionsView.vue')
    void import('./views/TradesView.vue')
    void import('./views/ScheduleView.vue')
  }
  const idle = window.requestIdleCallback
  if (typeof idle === 'function') idle(warm, { timeout: 2500 })
  else window.setTimeout(warm, 1200)
}

warmUpApiOrigin()

const app = createApp(App)

app.use(router)

app.mount('#app')
prefetchRouteChunks()
