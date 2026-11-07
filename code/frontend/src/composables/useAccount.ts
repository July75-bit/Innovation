/**
 * 白话导读：余额/总资产的"共享状态"，让每个页面看到的账户数字是同一份。
 *
 * 关键技巧：ref 定义在函数外面（模块级）。ES 模块只会被执行一次，
 * 所以 A 页面和 B 页面 import 这个文件拿到的是同一个 ref——改一处，所有页面同步更新。
 * 这就是本项目不用 Pinia 也能做状态管理的做法。
 *
 * 数字全部来自后端 GET /api/account：买入卖出成功后各页面会调 refreshAccount() 重新拉一次。
 */

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
