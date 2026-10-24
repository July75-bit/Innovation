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
