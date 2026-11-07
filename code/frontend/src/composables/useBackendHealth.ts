/**
 * 白话导读：侧栏那个"连接成功 / 后端未连接"小圆点的数据来源。
 *
 * 调 GET /api/health 一次，把结果存在模块级 ref 里，所有页面共享。
 * 各页面点"刷新"时会顺带再检测一次，所以后端起来后徽标会自动变绿，不用手动折腾。
 * 它只负责显示，接口失败也不会抛错打断页面主流程。
 */

/**
 * 后端连接状态的共享检测（顶栏徽标）。
 * 各页面 load() 时顺带触发一次，保证"重试/刷新成功后徽标同步恢复"。
 */
import { readonly, ref } from 'vue'
import { api } from '../api'

const service = ref<string | null | false>(null)

export async function checkBackendHealth(): Promise<void> {
  try {
    service.value = (await api.health()).service
  } catch {
    service.value = false
  }
}

export function useBackendHealth() {
  return { service: readonly(service), checkBackendHealth }
}
