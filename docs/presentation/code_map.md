# 代码对照表：功能 → 文件 → 函数（答辩查代码用）

> 用途：老师问「这个功能的代码在哪」「这段是怎么实现的」时，按功能找到文件和函数，打开讲清楚。
> 行号为 2026-11-28 develop 分支（`625c002`）的位置；代码改动后行号可能偏几行，以函数名为准（编辑器里 Ctrl+F 搜函数名）。
> 路径从仓库根目录算起。后端在 `code/backend/`，定价引擎在 `code/core_engine/`，前端在 `code/frontend/src/`。

## 先记住目录怎么分

| 目录 | 放什么 | 负责人 |
| --- | --- | --- |
| `code/frontend/src/views/` | 8 个页面（市场、详情、持仓、流水、赛程、个人、登录、404） | A |
| `code/frontend/src/components/` | 页面里的部件（交易面板、价格曲线、资产曲线等） | A |
| `code/frontend/src/api/` | 网页调用后端接口的代码 | A |
| `code/backend/app/api/` | 30 个接口，每个文件一组 | B |
| `code/backend/app/core/` | 交易规则、密码、限流、写价格、自动结算等公共逻辑 | B |
| `code/backend/app/models/` | 9 张数据库表的定义 | B |
| `code/core_engine/` | 定价公式、模拟比赛、赛程 | C |
| `code/backend/ai/` | 智能体：资料准备、调用模型、规则版、多角色、工具、仓位计算 | D |
| `tests/` | 后端测试（unit 单元 / integration 集成 / eval 智能体评测） | D |

一个请求的路线：**页面（views）→ 网页接口函数（api/index.ts）→ 后端接口（app/api）→ 规则 / 定价 / 智能体 → 数据库（models）**。

---

## 1. 买入、卖出（最常被问）

路线：详情页的交易面板点「买入」→ `api.buy()` → `POST /api/trades/buy` → 检查规则 → 同一事务里扣款、改持仓、写流水。

| 步骤 | 位置 | 函数 | 做什么 |
| --- | --- | --- | --- |
| 点按钮 | `code/frontend/src/components/TradePanel.vue:179` | `submit(side)` | 读数量，调用买入或卖出 |
| 「最大可买」 | `TradePanel.vue:126` | `applyMax()` | 按余额和 50 股上限算最多能买几股 |
| 发请求 | `code/frontend/src/api/index.ts:106` / `:118` | `buy()` / `sell()` | 调接口；成功后清空缓存，页面拿到新余额 |
| 买入接口 | `code/backend/app/api/trades.py:105` | `buy()` | 先查是否停牌 → 条件扣款（余额够才扣）→ 加仓（不超 50 股）→ 写流水 → 提交 |
| 卖出接口 | `trades.py:228` | `sell()` | 先入账 → 条件减仓（持仓够才减，卖光就删行）→ 写流水；不够就整笔撤回 |
| 流水列表 | `trades.py:327` | `list_trades()` | 当前用户的交易记录，按时间倒序 |
| 写一条流水 | `trades.py:78` | `_record_trade()` | 插入 trades 表 |
| 交易规则 | `code/backend/app/core/rules.py` | `calc_amount()` :30、`ensure_tradable_now()` :46、`ensure_sufficient_balance()` :84、`ensure_available_position()` :113、`ensure_position_limit()` :130 | 算金额、停牌拦截、余额不足、持仓不足、超过 50 股——各返回中文提示 |

**被问「怎么防止超卖」**：看 `trades.py` 里 `update(User).where(User.balance >= amount)` 这一句，余额够才扣，扣不到就整笔撤回；加仓同理 `Position.quantity + quantity <= limit`。测试在 `tests/unit/test_trades_concurrency.py`（两笔同时卖）。

## 2. 选手行情与价格曲线

| 步骤 | 位置 | 函数 | 做什么 |
| --- | --- | --- | --- |
| 市场页加载 | `code/frontend/src/views/MarketView.vue:267` | `load()` | 拉选手列表、排序筛选 |
| 选手列表接口 | `code/backend/app/api/players.py:53` | `list_players()` | 返回 16 名选手的现价和涨跌 |
| 选手详情接口 | `players.py:63` | `get_player()` | 一位选手的信息和最近价格点 |
| 价格历史接口 | `code/backend/app/api/prices.py:60` | `get_price_history()` | 每个价格点的价格、时间、原因 |
| 画曲线 | `code/frontend/src/components/PriceChart.vue` | `niceDomain()` :122 等 | 用 SVG 画价格曲线，Y 轴取整刻度 |
| 停牌显示 | `code/frontend/src/core/tradingStatus.ts:54` / `:68` | `haltReason()` / `isHalted()` | 按今天的赛程判断该选手是否停牌 |

## 3. 定价算法（C 的定价引擎）

路线：模拟一场比赛的得分 → 和自己近 5 场比，算表现分 S → 套公式算新价格 → 写入 players 和 price_history。

| 步骤 | 位置 | 函数 | 做什么 |
| --- | --- | --- | --- |
| 模拟比赛 | `code/core_engine/simulator.py:65` | `generate_match()` | 按选手评分和随机种子生成本轮得分（同种子结果相同） |
| 表现分 | `code/core_engine/pricing.py:247` | `standardize_score()` | 本轮得分与近 5 场的标准分，除以 3 后截断到 −1～1 |
| 新价格 | `pricing.py:162` | `update_price()` | `P′ = max(P_floor, P × (1 + αS + βD))`：α=0.15、β=0（需求信号 D 本期不生效）、P_floor=1.0；αS+βD 先截断到 ±20%，并生成原因文字 |
| 参数 | `pricing.py:44–52` | `DEFAULT_ALPHA = 0.15`、`DEFAULT_BETA = 0.0`、`DEFAULT_FLOOR = 1.0`、`MAX_STEP_PCT = 0.20`、`Z_FULL_SCALE = 3.0` | 公式里的常数；α、β、下限可用环境变量 PRICING_ALPHA / PRICING_BETA / PRICING_FLOOR 覆盖 |
| 需求信号 | `code/core_engine/simulator.py:145` | `to_demand_signal()` | 净买入量 ÷ 总成交量，截断到 −1～1；β=0 时不影响价格 |
| 停牌判断 | `code/core_engine/schedule.py:162` | `suspension_reason()` | 本队这一轮在比赛就整队停牌 |
| 写入数据库 | `code/backend/app/core/price_update.py:70` / `:119` | `plan_for_player()` / `apply_updates()` | 先算好每人的新价格，再在一个事务里写 players 和 price_history |
| 手动结算接口 | `code/backend/app/api/prices.py:88` | `recalc_prices()` | 带运维口令才能触发一轮结算 |
| 自动结算 | `code/backend/app/core/auto_settle.py:154` | `settle_if_due()` | 访问市场页、详情曲线或服务启动时，顺路把到期没结算的轮次补上（5 分钟最多检查一次） |

**被问「价格为什么这么动」**：打开 `pricing.py` 的 `update_price()`，公式就在里面；每个价格点的原因由 `_build_reason()`（:116）生成，写进 price_history.reason。测试在 `tests/unit/test_pricing.py`。

## 4. 智能体（D）

### 4.1 建议卡（最基本的一条）

路线：详情页 → `GET /api/analysis/{id}` → 准备资料 → 问模型 → 检查 6 个字段 → 不合格就用规则版。

| 步骤 | 位置 | 函数 | 做什么 |
| --- | --- | --- | --- |
| 接口 | `code/backend/app/api/ai.py:95` | `get_analysis()` | 取当前用户 → 准备资料 → `shared_advice()` 调 `analyze()`；同一用户、选手、价格、持仓 120 秒内与决策卡共用一条建议，`?refresh=true` 强制重算 |
| 准备资料 | `code/backend/ai/context.py:229` | `build_player_context()` | 查选手、最近 10 个价格点、**当前用户**的持仓；查库失败用种子数据 |
| 查持仓 | `context.py:150` | `_read_position()` | 按用户编号取持仓（未登录取演示账户） |
| 总入口 | `code/backend/ai/llm_agent.py:342` | `analyze()` | 没密钥直接规则版；否则问模型，出任何错都回落规则版 |
| 拼提问 | `llm_agent.py` | `build_user_prompt()`、`_fmt_account()` | 按白名单取 12 个字段拼成中文提问，含当前用户余额、还能买几股 |
| 调模型 | `llm_agent.py:201` | `_default_chat()` | 用标准库发请求给 DeepSeek，20 秒超时；先检查每分钟额度 |
| 检查回答 | `llm_agent.py:293` | `_parse_and_validate()` | 取出 JSON，动作只能买/卖/持有，风险只能低/中/高，理由不能空 |
| 截断理由 | `llm_agent.py:312` | `_truncate_reason()` | 超过 200 字在句号处截断 |
| 提示词 | `code/backend/ai/prompts.py` | `SYSTEM_PROMPT`、`USER_PROMPT_TEMPLATE` | 要求只输出 JSON、必须引用具体数值 |
| 规则版 | `code/backend/ai/fallback.py:66` | `rule_based_advice()` | 涨超 5% 且评分低于 60 → 卖；跌超 5% 且评分 75 以上 → 买；其余持有；无持仓不建议卖 |

### 4.2 决策卡、三人协作、工具调用、价格解读、简报

| 功能 | 接口函数（`code/backend/app/api/agent.py`） | 核心逻辑 |
| --- | --- | --- |
| 决策卡（建议 + 股数 + 止损） | `agent_decision()` | `shared_advice()`（`code/backend/app/core/advice_cache.py`）取与建议卡同一条建议 → `code/backend/ai/decision.py` `build_plan()`：目标持仓 =（余额 + 已持仓市值）× 10% / 6% / 3%，建议买入 = 目标 − 已持，再受余额和 50 股上限约束；止损线 −12% / −9% / −6% |
| 三人协作 | `agent_panel()` :487 | `code/backend/ai/panel.py:83` `run_panel()`：分析师 → 风控 → 交易员依次调用模型，角色提示在 `ROLE_PROMPTS`（:28），结论取自交易员；三人共用的资料由 `_account_line()` 写入当前用户的余额、已持股数和 50 股上限 |
| 工具调用 | `agent_tools()` :606（3 个工具的执行函数写在这个函数里） | `code/backend/ai/tools.py:109` `run_tool_loop()`：工具清单 `TOOL_SPECS`（:27），模型决定调用哪个，最多 3 轮 |
| 价格解读 | `agent_narrative()` :511 | `code/backend/ai/narrate.py:51` `generate_narrative()`，按价格点缓存在 price_narratives 表 |
| 今日简报 | `agent_brief()` :359 | `_brief_items()` :300 生成三条要点；`_clean_brief_summary()` :264 清洗模型输出；缓存 10 分钟 |
| 采纳 / 忽略 | `record_decision()` :442、`decision_stats()` :464 | 写 decision_logs 表，统计采纳率 |
| 调用审计 | `_write_trace()` :62、`agent_traces()`、`verify_traces()` | 每次调用写 agent_traces 表并串入哈希链；`GET /api/agent/traces/verify` 校验链是否完整；写失败不影响页面 |
| 审计哈希链 | `code/backend/app/core/trace_hash.py` | `compute_hash()` 算 SHA-256(本条内容 + 上一条哈希)；`verify_chain()` 逐条重算，报告第一处断开 |
| 前端调用 | `code/frontend/src/views/PlayerDetailView.vue` | `loadCore()` :163（先并行取选手信息和价格，再并行取建议、决策卡、价格解读）、`loadPanel()` :109、`loadTools()` :133、`recordChoice()` :260 |

**被问「AI 坏了怎么办」**：看 `llm_agent.py` 的 `analyze()`，`try ... except Exception` 里回落 `_fallback()`；三人协作和工具调用也各有 `except` 回落规则版。测试在 `tests/unit/test_ai_fallback.py`、`test_ai_panel.py`、`test_ai_tools_loop.py`。

## 5. 注册、登录、账号

| 步骤 | 位置 | 函数 | 做什么 |
| --- | --- | --- | --- |
| 登录页 | `code/frontend/src/views/AuthView.vue:102` | `submit()` | 登录或注册 |
| 前端登录态 | `code/frontend/src/composables/useAuth.ts` | `login()` :210、`register()` :196、`logout()` :236、`bootstrap()` :175 | 保存令牌；换账号时清空缓存（`forgetSession()` :80、`adopt()` :91） |
| 页面拦截 | `code/frontend/src/router/index.ts:111` | `router.beforeEach` | 没登录也没选访客，就跳到登录页 |
| 注册接口 | `code/backend/app/api/auth.py:69` | `register()` | 校验用户名和密码 → 加密存储 → 直接发令牌 |
| 登录接口 | `auth.py:109` | `login()` | 同一用户名 10 分钟内错 5 次先锁住 → 核对密码 → 发令牌 |
| 当前身份 / 退出 / 删号 | `auth.py:141` / `:154` / `:169` | `me()` / `logout()` / `delete_account()` | 删号要再输一次密码，连同持仓、流水、令牌一起删 |
| 识别当前用户 | `code/backend/app/api/deps.py:82` | `get_current_user()` | 带令牌 = 私人账号；不带 = 公共演示账户；令牌失效 = 401 |
| 密码与令牌 | `code/backend/app/core/security.py` | `hash_password()` :58、`verify_password()` :67、`new_token()` :83、`hash_token()` :89 | 密码加盐做 10 万次 PBKDF2；令牌库里只存哈希 |

## 6. 持仓、个人页、资产曲线

| 功能 | 位置 | 函数 |
| --- | --- | --- |
| 账户余额与总资产 | `code/backend/app/api/account.py:45` | `get_account()` |
| 资产曲线 | `account.py:176` | `get_account_history()`：用本账户流水和历史价格，在每个价格点和交易时间点还原「现金 + 持仓市值」 |
| 重建余额 | `account.py:225` | `rebuild_account()`：清空自己的持仓和流水，余额恢复初始值 |
| 持仓列表 | `code/backend/app/api/positions.py:31` | `list_positions()` |
| 前端页面 | `code/frontend/src/views/` | `PositionsView.vue` `load()` :62、`ProfileView.vue` `load()` :60、`TradesView.vue` `load()` :28 |

## 7. 安全与运维

| 功能 | 位置 | 函数 |
| --- | --- | --- |
| 限流（模型、登录、注册） | `code/backend/app/core/rate_limit.py` | `SlidingWindow`（:24）、`llm_budget_ok()`（:74）、`login_key()`（:80） |
| 运维口令 | `code/backend/app/core/ops_auth.py:33` | `require_ops_token()`：重灌和结算接口都要带口令 |
| 统一错误格式 | `code/backend/app/core/errors.py` | `ApiError`（:23）、`register_exception_handlers()`（:40）：中文提示 + 错误码，不暴露报错细节 |
| 跨域设置 | `code/backend/app/main.py:48` | `resolve_cors_origins()` |
| 启动 | `main.py:90` | `lifespan()`：建表、自动结算 |
| 数据库连接 | `code/backend/app/core/database.py` | `get_db()`（:57）、`init_db()`（:98） |
| 健康检查 / 数据库自检 / 日志 / 重灌 | `app/api/health.py:12`、`debug.py:49`、`logs.py:28`、`debug.py:89` | `health()`、`debug_db()`、`debug_logs()`、`debug_reseed()` |
| 配置项 | `code/backend/app/core/config.py:22` | `Settings`：所有环境变量（模型、限流、自动结算等） |

## 8. 数据库表定义（`code/backend/app/models/`）

| 文件 | 表 |
| --- | --- |
| `user.py` / `auth_token.py` | users / auth_tokens |
| `player.py` / `price_history.py` | players / price_history |
| `position.py` / `trade.py` | positions / trades |
| `agent.py` | agent_traces / decision_logs / price_narratives |

## 9. 测试对应（被问「怎么证明」时打开）

| 功能 | 测试文件（`tests/`） |
| --- | --- |
| 买卖规则、并发 | `unit/test_trades_rule.py`、`unit/test_trades_concurrency.py`、`unit/test_api_trades.py` |
| 定价、模拟比赛、赛程 | `unit/test_pricing.py`、`unit/test_simulator.py`、`unit/test_schedule.py`、`integration/test_price_reason_traceability.py` |
| 自动结算、手动结算 | `unit/test_auto_settle.py`、`integration/test_prices_recalc.py` |
| 智能体 | `unit/test_llm_agent.py`、`unit/test_ai_fallback.py`、`unit/test_ai_panel.py`、`unit/test_ai_tools_loop.py`、`unit/test_agent_api.py` |
| 智能体评测、红队 | `eval/test_agent_properties.py`、`eval/test_agent_redteam.py` |
| 登录、多用户 | `unit/test_api_auth.py`、`integration/test_auth_multiuser.py` |
| 限流、数量上限 | `unit/test_rate_limit_and_caps.py` |
| 审计哈希链 | `unit/test_trace_hash_chain.py` |
| 端到端流程 | `integration/test_e2e_flow.py` |

现场跑：仓库根目录执行 `python -m pytest tests/unit/test_trades_rule.py -q`（换成任意文件）。

---

## 被问代码时的答法

1. **先说在哪**：「这个在 `trades.py` 的 `buy()` 函数里。」——用上面的表找到，打开文件，Ctrl+F 搜函数名。
2. **再说三步**：按表里「做什么」一列讲，比如「先查停牌，再条件扣款，最后写流水」。
3. **最后给证据**：「对应的测试在 `test_trades_concurrency.py`，可以现场跑。」
4. **不是自己写的部分**：如实说「这部分是 B（或 C）写的，我知道它的作用是……，细节可以请他补充」，不要硬讲。
