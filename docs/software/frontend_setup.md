# 前端脚手架配置记录（T1-04）

> **性质**：历史记录，不是操作指引。
> **背景**：第 1 天 `npm create vue@latest` 要求 `code/frontend/` 为空目录，
> 原占位说明从 `code/frontend/README.md` 移入本文件保存（T1-04"移走、别删"）。
> **当前开发说明**：见 [code/frontend/README.md](../../code/frontend/README.md)——项目已生成并跑通，
> 下文"目录为空"等表述均为第 1 天当时的语境。

## 脚手架命令与选项（2026-10-24 实际执行）

```powershell
# 仓库根目录执行
npm create vue@latest code/frontend
```

| 配置项 | 选择 |
| --- | --- |
| Project name | frontend |
| TypeScript | Yes |
| JSX Support | No |
| Vue Router | Yes |
| Pinia | No |
| Vitest | Yes |
| End-to-End Testing | No |
| ESLint | Yes |
| Prettier | Yes |

> 实际用 `create-vue@3.24.0` 生成（Vue 3.5 / Vite 8 / vue-router 5 / Vitest 4 / TS 6），
> 非交互参数为 `--ts --router --vitest --eslint-with-prettier`。

## 当时要求手工补的三件事（现状核对）

1. `code/frontend/.env.example`：`VITE_API_BASE_URL=http://127.0.0.1:8000`
   ——✅ 已建；第 2 天起另含 `VITE_USE_MOCK` 开关，以仓库当前文件为准。
   所有请求从环境变量读后端地址，源码 grep 无字面地址（CI 有自动检查）。
2. `npm run dev` 端口 `5173`——✅ 默认值未改，后端 CORS 放行该源。
3. `package-lock.json` 提交入库（CI `npm ci` 依赖）——✅ 已提交。

## 路由约定（已实现，代码见 `src/router/index.ts`）

| 路由 | 页面 | 主要内容 |
| --- | --- | --- |
| `/` | 市场页 | 选手名称、当前价格、涨跌幅、模拟表现分（标注"模拟"） |
| `/players/:id` | 选手详情页 | 价格、涨跌原因、历史价格折线图、AI 建议（BUY/SELL/HOLD + 理由 + 风险等级 + 免责） |
| `/positions` | 持仓页 | 持有数量、买入均价、当前估值 |
| `/trades` | 交易记录页 | 时间倒序的买卖流水 |

交易区域：数量输入框 + 买入/卖出按钮；成功或失败都重新拉取余额/持仓/流水，
并把后端返回的 `message` 原样展示（余额不足、数量不合法等），不自动重试。

## 边界（持续有效）

- 不修改 `code/backend/` 下任何文件（A 的边界）
- 不在本地只改页面数字伪造交易成功——交易是否成功以后端数据库为准
