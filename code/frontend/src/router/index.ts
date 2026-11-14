/**
 * 白话导读：浏览器地址栏 URL ↔ 页面组件 的对应表，外加"没登录就赶去登录页"的守门逻辑。
 *
 * routes 数组怎么读：path 是地址，component 是页面文件，() => import(...) 是懒加载
 * （第一次访问该页才下载它的代码，首屏更快）。目前 6 个页面：/auth、/、/players/:id、/positions、/trades、/schedule。
 *
 * beforeEach = 全局前置守卫：每次换页前跑一遍，看 useAuth 里的登录态决定放行还是跳登录页。
 * 想加新页面：在 routes 里加一条，再去 App.vue 的侧栏导航加个链接。
 */

import { createRouter, createWebHistory } from 'vue-router'
import MarketView from '../views/MarketView.vue'
import { useAuth } from '../composables/useAuth'

/** 登录页自带全屏背景，路由 meta 用来告诉外壳"这一页不套侧栏" */
declare module 'vue-router' {
  interface RouteMeta {
    /** true = 不需要登录态就能访问（目前只有 /auth） */
    public?: boolean
    /** 浏览器标题 */
    title?: string
  }
}

/** 路由约定见原 code/frontend/README.md：/ 市场、/players/:id 详情、/positions 持仓、/trades 流水、/schedule 赛程 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 注册 / 登录：本地演示页，纯前端账号态，不发后端请求（见 composables/useAuth.ts）
    {
      path: '/auth',
      name: 'auth',
      component: () => import('../views/AuthView.vue'),
      meta: { public: true, title: '登录 / 注册' },
    },
    {
      path: '/',
      name: 'market',
      component: MarketView,
    },
    // 市场页的正经路径是 `/`，但 `/market` 太容易被手输/收藏/写进文档。
    // 没有这条时 vue-router 匹配不到组件、又没有兜底，页面会**白屏但不报错**
    // （静态站 rewrite 把 /market 也返回 index.html，所以连 404 都没有）。
    {
      path: '/market',
      redirect: '/',
    },
    {
      path: '/players/:id',
      name: 'player-detail',
      component: () => import('../views/PlayerDetailView.vue'),
    },
    {
      path: '/positions',
      name: 'positions',
      component: () => import('../views/PositionsView.vue'),
    },
    {
      path: '/trades',
      name: 'trades',
      component: () => import('../views/TradesView.vue'),
    },
    // 赛程（第 8 天新增）：展示"赛程 → 队伍级暂停 → 点数"的派生算法本身，
    // 数据来自 src/data/demoSchedule.ts，规则来自 src/core/schedule.ts
    {
      path: '/schedule',
      name: 'schedule',
      component: () => import('../views/ScheduleView.vue'),
    },
    // 兜底：任何拼错/过期的路径都回首页。空白页比 404 更像"坏了"，
    // 答辩现场手一抖输错地址不至于看起来像站点挂了。
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

/**
 * 登录态守卫（第 7 轮起：身份由后端令牌决定）。
 *
 * 三件事按顺序做：
 * 1. `await bootstrap()` —— 首屏拿本地令牌问一次 /api/auth/me，把身份恢复出来。
 *    这一步必须在放行判断**之前**，否则刷新后第一屏会被误判成未登录、闪一下弹回登录页。
 * 2. 放行条件写宽一点：私人账号和「访客进入」都算可以逛（`isAuthenticated`），
 *    否则没注册过的人连界面都看不到，反而像 bug。
 * 3. 未登录时把原路径放进 ?redirect=，登录成功再送回他本来要去的那一页。
 */
router.beforeEach(async (to) => {
  const { isAuthenticated, bootstrap } = useAuth()
  await bootstrap()

  if (to.meta.public) {
    // 已经进来了还去登录页 = 想退出/换号，直接给过；
    // 但正常访问（比如手输 /auth）时把已登录用户送回市场页，避免来回弹。
    if (to.name === 'auth' && isAuthenticated.value && !to.query.redirect) return { path: '/' }
    return true
  }

  if (!isAuthenticated.value) {
    return { name: 'auth', query: to.fullPath === '/' ? {} : { redirect: to.fullPath } }
  }
  return true
})

export default router
