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
  ],
})

export default router
