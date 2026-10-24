> 本文件由 `code/frontend/README.md` 移入（T1-04，脚手架要求目标目录为空）。
> 脚手架生成后的最新开发说明见 [code/frontend/README.md](../../code/frontend/README.md)。

---

# code/frontend/ —— 由 A 同学用官方脚手架生成，请勿手工预置文件

## 为什么这个目录现在是空的

6 天手册第 1 天要求 A 同学在**仓库根目录**执行：

```powershell
npm create vue@latest code/frontend
```

脚手架要求 `code/frontend/` 目录**不存在或为空**，否则会提示目录非空而失败。因此这里只放这份说明，不预置 `package.json`、`vite.config.ts` 等文件。

## A 同学第 1 天的操作

```powershell
# 在仓库根目录执行
npm create vue@latest code/frontend
```

选项（与手册一致）：

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

生成后：

```powershell
cd code/frontend
npm install
npm run dev
```

## 必须手工补的三件事

1. 建 `code/frontend/.env.example`：

   ```text
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

   所有请求**从环境变量读后端地址**，不要写死 `127.0.0.1:8000`（第 5 天线上部署会改）。

   代码里的用法：

   ```ts
   const baseUrl = import.meta.env.VITE_API_BASE_URL
   ```

2. 确认 `npm run dev` 的端口是 `5173`（后端 CORS 默认放行这个源）。

3. 把 `package-lock.json` 提交到仓库（CI 用 `npm ci`，缺它就会失败）。

## 路由约定

| 路由 | 页面 | 主要内容 |
| --- | --- | --- |
| `/` | 市场页 | 选手名称、当前价格、涨跌幅、表现评分 |
| `/players/:id` | 选手详情页 | 价格、表现、涨跌原因、历史价格折线图、AI 建议（BUY/SELL/HOLD + 理由 + 风险等级） |
| `/positions` | 持仓页 | 持有数量、买入均价、当前估值 |
| `/trades` | 交易记录页 | 时间倒序的买卖流水 |

交易区域：数量输入框 + 买入按钮 + 卖出按钮，成功或失败都要刷新余额/持仓/流水，并把后端返回的 `message` 展示给用户（余额不足、数量不合法等）。

## 不要做的事

- 不要修改 `code/backend/` 下任何文件（A 的边界）
- 不要在本地只改页面数字伪造交易成功 —— 交易是否成功以后端数据库为准

