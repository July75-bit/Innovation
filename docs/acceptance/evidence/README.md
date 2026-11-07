# 验收证据截图（M3 / T3-04 + T4 前端项）

> 采集时间：2026-10-24（第 4 天）｜ 采集方式：真实后端（uvicorn :8000，seed 重置 + 8 轮模拟价格）
> + 真实浏览器（Chromium headless，1280×900 全页截图）｜ 环境：`VITE_USE_MOCK=false` 真实接口模式

## T3-04 全链路（查行情 → 买 2 股 → 持仓 → 卖 1 股 → 流水）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `01-market.png` | 市场页 | 8 名选手、涨跌幅、"模拟数据"标注、sh1ro 暂停置灰、徽标"连接成功：playerstock-backend"、余额 5000.00 |
| `02-detail-chart-ai.png` | ZywOo 详情页 | **T4-01** 折线图 10 个价格点；**T4-02** 涨跌原因 latest_reason；**T4-04** AI 建议卡（action/reason/risk/source/disclaimer） |
| `03-buy2-success.png` | 买入 2 股 | 后端返回"买入成功"，余额 5000→4747.46 |
| `04-positions.png` | 持仓页 | 2 股、均价/现价/市值/盈亏（后端算好值直显） |
| `05-sell1-success.png` | 卖出 1 股 | 后端返回"卖出成功"，余额→4873.73 |
| `06-trades.png` | 交易流水 | 时间倒序、方向/数量/成交价/金额/交易后余额 |

## 5 条错误分支（后端中文 message 原样展示，不重试）

| 文件 | 分支 | 实测消息 |
| --- | --- | --- |
| `07-err-insufficient-balance.png` | 余额不足 | 余额不足，当前余额 4873.73，需要 6313.50 |
| `08-err-position-limit.png` | 超 50 股上限 | 超过单选手持仓上限 50 股，当前持有 49 股，本次买入 2 股 |
| `09-err-insufficient-position.png` | 持仓不足 | 持仓不足，当前持有 1 股，本次卖出 10 股 |
| `10-err-invalid-qty.png` | 非法数量 | 前端拦截"数量必须是正整数"，按钮禁用（不发请求） |
| `11-suspended.png` | 暂停交易 | sh1ro 面板黄字提示 + 买卖按钮禁用 |

## T4-05 三态

| 文件 | 状态 | 触发方式 |
| --- | --- | --- |
| `12-state-loading.png` | 加载中 | 延迟 `/api/players` 响应 2s |
| `13-state-empty.png` | 空数据 | `/api/players` 返回 `[]` |
| `14-state-offline-error.png` | 失败（拔网线） | 真实停止后端进程：错误条"无法连接后端服务…"+ 重试按钮 + 顶栏徽标"后端未连接" |

## T4-02 每点 reason 展示（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `15-t4-02-point-reason.png` | ZywOo 详情页折线图：悬停 #3 数据点 + 展开「价格变动明细（10）」 | tooltip 显示 `2026-11-01 08:00:00 · 107.10 币` + "本场表现下滑（S=-1.00），价格下跌 15.00%（本轮模拟得分 76.6）"，与 `GET /api/players/1/prices` 第 3 点逐字一致；明细列表 10 行逐点带 时间/价格/reason |

## TC-307 刷新持久化（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `16-tc307-refresh-persist.png` | 深链 `/players/1` 直接打开后 F5 刷新全页 | 余额 / 价格历史（10 点）/ AI 卡 / 持仓提示全部由后端重建，无丢数据、控制台零报错 |

## 代码质量扫描报告（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `17-code-quality-scan.png` | 代码质量报告截图（实际命令输出渲染） | `pytest` 120 passed；`ruff check --statistics .` 第 3 次扫描 72 项（D 负责文件 0）；CI 三门槛全绿；含重构前后对比 |

## 线上验收（第 5 天，Render）

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| `online/online-account-5000.png` | `GET /api/account` | 线上余额 5000.00 / 总资产 5000.00 |
| `online/online-positions-empty.png` | `GET /api/positions` | 交易测试后清仓为空 |
| `online/online-trades-before-tc403.png` | `GET /api/trades` | **TC-403 之前的历史状态（空）**，仅作对照，不作为验收证据；当前线上为 3 条流水（见 test_report TC-404） |
| `online/online-prices-11points.png` | `GET /api/players/1/prices` | 11 个点、升序、末点 108.75 = current_price、reason 含「本轮得分 + S」 |

> 复现方式见 `code/frontend/README.md`（启动步骤）与 `docs/software/database_design.md` §4.1（价格点配方）。
