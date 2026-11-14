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
import App from './App.vue'
import router from './router'
import { initTheme } from './composables/useTheme'
import { initGlassGlow } from './composables/useGlassGlow'

// 主题：index.html 已内联设置过一次（防闪），这里同步内存状态并处理"没存过"的情况
initTheme()
// 液态玻璃：桌面指针跟随高光（触屏/减少动效环境下自动不启用）
initGlassGlow()

const app = createApp(App)

app.use(router)

app.mount('#app')
