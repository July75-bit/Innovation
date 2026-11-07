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

/** 路由约定见原 code/frontend/README.md：/ 市场、/players/:id 详情、/positions 持仓、/trades 流水 */
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
    // 兜底：任何拼错/过期的路径都回首页。空白页比 404 更像"坏了"，
    // 答辩现场手一抖输错地址不至于看起来像站点挂了。
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

/**
 * 登录态守卫。
 *
 * 放行条件写宽一点：登录用户和「访客进入」都算可以逛（`isAuthenticated`），
 * 否则本地演示时没注册账号的人连界面都看不到，反而像 bug。
 * 未登录时把原路径放进 ?redirect=，登录成功再送回他本来要去的那一页。
 */
router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()

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
