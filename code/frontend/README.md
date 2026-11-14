# code/frontend —— PlayerStock 前端（A 同学负责）

Vue 3 + TypeScript + Vite，由官方脚手架 `npm create vue@latest` 生成
（选项：TypeScript=Yes / JSX=No / Vue Router=Yes / Pinia=No / Vitest=Yes / E2E=No / ESLint+Prettier=Yes）。

> **第一次读这个目录？** 先看 [docs/前端代码导读.md](docs/前端代码导读.md)：
> 每个文件在做什么、一次点击的数据怎么流到后端、注释里的项目黑话（契约 §4.2 / day3 / A4 / TC-405）怎么翻译。
> 各源文件开头也有一段「白话导读」注释，可直接在编辑器里看。

## 运行

```powershell
cd code/frontend
npm install                  # 首次或依赖变化时
Copy-Item .env.example .env.local   # 每台机器首次执行一次（.env.local 不入库，新克隆没有）
npm run dev                  # http://localhost:5173（后端 CORS 默认放行该源）
```

常用脚本：`npm run type-check`、`npm run lint`、`npm run format`、`npm run test:unit`、`npm run build`（产物 `dist/`，Render Static Site 用）。

## 环境变量（必须，不许写死地址）

| 文件 | 用途 |
| --- | --- |
| `.env.example` | 模板：`VITE_API_BASE_URL=http://127.0.0.1:8000` + `VITE_USE_MOCK=false` |
| `.env.local` | 本地实际值（已被 .gitignore 忽略，新克隆后从 example 复制） |
| Render 环境变量 | 第 5 天部署时注入线上后端地址 |

代码统一从 `import.meta.env.VITE_API_BASE_URL` 读取（封装在 `src/api/client.ts`，代码里 grep 不到任何具体地址——未配置时页面会明确报"未配置后端地址"）。

**Mock 开关（day2 T2 产出物）**：`VITE_USE_MOCK=true` 时全部接口切到 `src/mock/players.ts`
的内存模拟数据（数据逐字来自 `data/seed_players.json`，含 50 股上限/暂停交易/余额与持仓校验，
刷新页面即重置），供后端未就绪时开发演示；**联调与上线必须为 `false`**。

## 结构

```text
src/
├── api/
│   ├── types.ts       # 契约 §4 全部响应类型（snake_case，不做驼峰转换）
│   ├── client.ts      # fetch 封装：环境变量、统一错误体、有令牌时自动带 Authorization
│   ├── token.ts       # 访问令牌存放处（localStorage / sessionStorage，client.ts 读它）
│   └── index.ts       # 14 个业务接口函数（api.listPlayers / api.buy / api.register / ...）
├── mock/
│   ├── players.ts   # VITE_USE_MOCK=true 时的内存模拟数据（含交易校验，仅开发兜底）
│   └── auth.ts      # VITE_USE_MOCK=true 时的假登录（与后端同规则，避免"行情假、登录真"）
├── assets/
│   ├── main.css              # 全局设计令牌（色彩 / 字体 / 间距圆角）
│   ├── auth-bg.jpg           # 登录页背景：源图压暗 + 降饱和 + 轻模糊 + 暗角，1920×1080（约 95 KB）
│   └── auth-bg-narrow.jpg    # ≤900px 竖版裁切，900×1200（约 53 KB）
├── composables/
│   ├── useAccount.ts        # 余额共享状态（模块级 ref，未用 Pinia）
│   ├── useBackendHealth.ts  # 后端连接检测共享（顶栏徽标，各页刷新时同步复检）
│   └── useAuth.ts           # 注册 / 登录：真鉴权（令牌 + /api/auth/*），身份见契约 §4.15
├── components/
│   ├── PriceChart.vue   # 价格历史折线图（零依赖 SVG，升序直接用）
│   ├── TradePanel.vue   # 数量输入 + 买入/卖出 + 后端 message 展示
│   ├── LoadingState.vue # 三态组件（day1 统一布局要求，4 页共用）
│   ├── EmptyState.vue   # 空态（可插槽放引导链接）
│   └── ErrorState.vue   # 错误态（展示后端中文 message + 重试，不自动重放交易）
├── views/
│   ├── AuthView.vue          # /auth        注册 / 登录（全屏 CS2 背景）
│   ├── MarketView.vue        # /            市场列表
│   ├── PlayerDetailView.vue  # /players/:id 详情 + 折线图 + AI 建议 + 交易
│   ├── PositionsView.vue     # /positions   持仓 + 账户汇总
│   ├── ScheduleView.vue      # /schedule    赛程：轮次 → 暂停/点数 的派生可视化
│   └── TradesView.vue        # /trades      交易流水（后端已倒序）
├── core/schedule.ts   # core_engine/schedule.py 的移植：赛程派生 + 校验 + 圆桌法生成
├── data/demoSchedule.ts # 赛程镜像（由 scripts/build_schedule.py 生成，勿手改）
└── utils/format.ts    # money / pct / trendClass / dateTime
```

## 注册 / 登录（第 7 轮起：真鉴权）

第 6 轮这层是"只写浏览器 localStorage 的假账号"；**第 7 轮换成后端真鉴权**（契约 §4.11~§4.15）：
口令由后端 PBKDF2-HMAC-SHA256 散列，令牌由后端签发、可在服务端撤销，余额 / 持仓 / 流水**按账号隔离**。

| 入口 | 行为 |
| --- | --- |
| `/auth` | 登录 / 注册两个标签页，背景是处理过的 CS2 主视觉（`src/assets/auth-bg*.jpg`） |
| 注册 | **只要用户名 + 密码**（外加一次确认）。成功即登录——201 直接返回令牌，不用再发一次登录 |
| 登录 | 每次登录签发**新**令牌；勾"记住我"令牌落 localStorage，否则只活于当前标签页 |
| 访客 | "先随便逛逛"= **故意不带令牌**，用的是后端公共演示账户 `demo`（第 1~6 轮的历史数据都在它身上，不迁移） |
| 守卫 | `router/index.ts` 的 `beforeEach` 先 `await bootstrap()`（拿本地令牌问一次 `/api/auth/me`）再判断：未登录 → `/auth?redirect=原路径`；已登录访问 `/auth` → 回市场页 |
| 退出 | 侧栏账号卡片（窄屏在抽屉里）的"退出"：先撤销服务端令牌，再清本地；网络失败也照样清 |
| 删除账号 | 仅私人账户可见。侧栏"删除账号"→ 确认弹窗：必须再输一次口令 + 手输一遍用户名才能点删除；成功后级联删持仓/流水/令牌并回登录页（`?deleted=1` 显示结果）。公共演示账户不提供这个入口 |

- 登录页是独立全屏布局：`App.vue` 用 `isAuthPage` 判断，这一页不渲染侧栏 / 顶栏 / 氛围背景。
- 侧栏账号卡片显示 `nickname` + 身份标签（私人账户 / 公共演示账户 / 未登录），一眼能看出现在动的是谁的钱。
- **令牌只在 `api/token.ts` 里管**：`client.ts` 有令牌就自动加 `Authorization: Bearer …`，页面代码不碰令牌。
- `bootstrap()` 只在 401（过期 / 被撤销）时清会话；后端没起、网络错误都**保留令牌**，避免"重启后端 = 全员掉线"。
- 校验规则前后端各一份且必须一致（`useAuth.ts` ↔ `code/backend/app/core/security.py`），改规则要两边一起改。
- `VITE_USE_MOCK=true` 时 auth 也走本地假实现（`src/mock/auth.ts`），不会出现"行情是假的、登录是真的"。
- 想去掉登录门槛：删 `router/index.ts` 里的 `beforeEach` 即可，界面与账号态互不牵连。

## 契约铁律（改代码前先读 docs/software/api_contract.md）

1. **交易是否成功以后端数据库为准**：组件只展示接口返回，绝不本地改数字伪造成功。
2. 字段 snake_case：`player_id` / `current_price` / `change_pct`……不重命名。
3. `change_pct`、`profit` 等由后端算好，前端**不重算、不二次截断**。
4. 错误直接用后端中文 `message` 展示，**不写映射表、不自动重试**（重试=第二笔真实交易）。
5. `rating` 是项目**模拟**综合分（0–100），UI 必须带「模拟数据」标注（市场页/详情页已做）。
6. AI 分析接口成功返回裸对象；AI 故障 = 200 + `source:'rule_fallback'`，按 `source` 区分文案即可，不需要 4xx/5xx 分支。
7. 交易成功后必须刷新：余额（useAccount.refreshAccount）+ 行情 + 持仓/流水。

## 待办（对齐里程碑）

- [x] 后端启动后联调：查行情 → 买入 → 看持仓 → 卖出（2026-10-24 实机两轮通过：5 条错误分支 + AI 卡 + 三态均验证）
- [ ] 折线图悬停显示 `reason`（第 4 天，答辩归因用）
- [ ] 每日签到补给入口（若后端第 4 天提供接口）
- [ ] 注册 / 登录接后端（`POST /api/auth/register`、`/login`、`/logout`）：届时替换 `useAuth.ts`，并删掉本地摘要
