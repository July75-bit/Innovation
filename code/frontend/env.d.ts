/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端 API 地址；本地默认 http://127.0.0.1:8000，线上由部署环境注入（契约 §1） */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
