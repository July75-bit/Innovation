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
