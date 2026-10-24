/**
 * 账户余额的共享状态（团队约定不装 Pinia，用模块级 ref 实现）。
 * 任何页面买入/卖出成功后都要调用 refreshAccount()，保证展示的余额
 * 永远来自后端（契约铁律：交易是否成功以后端数据库为准）。
 */
import { readonly, ref } from 'vue'
import { api } from '../api'
import type { Account } from '../api/types'

const accountState = ref<Account | null>(null)
const refreshing = ref(false)

export async function refreshAccount(): Promise<void> {
  refreshing.value = true
  try {
    accountState.value = await api.getAccount()
  } finally {
    refreshing.value = false
  }
}

export function useAccount() {
  return {
    /** 当前账户快照；首屏未加载时为 null，模板要判空 */
    account: readonly(accountState),
    refreshing: readonly(refreshing),
    refreshAccount,
  }
}
