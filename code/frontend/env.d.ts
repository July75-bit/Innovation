/**
 * 白话导读：给编辑器/类型检查看的"环境变量声明"，没有任何运行代码。
 *
 * Vite 的约定：只有以 VITE_ 开头的变量才会被塞进前端代码（import.meta.env.VITE_XXX）。
 * 这个文件把这两个变量声明出来，写 import.meta.env.VITE_API_BASE_URL 时才有补全、也不会报类型错误。
 * 实际取值来自 .env.local（本地）/ Render 环境变量（线上），见 README「环境变量」一节。
 */

/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 地址；本地值见 .env.example，线上由部署环境变量注入（契约 §1） */
  readonly VITE_API_BASE_URL?: string
  /** 'true' 时使用 src/mock 的本地模拟数据（后端未就绪时的开发兜底）；其余值走真实接口 */
  readonly VITE_USE_MOCK?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
