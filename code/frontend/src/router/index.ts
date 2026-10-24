import { createRouter, createWebHistory } from 'vue-router'
import MarketView from '../views/MarketView.vue'

/** 路由约定见原 code/frontend/README.md：/ 市场、/players/:id 详情、/positions 持仓、/trades 流水 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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

export default router
