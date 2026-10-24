/**
 * 统一 fetch 封装。
 *
 * - 后端地址只从环境变量 VITE_API_BASE_URL 读取（不写死，线上部署会改）；
 * - 4xx/5xx 一律解析统一错误体 { success:false, message, code }（契约 §2）；
 * - message 可直接展示给用户，前端不写错误码映射表；
 * - 业务失败（如余额不足）按 code 提示即可，**不要自动重试**（契约 §4.7：重试会变成第二笔真实交易）。
 */
import type { ApiErrorBody } from './types'

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
      '未配置后端地址：请在 .env.local 填写 VITE_API_BASE_URL（参考 .env.example）',
      'MISSING_API_BASE_URL',
      0,
    )
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(
      `无法连接后端服务（当前地址：${API_BASE_URL}），请确认后端已启动`,
      'NETWORK_ERROR',
      0,
    )
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
