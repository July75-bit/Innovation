/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 地址；本地开发复制 .env.example 为 .env.local 填写，线上由部署环境注入（契约 §1） */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
