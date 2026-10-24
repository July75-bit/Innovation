# 后端联调自测记录（B 作为被测方）

> **负责人**：B ｜ **日期**：2026-10-25（第 4 天）｜ **对应**：day4 的「配合 A 联调（错误码 / 并发 / 成交价语义）」
>
> **为什么单独记一份**：A 的浏览器证据（`docs/acceptance/evidence/` 14 张）证明的是**前端能看到什么**；
> 这份证明的是**后端在同样的动作下返回什么**——错误码、并发语义、成交价口径。两边合起来才算联调闭环。

## 1. 环境与复现

| 项 | 内容 |
| --- | --- |
| 机器 | Windows 10 / Python 3.13.5 / 仓库内 `.venv` |
| 数据库 | 全新库，由一条命令生成：`python scripts/bootstrap_demo_data.py`（78 条 `price_history`、8 名选手） |
| 服务 | `uvicorn app.main:app --host 127.0.0.1 --port 8025`（真实进程，非 TestClient） |
| 驱动脚本 | `python scripts/smoke_test_api.py --base http://127.0.0.1:8025` |

> 脚本已入库，可对**任意**环境重跑：第 5 天把 `--base` 换成公网地址即可产出线上版本的同款记录
> （`--read-only` 只读不交易）。

## 2. 实测记录（原样输出）

| 环节 | 请求 | 实际结果 |
| --- | --- | --- |
| 健康检查 | `GET /api/health` | 200 `status=ok, service=playerstock-backend` |
| 市场列表 | `GET /api/players` | 8 名；前三：#1 ZywOo 108.75, #2 donk 131.45, #3 m0NESY 85.08 |
| 选手详情 | `GET /api/players/1` | ZywOo 现价 108.75，涨跌 -13.88%，状态 trading |
| 价格历史 | `GET /api/players/1/prices` | **11 点**，升序=True，末点 108.75 |
| 账户 | `GET /api/account` | 余额 5000.0，总资产 5000.0 |
| 买入 2 股 | `POST /api/trades/buy` | 200，成交价 **108.75**（= 当时最新价 108.75），金额 217.5，余额 4782.5 |
| 买入后持仓 | `GET /api/positions` | 1 条：ZywOo × 2，均价 108.75，浮盈 0.0 |
| 卖出 1 股 | `POST /api/trades/sell` | 200，成交价 108.75，余额 4891.25 |
| 交易流水 | `GET /api/trades` | 2 条 |
| 余额不足 | 买 #2 × 50 | 400 `INSUFFICIENT_BALANCE / 余额不足，当前余额 4891.25，需要 6572.50` |
| 超持仓上限 | 买 #4 × 51 | 400 `POSITION_LIMIT_EXCEEDED / 超过单选手持仓上限 50 股，当前持有 0 股，本次买入 51 股` |
| 非法数量 0 | 买 #1 × 0 | 422 `VALIDATION_ERROR / 请求参数不合法：quantity` |
| 非法数量 -1 | 买 #1 × -1 | 422 `VALIDATION_ERROR / 请求参数不合法：quantity` |
| 非法数量 1.5 | 买 #1 × 1.5 | 422 `VALIDATION_ERROR / 请求参数不合法：quantity` |
| 选手不存在 | 买 #99999 | 404 `PLAYER_NOT_FOUND / 选手不存在` |
| 暂停交易 | 买 #7（suspended） | 400 `PLAYER_TRADING_SUSPENDED / 该选手比赛进行中，暂停交易，请等结算完成后重试` |
| 持仓不足 | 卖 #1 × 5 | 400 `INSUFFICIENT_POSITION / 持仓不足，当前持有 1 股，本次卖出 5 股` |
| **并发卖出** | 同时发 2 个「卖 1」（实际只持 1 股） | 状态码 **[200, 400]**；剩余持仓 无；余额 5000.0（只入账一次） |

最终：**余额 5000.0**（5000 − 217.50 + 108.75 + 108.75 = 5000.00，钱没多也没少）、持仓空、流水 3 条。

## 3. 这四条语义对上了什么

| 语义 | 期望（契约） | 实测 |
| --- | --- | --- |
| **成交价 = 最新价** | `current_price`，不是用户输入价 | 108.75 买入、108.75 卖出，与 `GET /api/players/1` 一致 |
| **错误码** | 契约 §5：`INSUFFICIENT_BALANCE` / `POSITION_LIMIT_EXCEEDED` / `VALIDATION_ERROR` / `PLAYER_NOT_FOUND` / `PLAYER_TRADING_SUSPENDED` / `INSUFFICIENT_POSITION` | 6 类全部命中，且 `message` 是可直接展示的中文原句 |
| **校验顺序** | §4.7：余额先于持仓上限 | 买 #1 × 51（5546.25 > 余额）返回 `INSUFFICIENT_BALANCE` 而不是上限错误；换成买得起的 #4 × 51 才返回 `POSITION_LIMIT_EXCEEDED` |
| **并发重复提交** | 同一份持仓不能被卖两次 | 两个并发「卖 1」→ 一个 200、一个 400，余额只增加一次 |

> 上面「校验顺序」那一行是这次实测顺带确认的：脚本第一版直接拿 #1 × 51 去测上限，
> 结果被余额拦下了——这正是契约要求的行为，也说明 `test_buy_checks_balance_before_position_limit` 守的东西在真实 HTTP 链路上同样成立。

## 4. 与前端证据的关系

- A 的证据（`evidence/01`–`14`）覆盖：市场列表、详情页折线图、涨跌原因、AI 卡、三态、买入/卖出/持仓/流水页面；
- 本记录覆盖：同样的动作在**接口层**的返回与边界；
- 两者一致的点：余额 5000 → 买入后 4747.46/4782.5（口径见各自记录，因价格点批次不同）、卖出后余额回升、持仓与流水同步变化。

## 5. 未覆盖

| 项 | 原因 | 后续 |
| --- | --- | --- |
| 线上环境的同款记录 | 未部署 | 第 5 天用 `--base https://<后端>.onrender.com` 重跑本脚本 |
| 真并发压测（>2 并发、连接池打满） | 6 天时间不足 | 已用条件更新兜底，见 `database_design.md` §3.1 |
| 交叉原型测试（外部组） | 需另一支团队参与 | 组内互测兜底（A↔B、C↔D），D 组织 |
