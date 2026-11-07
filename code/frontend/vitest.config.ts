/**
 * 白话导读：单元测试配置。先继承 vite.config.ts，再追加测试相关设置。
 * environment: "jsdom" 最关键——在 Node 里模拟出一个假浏览器（有 document、localStorage），
 * 这样组件测试和"本地登录"这类依赖浏览器的逻辑才能在没有浏览器的环境下跑。
 * 跑测试：npm run test:unit；用例都在各目录的 __tests__ 文件夹里。
 */

import { fileURLToPath } from 'node:url'
import { mergeConfig, defineConfig, configDefaults } from 'vitest/config'
import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),
    },
  }),
)
