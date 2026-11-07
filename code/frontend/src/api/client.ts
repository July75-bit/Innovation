/**
 * 白话导读：全项目唯一直接调用后端的地方（网络层底座）。
 *
 * 通俗理解：它是一个"传送门"，页面说什么路径，它就 fetch 什么路径，然后把后端返回的 JSON 交出去。
 * 它额外干三件事：
 *   1) 后端地址来自环境变量 VITE_API_BASE_URL（不写死在代码里，本地/线上切换只改 .env）；
 *   2) 失败时把后端的错误 JSON 转成 ApiError 对象，message 是中文、可直接弹给用户；
 *   3) 网络断了 / 后端没起 / 地址没配，也统一转成能看懂的中文错误，页面不会白屏。
 *
 * 下面的注释里出现"契约"= docs/software/api_contract.md（前后端约定的接口说明书）。
 * 要看具体接口怎么调用，去 src/api/index.ts。
 */

/**
 * 统一 fetch 封装。
 *
 * - 后端地址只从环境变量 VITE_API_BASE_URL 读取，**代码里不出现任何具体地址**
 *   （day2 翻车点 #5：源码里不允许出现任何字面的本地地址）；
 * - 4xx/5xx 一律解析统一错误体 { success:false, message, code }（契约 §2）；
 * - message 可直接展示给用户，前端不写错误码映射表；
 * - 业务失败（如余额不足）按 code 提示即可，**不要自动重试**（契约 §4.7：重试会变成第二笔真实交易）。
 */
import { getToken } from './token'
import type { ApiErrorBody } from './types'

/** 未配置时为空串，request() 会给出明确报错，绝不回退到写死的地址 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

/** 网络层 / 业务层统一错误：message 直接给用户看，code 用于程序判断 */
export class ApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiError(
      '未配置后端地址：请在 code/frontend/.env.local 中设置 VITE_API_BASE_URL（参考 .env.example）',
      'CONFIG_MISSING',
      0,
    )
  }

  let response: Response
  try {
    // 仅带 body 的请求（POST 交易）才声明 Content-Type：
    // GET 不带该头 = CORS 简单请求，不触发 OPTIONS 预检，缩小跨域故障面（day5 线上走查 P2 改进）。
    const headers: Record<string, string> = {
      ...(init?.headers as Record<string, string> | undefined),
    }
    if (init?.body != null) headers['Content-Type'] = 'application/json'
    // 私人账号（第 7 轮）：本地有令牌就带上，后端据此把余额/持仓/流水落到该账号上。
    // 没令牌时**不加这个头**——后端把"没带 Authorization"识别为公共演示账户，
    // 这正是"未登录访客"与"令牌失效"的分界（后者后端回 401，useAuth 会清会话）。
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('无法连接后端服务，请确认后端已启动后重试', 'NETWORK_ERROR', 0)
  }

  let data: unknown = null
  try {
    data = await response.json()
  } catch {
    // 非 JSON 响应（如网关 HTML），按状态码兜底
  }

  if (!response.ok) {
    const body = data as Partial<ApiErrorBody> | null
    throw new ApiError(
      body?.message ?? `请求失败（HTTP ${response.status}），请稍后再试`,
      body?.code ?? 'INTERNAL_ERROR',
      response.status,
    )
  }

  return data as T
}
