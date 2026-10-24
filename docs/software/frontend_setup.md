# 前端脚手架与本地运行说明

> **负责人**：A ｜ **补充**：D（第 3 天补回该文件，对应 T1-04「把原脚手架 README 移到这里，别直接删」）
> **适用目录**：`code/frontend/` ｜ **技术栈**：Vue 3 + TypeScript + Vite（Router / Vitest / ESLint / Prettier）

## 1. 脚手架是怎么生成的

```powershell
cd D:\projects\innovation\Innovation
# 生成前 code/frontend/ 必须为空目录（原来的 README 已移走/或先备份）
npm create vue@latest code/frontend
#   TypeScript          Yes
#   JSX                 No
#   Vue Router          Yes
#   Pinia               No
#   Vitest              Yes
#   E2E                 No
#   ESLint              Yes
#   Prettier            Yes
```

生成后提交了 `package.json` / `package-lock.json` / `tsconfig*.json` / `vite.config.ts` / `vitest.config.ts` / `eslint.config.ts` 等。

## 2. 本地跑起来（前后端一起）

```powershell
# 1) 后端（另开终端）
cd D:\projects\innovation\Innovation
python scripts\seed_db.py                     # 建表 + 8 名选手 + demo 账户（幂等）
cd code\backend
python -m uvicorn app.main:app --reload --port 8000

# 2) 前端
cd D:\projects\innovation\Innovation\code\frontend
npm ci                                        # 依赖未入库，首次必须装
Copy-Item .env.example .env.local             # 本地地址模板；.env.local 已被 gitignore
npm run dev                                   # http://localhost:5173
```

前端默认 `VITE_USE_MOCK=false`，所有页面走真实后端；`VITE_USE_MOCK=true` 时切到 `src/mock/players.ts` 的内存数据（后端没起时的开发兜底）。

## 3. 目录与脚本

```text
src/
├── api/           # client.ts（fetch 封装）+ index.ts（接口函数）+ types.ts（契约类型）
├── components/    # TradePanel / PriceChart / LoadingState / EmptyState / ErrorState
├── composables/   # useAccount（余额共享状态）
├── mock/          # players.ts（VITE_USE_MOCK=true 时的内存数据）
├── router/        # / 市场、/players/:id 详情、/positions 持仓、/trades 流水
├── utils/         # format.ts（金额/百分比格式化）+ __tests__/format.spec.ts
├── views/         # MarketView / PlayerDetailView / PositionsView / TradesView
└── App.vue        # 顶部导航 + 余额/健康徽标 + 合规页脚
```

| 脚本 | 用途 |
| --- | --- |
| `npm run dev` | 本地开发（5173） |
| `npm run build` | `type-check` + 生产构建到 `dist/` |
| `npm run type-check` | `vue-tsc --build` |
| `npm run lint` | oxlint + eslint（带 `--fix`） |
| `npm run test:unit` | Vitest（`src/utils/__tests__/format.spec.ts`） |

## 4. 环境变量与硬约束

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端地址；**唯一来源**，代码里不允许出现写死的 `127.0.0.1`/`localhost:8000`（CI 有 grep 检查） |
| `VITE_USE_MOCK` | `true` 时全部接口切内存 mock；默认 `false` |

- 未配置 `VITE_API_BASE_URL` 时，`src/api/client.ts` 会明确报「未配置后端地址」，不会静默连错地址；
- 后端 CORS 默认放行 `http://localhost:5173` / `http://127.0.0.1:5173`（见 `code/backend/.env.example` 的 `CORS_ORIGINS`）。

## 5. 当前状态（2026-10-24）

- 页面/组件/路由/接口封装均已提交（A 的 `9782dc7`、`dbff9bd`）；
- **本工作区尚未 `npm ci`**：`node_modules` 不存在，所以“浏览器里跑通全链路”的运行证据仍待 A 补（对应 T1-06/T1-08、T3-02/T3-04）；
- 前端 `dist/` 也未生成，Render Static Site 部署要等 A 本地 `npm run build` 验证后再走第 5 天流程。
