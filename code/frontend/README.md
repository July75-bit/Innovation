# code/frontend —— PlayerStock 前端（A 同学负责）

Vue 3 + TypeScript + Vite，由官方脚手架 `npm create vue@latest` 生成
（选项：TypeScript=Yes / JSX=No / Vue Router=Yes / Pinia=No / Vitest=Yes / E2E=No / ESLint+Prettier=Yes）。

## 运行

```powershell
cd code/frontend
npm install                  # 首次或依赖变化时
# .env.local 已包含 VITE_API_BASE_URL=http://127.0.0.1:8000
npm run dev                  # http://localhost:5173（后端 CORS 默认放行该源）
```

常用脚本：`npm run type-check`、`npm run lint`、`npm run format`、`npm run test:unit`、`npm run build`（产物 `dist/`，Render Static Site 用）。

## 环境变量（必须，不许写死地址）

| 文件 | 用途 |
| --- | --- |
| `.env.example` | 模板：`VITE_API_BASE_URL=http://127.0.0.1:8000` |
| `.env.local` | 本地实际值（已被 .gitignore 忽略，新克隆后从 example 复制） |
| Render 环境变量 | 第 5 天部署时注入线上后端地址 |

代码统一从 `import.meta.env.VITE_API_BASE_URL` 读取（封装在 `src/api/client.ts`）。

## 结构

```text
src/
├── api/
│   ├── types.ts       # 契约 §4 全部响应类型（snake_case，不做驼峰转换）
│   ├── client.ts      # fetch 封装：环境变量、统一错误体 {success,message,code}
│   └── index.ts       # 10 个业务接口函数（api.listPlayers / api.buy / ...）
├── composables/
│   └── useAccount.ts  # 余额共享状态（模块级 ref，未用 Pinia）
├── components/
│   ├── PriceChart.vue # 价格历史折线图（零依赖 SVG，升序直接用）
│   └── TradePanel.vue # 数量输入 + 买入/卖出 + 后端 message 展示
├── views/
│   ├── MarketView.vue        # /            市场列表
│   ├── PlayerDetailView.vue  # /players/:id 详情 + 折线图 + AI 建议 + 交易
│   ├── PositionsView.vue     # /positions   持仓 + 账户汇总
│   └── TradesView.vue        # /trades      交易流水（后端已倒序）
└── utils/format.ts    # money / pct / trendClass / dateTime
```

## 契约铁律（改代码前先读 docs/software/api_contract.md）

1. **交易是否成功以后端数据库为准**：组件只展示接口返回，绝不本地改数字伪造成功。
2. 字段 snake_case：`player_id` / `current_price` / `change_pct`……不重命名。
3. `change_pct`、`profit` 等由后端算好，前端**不重算、不二次截断**。
4. 错误直接用后端中文 `message` 展示，**不写映射表、不自动重试**（重试=第二笔真实交易）。
5. `rating` 是项目**模拟**综合分（0–100），UI 必须带「模拟数据」标注（市场页/详情页已做）。
6. AI 分析接口成功返回裸对象；AI 故障 = 200 + `source:'rule_fallback'`，按 `source` 区分文案即可，不需要 4xx/5xx 分支。
7. 交易成功后必须刷新：余额（useAccount.refreshAccount）+ 行情 + 持仓/流水。

## 待办（对齐里程碑）

- [ ] 后端启动后联调：查行情 → 买入 → 看持仓 → 卖出（第 3 天验收）
- [ ] 折线图悬停显示 `reason`（第 4 天，答辩归因用）
- [ ] 每日签到补给入口（若后端第 4 天提供接口）
