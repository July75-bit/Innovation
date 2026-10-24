# 前后端接口契约（API Contract）

> **负责人**：B（定稿） ｜ **截止**：**第 1 天必须确认**，之后不得随意改字段 ｜ **状态**：✅ 四人已签（D/B/A/C；C 于 `94ea9aa` 补签）
> **对应课程指标**：#9 接口文档；分工文档第五节"最关键的是接口约定"

> 🔴 铁律：**交易是否成功以后端和数据库为准，不允许前端只改页面数字。**
> 🔴 改字段必须：更新本文档 → PR 勾"接口变更" → 通知对接人 → 前端同步改。

## 1. 通用约定

| 项 | 约定 |
| --- | --- |
| Base URL | 本地 `http://127.0.0.1:8000`，线上由环境变量 `VITE_API_BASE_URL` 注入 |
| 路径前缀 | 所有业务接口带 `/api` |
| 编码 | `application/json; charset=utf-8` |
| 字段命名 | **snake_case**，主键统一叫 `player_id` / `user_id`，**不要用 `id`** |
| 金额与价格 | `number`，保留 2 位小数（后端返回已格式化数值，前端不再二次截断） |
| 时间 | ISO 8601 字符串，统一 UTC，例 `2026-01-01T10:05:00Z`（前端 `new Date()` 可直接解析） |
| 布尔 | `true` / `false`（不要用 0/1） |

## 2. 统一错误格式

所有 4xx/5xx 返回：

```json
{
  "success": false,
  "message": "余额不足，当前余额 50.00，需要 100.00",
  "code": "INSUFFICIENT_BALANCE"
}
```

| HTTP | code | 场景 |
| --- | --- | --- |
| 400 | `INSUFFICIENT_BALANCE` | 余额不足 |
| 400 | `INSUFFICIENT_POSITION` | 持仓不足 |
| 400 | `POSITION_LIMIT_EXCEEDED` | 超过单选手 50 股上限 |
| 400 | `PLAYER_TRADING_SUSPENDED` | 选手比赛暂停交易 |
| 400 | `INVALID_QUANTITY` | 数量非正整数 |
| 404 | `PLAYER_NOT_FOUND` | 选手不存在 |
| 422 | `VALIDATION_ERROR` | Pydantic 校验失败 |
| 429 | `AI_RATE_LIMITED` | AI 调用限流（若启用） |
| 500 | `INTERNAL_ERROR` | 未预期异常（前端展示通用文案） |

> `message` 必须是**可直接展示给用户的中文**，前端不写映射表。

## 3. 接口清单

| # | 方法 | 路径 | 功能 | 对接人 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | `/api/health` | 健康检查 | 全员 | ✅ 已实现 |
| 2 | GET | `/api/players` | 市场选手列表 | A + B | ✅ 已实现 |
| 3 | GET | `/api/players/{player_id}` | 单个选手详情 | A + B | ✅ 已实现 |
| 4 | GET | `/api/players/{player_id}/prices` | 价格历史 | A + B + C | ✅ 已实现 |
| 5 | GET | `/api/account` | 账户余额 | A + B | ✅ 已实现 |
| 6 | GET | `/api/positions` | 持仓列表 | A + B | ✅ 已实现 |
| 7 | POST | `/api/trades/buy` | 买入 | A + B | ✅ 已实现 |
| 8 | POST | `/api/trades/sell` | 卖出 | A + B | ✅ 已实现（提前完成） |
| 9 | GET | `/api/trades` | 交易流水 | A + B | ✅ 已实现 |
| 10 | GET | `/api/analysis/{player_id}` | AI 分析建议 | A + B + D | ✅ 已实现（第 3 天 D 接线） |

> 第 1 天后端状态：1–9 已按本契约实现并有测试覆盖（`python -m pytest`）；
> 第 10 项于第 3 天由 D 把 `code/backend/ai/`（`build_player_context` + `analyze`）接进
> `app/api/ai.py`（B 的路由外壳，接线改动已同步本契约与测试）。
> 卖出（第 8 项）原计划第 2 天，因与买入共用同一套事务与校验、提前一并完成。

---

## 4. 接口详情

### 4.1 `GET /api/health`

```json
{ "status": "ok", "service": "playerstock-backend" }
```

### 4.2 `GET /api/players`

市场列表。无分页（8 名选手）。

```json
[
  {
    "player_id": 1,
    "name": "ZywOo",
    "display_name": "ZywOo",
    "team": "Vitality",
    "role": "AWPer",
    "current_price": 126.00,
    "prev_price": 120.00,
    "change_pct": 5.00,
    "rating": 88,
    "status": "trading"
  }
]
```

> `status ∈ {trading, suspended}`；`change_pct` 后端算好，前端不要自己算。
> 数据口径：`role` 为选手真实位置；`rating` 是本项目自建的**模拟综合表现分（0–100）**，仅用于驱动定价公式，**不是 HLTV Rating，也不是任何官方统计**，前端需标注为模拟数据。

### 4.3 `GET /api/players/{player_id}`

```json
{
  "player_id": 1,
  "name": "ZywOo",
  "display_name": "ZywOo",
  "team": "Vitality",
  "role": "AWPer",
  "current_price": 126.00,
  "prev_price": 120.00,
  "change_pct": 5.00,
  "rating": 88,
  "status": "trading",
  "latest_reason": "模拟比赛表现提升（模拟评分由 78 升至 88，S=+0.42）"
}
```

404 → `PLAYER_NOT_FOUND`。

### 4.4 `GET /api/players/{player_id}/prices`

```json
{
  "player_id": 1,
  "points": [
    { "ts": "2026-01-01T10:00:00Z", "price": 120.00, "reason": "初始价格" },
    { "ts": "2026-01-01T10:05:00Z", "price": 126.00, "reason": "模拟比赛表现提升" }
  ]
}
```

- 时间**升序**，前端直接用
- 无数据返回 `points: []`，**不返回 404**
- 每条必须带 `reason`（答辩要拆解归因）

### 4.5 `GET /api/account`

```json
{
  "user_id": 1,
  "balance": 5000.00,
  "initial_balance": 5000.00,
  "position_value": 0.00,
  "total_asset": 5000.00
}
```

### 4.6 `GET /api/positions`

```json
[
  {
    "player_id": 1,
    "name": "ZywOo",
    "quantity": 10,
    "avg_cost": 120.00,
    "current_price": 126.00,
    "market_value": 1260.00,
    "profit": 60.00,
    "profit_pct": 5.00
  }
]
```

持仓为 0 的选手不出现在列表中；无持仓返回 `[]`。

### 4.7 `POST /api/trades/buy`

请求：

```json
{ "player_id": 1, "quantity": 2 }
```

成功 200：

```json
{
  "success": true,
  "message": "买入成功",
  "balance": 4748.00,
  "player_id": 1,
  "quantity": 2,
  "price": 126.00,
  "trade_id": 17
}
```

失败 400 示例：

```json
{ "success": false, "message": "余额不足，当前余额 50.00，需要 126.00", "code": "INSUFFICIENT_BALANCE" }
```

校验顺序（B 必须按此顺序，便于前端给准确提示）：

1. `player_id` 存在 → 否则 404
2. `quantity` 为正整数 → 否则 422
3. 选手 `status == trading` → 否则 400
4. 余额充足 → 否则 400
5. 买入后持仓 ≤ 50 → 否则 400
6. 事务内扣款 + 加持仓 + 写流水 → COMMIT

**并发与重复提交的语义（第 2 天补充，无字段变更）**

- 同一账户的并发下单由后端串行化，**不会**出现超卖、超持仓上限或余额变负；
  判断写在数据库的条件更新里，详见 `database_design.md` §3.1。
- 并发下单或前端连点时，后一笔可能直接收到 §2 的统一错误体
  （`INSUFFICIENT_BALANCE` / `POSITION_LIMIT_EXCEEDED` / `INSUFFICIENT_POSITION`）。
  前端**按 `code` 提示即可，不要自动重试**——重试会变成第二笔真实交易。
- 本契约暂**不提供幂等键**（如 `client_order_id`）。若第 3 天要支持"重复提交只成交一次"，
  按 §6 流程提字段变更后再改，禁止前后端各自先实现。

### 4.8 `POST /api/trades/sell`

请求同买入。成功：

```json
{
  "success": true,
  "message": "卖出成功",
  "balance": 4874.00,
  "player_id": 1,
  "quantity": 1,
  "price": 126.00,
  "trade_id": 18
}
```

失败：`INSUFFICIENT_POSITION`（持仓不足，不允许卖空）。

### 4.9 `GET /api/trades`

交易流水，**时间倒序**。

```json
[
  {
    "trade_id": 18,
    "player_id": 1,
    "name": "ZywOo",
    "side": "SELL",
    "quantity": 1,
    "price": 126.00,
    "amount": 126.00,
    "balance_after": 4874.00,
    "created_at": "2026-01-01T10:10:00Z"
  }
]
```

`side ∈ {BUY, SELL}`。

### 4.10 `GET /api/analysis/{player_id}`

> **状态**：✅ 已实现（2026-10-23 第 3 天，D 接线）。
> 链路：`app/api/ai.py` → `ai.context.build_player_context()`（只读查库，失败回落 seed 数据）
> → `ai.llm_agent.analyze()`（无密钥/超时/非 JSON/枚举非法内部回落规则版）→ 固定 6 字段裸对象。
> 测试：`tests/unit/test_api_ai.py`、`tests/integration/test_e2e_flow.py`。

```json
{
  "player_id": 1,
  "action": "HOLD",
  "reason": "近 5 个价格点累计变动 +5.0%，综合表现分 88，未触发买卖阈值（规则版建议）",
  "risk_level": "LOW",
  "source": "rule_fallback",
  "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
}
```

**字段定义（6 个，前端按此渲染）**

| 字段 | 类型 | 必填 | 取值 / 约束 |
| --- | --- | --- | --- |
| `player_id` | int | ✅ | 与请求路径一致（实现以路径为准回填） |
| `action` | enum | ✅ | `BUY` / `SELL` / `HOLD`（大写，不接受中文或小写 `buy`） |
| `reason` | string | ✅ | 中文 1–3 句，**≤ 120 字**，必须引用具体数值（价格/涨跌幅/表现分） |
| `risk_level` | enum | ✅ | `LOW` / `MEDIUM` / `HIGH` |
| `source` | enum | ✅ | `llm`（模型生成）/ `rule_fallback`（规则兜底） |
| `disclaimer` | string | ✅ | 固定文案，前端**必须**展示 |

> `suggested_price_band`：本期**不输出**（2026-10-23 决策：LLM 版与规则版字段集合完全一致，
> 规则版不编造价格区间）。契约保留该字段为"可缺省"，前端按缺省容错；将来恢复输出也不必改渲染逻辑。

**错误码（本接口专属规则）**

| HTTP | code | 触发条件 | 说明 |
| --- | --- | --- | --- |
| 200 | — | 正常返回，**包含 AI 失败降级** | 默认路径；用 `source` 区分来源 |
| 404 | `PLAYER_NOT_FOUND` | `player_id` 不存在 | 返回 §2 统一错误体 |
| 429 | `AI_RATE_LIMITED` | 启用了限流且已超限 | 本期未启用限流，不会出现 |
| 500 | `INTERNAL_ERROR` | **仅**非 AI 故障（如数据库不可用） | 兜底逻辑本身也失败才算 |

> 🔴 **硬规则：AI 相关故障一律不得用 4xx / 5xx 表达。**
> 模型超时、未配置密钥、返回非法 JSON、调用被限流 —— 都必须返回 **200 + `source=rule_fallback`**，
> 保证前端只有一套渲染逻辑，且"AI 挂了不影响交易"这条设计目标可验证。
>
> **实现保证（2026-10-23）**：无密钥直接规则版、不碰网络；调模型超时取
> `settings.llm_timeout_seconds`（默认 20s）；超时/网络错误/非 JSON/枚举非法 → 200 + 规则版；
> 连上下文组装都失败时用「最小上下文」走规则版，同样不升级成 5xx。只有选手不存在（404）
> 与非 AI 故障（500）才用非 200 表达。

**只读保证（AI 绝不改余额）**

| 项 | 约定 |
| --- | --- |
| 数据操作 | 本接口只做 `SELECT`，**禁止**调用 `Session.commit()`，禁止任何 INSERT / UPDATE / DELETE |
| 依赖注入 | 路由只依赖 `get_db`（只读使用），不得注入交易服务 |
| 权限边界 | AI 只产出建议；真正下单必须由用户显式调用 `/api/trades/buy` / `sell` |
| 验证方式 | `docs/acceptance/test_plan.md` **TC-205**：调用本接口前后对比余额与持仓，必须完全不变；已在 `tests/unit/test_api_ai.py` 与 `tests/integration/test_e2e_flow.py` 断言 |

**响应形态注意**：本接口成功时返回**裸对象**（无 `success` 字段），失败时返回 §2 的统一错误体 `{success:false, message, code}`；前端按 HTTP 状态码分支处理。

---

## 5. 字段命名对照（防扯皮表）

| 含义 | ✅ 统一叫法 | ❌ 不要出现 |
| --- | --- | --- |
| 选手主键 | `player_id` | `id`, `pid`, `playerId` |
| 当前价格 | `current_price` | `price`, `currentPrice`, `now_price` |
| 上一价格 | `prev_price` | `last_price` |
| 涨跌幅（%） | `change_pct` | `change`, `pct`, `chg` |
| 模拟综合表现分（0–100） | `rating` | `score`, `performance` |
| 选手位置（真实） | `role`（AWPer / Entry / Rifler / IGL / Support / Lurker） | `position_name`, `pos` |
| 余额 | `balance` | `money`, `cash`, `fund` |
| 数量 | `quantity` | `qty`, `amount`, `num` |
| 方向 | `side`（BUY/SELL） | `type`, `direction` |
| 变化原因 | `reason` | `desc`, `note`, `msg` |
| 风险等级 | `risk_level` | `risk`, `level` |

## 6. 变更流程

1. 提出方在 PR 里勾选"接口变更"，写明新旧字段
2. B 更新本文件并合并
3. 通知对接人（A/B/C/D 中受影响者）
4. 前后端**同一天**完成适配，不允许"先合了再说"
5. 契约变更记录：

| 日期 | 变更内容 | 提出人 | 影响方 |
| --- | --- | --- | --- |
| 2026-10-17 | 初版定稿 | B | A/B/C/D |
| 2026-10-23 | 第 10 项 `GET /api/analysis/{player_id}` 实现并生效：固定 6 字段（去掉 `suggested_price_band` 输出）、AI 故障一律 200 + `rule_fallback`、404 仅用于选手不存在 | D | A/B |
| 2026-10-23（第 2 天） | 补 §4.7"并发与重复提交的语义"说明；买入的校验顺序在代码侧对齐本文（余额先于持仓上限，此前实现把上限提到了前面）。**字段与错误码均无变更** | B | 无（A 按 `code` 提示即可；D 的 AI 只读，不受影响） |

## 7. 契约验收（第 1 天）

- [x] A 确认所有字段都能在页面上渲染（不需要额外请求）（2026-10-24，实测 10 接口全通过，见下方 A 签字）
- [x] C 确认价格字段与 `price_history` 结构一致（2026-10-24，见下方 C 签字）
- [x] D 确认 AI 分析接口的输入数据都能从上述接口拼出来（2026-10-23）
- [x] 四人在这份文档下各留一行"确认"记录（2026-10-24，A/B/C/D 签字齐全）
- [x] **D 签字**（2026-10-23，T1-33）：`GET /api/analysis/{player_id}` 的**固定 6 字段**（2026-10-23 决策：不输出 `suggested_price_band`，契约中该字段保留为可缺省）、4 个错误码、"AI 绝不改余额"的只读保证已写入 §4.10；规则版兜底 `code/backend/ai/fallback.py` 已实现并通过自测。（2026-10-24 更正：此行原文写"7 个字段"，与 §4.10 / §6 变更记录统一为 6 字段）
- [x] **B 签字**（2026-10-24，第 2 天契约冻结复查，B 主持）：逐条核对 10 个接口的请求/响应字段，与 §4 一致，**无新增/改名字段**；`role` 为选手真实位置、`rating` 为项目模拟综合评分（UI 必须标注"模拟"）；`hltv_rating` / `kast` / `adr` 已删除且模型、schema、种子数据、AI 上下文里均无残留；第 10 项由 D 的改动已记入 §6 变更记录并可追溯。核对方式：`/openapi.json` 路径清单 + `tests/unit/test_api_players.py` / `test_api_trades.py` 逐字段断言 + 实机 25 项验收全绿
- [x] **A 签字**（2026-10-24，第 2 天契约冻结复查，A 补签）：逐条核对 10 个接口的请求/响应字段，与 §4 一致，**全部字段可在页面渲染、无需额外请求**；`change_pct` / `profit` / `profit_pct` 直接展示后端计算值，前端不重算、不二次截断；`rating` 在市场卡片与详情页均标注「模拟数据，非官方统计」；错误体 `message` 原样展示（无映射表），业务失败**不自动重试**；AI 分析按固定 6 字段渲染、以 `source` 区分 `llm` / `rule_fallback`，AI 故障不阻塞交易展示；地址全部走 `VITE_API_BASE_URL`（源码 grep 无字面本地地址），`VITE_USE_MOCK` 开关已同步 `.env.example` 与 README。核对方式：`code/frontend/src/api/types.ts` 与 §4 逐字段对照 + 前后端实机联调全链路（查行情 → 买 2 股 → 持仓 → 卖 1 股 → 流水 + 余额不足/持仓不足/超上限/非法数量/暂停交易 5 条错误分支）实测通过
- [x] **C 签字**（2026-10-24，第 2 天契约冻结复查，C 补签）：价格相关字段与本文一致，**无新增/改名**。① `players.current_price` 为唯一权威价（定价与交易都读它），`players.prev_price` 保存上一次价格、用于算涨跌幅；② 历史表为 `price_history(price_id, player_id, price, reason, ts)`（与 `database_design.md` §2.5 一致），`ts` 为带时区 UTC（`DateTime(timezone=True)`，接口返回形如 `2026-11-01T00:00:00Z`），按 `ts` 升序返回、空数组不 404；③ `change_pct` 是接口字段（百分数数值、保留 2 位），由取整后的新价反算，保证「价格 ×（1+涨跌幅）」自洽；④ `reason` 为中文短句且必非空，落库列 `VARCHAR(200)`、写入前按 200 字符截断；⑤ 价格更新只写 `players.current_price / prev_price` 与 `price_history`，**不碰 `users.balance` / `positions` / `trades`**；⑥ 信号映射为 `S = clamp(z / Z_FULL_SCALE, -1, 1)`（`Z_FULL_SCALE=3.0`），只影响 S 的取值、**不改变任何字段口径**。核对方式：`code/core_engine/pricing.py` 与 §4.4 逐字段对照 + `tests/unit/test_pricing.py`（10 条）+ `tests/unit/test_simulator.py`（3 条，同 seed 可复现）+ `python scripts/simulate_match.py --seed 42 --json` 实测 `ts` 形态与 JSON 字段 + `code/backend/app/core/price_update.py` 落库字段对照