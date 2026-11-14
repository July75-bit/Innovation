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
| 400 | `PLAYER_TRADING_SUSPENDED` | 选手暂停交易（运维手动冻结，或**本队这一轮有比赛**：按赛程派生） |
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
| 11 | POST | `/api/prices/recalc` | **赛后结算（运维接口，不对前端开放）**：写入一轮比赛后的价格 | B + C | ✅ 已实现（第 4 天 C；`tests/integration/test_prices_recalc.py` 5 条） |
| 13 | POST | `/api/auth/register` | **注册私人账号（第 7 轮）**：成功即登录，返回访问令牌 | A + B | ✅ 已实现（`tests/unit/test_api_auth.py`） |
| 14 | POST | `/api/auth/login` | **登录**：口令校验通过签发新令牌 | A + B | ✅ 已实现 |
| 15 | GET | `/api/auth/me` | **当前身份**：首屏用本地令牌确认还管不管用 | A + B | ✅ 已实现 |
| 16 | POST | `/api/auth/logout` | **退出**：撤销当前令牌（幂等） | A + B | ✅ 已实现 |
| 17 | DELETE | `/api/auth/account` | **删除账号**：口令二次确认，级联删持仓/流水/令牌 | A + B | ✅ 已实现（`tests/unit/test_api_auth.py` + `tests/integration/test_auth_multiuser.py`） |
| 12 | GET | `/api/debug/db` | **只读自检（验收探针，不对前端开放）**：返回数据库方言、表清单与行数 | B | ✅ 已实现（第 5 天 B；`tests/unit/test_debug_api.py` 3 条）。只回元信息、不含连接串与个人数据；`DEBUG_ENDPOINTS=0` 可关闭（关后 404） |

> 第 1 天后端状态：1–9 已按本契约实现并有测试覆盖（`python -m pytest`）；
> 第 10 项于第 3 天由 D 把 `code/backend/ai/`（`build_player_context` + `analyze`）接进
> `app/api/ai.py`（B 的路由外壳，接线改动已同步本契约与测试）。
> 第 11 项是第 4 天新增的**运维接口**（结算不是玩家动作）：前端不调用、A 无需适配；
> 请求/响应、幂等去重键与 409 语义见 §6 变更记录与 `mechanism_design.md` §5 第 4 条。
> 卖出（第 8 项）原计划第 2 天，因与买入共用同一套事务与校验、提前一并完成。

---

## 4. 接口详情

### 4.1 `GET /api/health`

```json
{ "status": "ok", "service": "playerstock-backend" }
```

### 4.2 `GET /api/players`

市场列表。无分页（16 名选手，8 支战队各 2 人）。

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
> **暂停交易的判定（2026-11-14 第 8 轮补）**：两层，顺序固定 ——
> 1. `players.status != trading`（运维手动冻结）**优先**，文案沿用原句；
> 2. 否则看**本队这一轮是否在比赛**：轮次按 UTC 比赛日查 `data/match_schedule.json`（与 `POST /api/prices/recalc` 的停牌口径同源），命中则整队 4 人拦单。
>
> 今天不是比赛日时只有第 1 层生效。命中任一层的响应仍是 `400 PLAYER_TRADING_SUSPENDED`，**字段与错误码不变**，只是 `message` 会写出具体对阵（如“G2 vs Astralis 比赛中，暂停交易，请等本轮结算完成后再下单”）。
> 前端市场页 / 详情页 / 交易面板按同一规则展示与禁用，界面结论与接口一致。

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

> 卖出走与 §4.7 完全相同的状态闸门（含本轮赛程派生），因此“正在打比赛的选手”连持仓也卖不掉，需等本轮结算。

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

### 4.11 `POST /api/auth/register`（第 7 轮）

请求：

```json
{ "username": "lan_player", "password": "cs2go1234" }
```

成功 `201`：

```json
{
  "token": "bH_…",
  "expires_at": "2026-12-07T08:12:31Z",
  "user": {
    "user_id": 2,
    "nickname": "lan_player",
    "balance": 5000.0,
    "initial_balance": 5000.0,
    "created_at": "2026-11-07T08:12:31Z",
    "account_type": "private"
  }
}
```

失败码（都是 §2 的统一错误体）：

| HTTP | `code` | 触发条件 | 前端处理 |
| --- | --- | --- | --- |
| 422 | `INVALID_INPUT` | 用户名不合法 / 口令不满足规则 | 直接展示 `message` |
| 409 | `USERNAME_TAKEN` | 同名已存在（大小写不敏感） | 直接展示 `message` |
| 409 | `USERNAME_RESERVED` | 用了保留名 `demo` | 直接展示 `message` |

**规则两边各校验一遍**：前端 `src/composables/useAuth.ts` 先挡一道（少发一次请求），
后端 `app/core/security.py` 是准绳（不能靠前端）。改规则必须两处一起改。

### 4.12 `POST /api/auth/login`

请求同 §4.11。成功 `200` 同 §4.11 响应形状（每次登录签发**新**令牌，多设备互不影响）。

| HTTP | `code` | 说明 |
| --- | --- | --- |
| 401 | `INVALID_CREDENTIALS` | 账号不存在**与**口令错误都是这一句 `用户名或密码不正确`——接口不能用来枚举账号名 |
| 403 | `PUBLIC_ACCOUNT` | `demo` 是公共账户，没有口令，不接受密码登录 |

### 4.13 `GET /api/auth/me`

带 `Authorization: Bearer <token>` 时返回该账号身份；**不带**该头时返回公共演示账户（`authenticated: false`）。

```json
{ "authenticated": true, "user": { "user_id": 2, "nickname": "lan_player", "…": "同上" } }
```

| HTTP | `code` | 前端动作 |
| --- | --- | --- |
| 401 | `UNAUTHORIZED` | 令牌过期/被撤销 → 清本地令牌，回 `/auth` |
| 0（网络错误） | `NETWORK_ERROR` | **保留令牌**，不踢人回登录页（后端重启不该让全员掉线） |

### 4.14 `POST /api/auth/logout`

撤销**当前这枚**令牌（删 `auth_tokens` 行）。没带令牌也返回成功，`revoked: false`——幂等，
前端清本地存储后重复调用不该报错。

```json
{ "success": true, "message": "已退出登录", "revoked": true }
```

### 4.16 `DELETE /api/auth/account`（删除账号）

请求（**必须再输一次口令**）：

```json
{ "password": "cs2go1234" }
```

成功 `200`：

```json
{
  "success": true,
  "message": "账号已删除",
  "deleted_positions": 1,
  "deleted_trades": 1,
  "deleted_tokens": 1
}
```

四道闸，少一道都可能删错东西：

| HTTP | `code` | 条件 |
| --- | --- | --- |
| 401 | `UNAUTHORIZED` | 没带 `Authorization`——那会落到公共演示账户，它不属于任何个人，不能删 |
| 403 | `PUBLIC_ACCOUNT` | 带了令牌但账户无口令（理论上不该出现，兜底用） |
| 401 | `INVALID_CREDENTIALS` | 口令不对，**且必须什么都没删**（测试专门守这条） |
| 200 | — | 删除成功，响应里报告删掉的持仓 / 流水 / 令牌行数 |

**为什么删号要输口令**：删的是余额、持仓、流水，不可恢复。只靠令牌就能删号，
在"共用电脑忘了退出"这种场景下是不可接受的失败模式。

**删除范围**：`positions`、`trades`、`auth_tokens` 里属于该 `user_id` 的行，然后 `users` 行本身。
`players` / `price_history` 与公共演示账户 `demo` 的数据**一律不动**（有集成用例守着）。
删除顺序是先子表后 `users`，不依赖 ORM 级联，也就不怕某个环境的 SQLite 没开 `PRAGMA foreign_keys`。

**DELETE 带请求体**：`TestClient` 的 `.delete()` 不收 `json=`，测试里走 `client.request("DELETE", …)`；
浏览器 `fetch` 没有这个限制，前端就是这么发的。

### 4.17 `POST /api/account/rebuild`（余额重建）

把**当前账户**恢复成刚注册的样子：余额 → `initial_balance`（1000/5000 口径同配置），
清空自己的持仓与流水。**其它账号、市场行情、选手数据一律不动。**

请求：`POST /api/account/rebuild?confirm=true`（无请求体；`confirm` 必须为 `true`，防误触）

成功 `200`：

```json
{
  "user_id": 2,
  "balance": 5000.0,
  "cleared_positions": 1,
  "cleared_trades": 3,
  "note": "余额已恢复为初始值；本账户的持仓与流水已清空（其它账号与行情不受影响）"
}
```

| HTTP | `code` | 条件 |
| --- | --- | --- |
| 400 | `CONFIRM_REQUIRED` | 没传 `confirm=true`（防误触，前端按钮点击后才带） |
| 200 | — | 重建成功（幂等：第二次调用清掉 0 条） |

**为什么需要这个接口**：第 6 天起，**重置市场行情**（`POST /api/debug/reseed`）只重置行情与
公共演示账户 `demo`——**注册账号的余额、持仓、流水跟着账号走，永不因重灌丢失**。
所以"我想从头再来"必须由用户自己按下这个按钮（前端：持仓页「余额重建」）。


### 4.15 身份与数据归属（本轮新增的全局约定）

| 请求 | 落到哪个账户 | 说明 |
| --- | --- | --- |
| 带有效 `Authorization: Bearer …` | 该令牌的私人账户 | 余额 / 持仓 / 流水按 `user_id` 隔离，50 股上限**按人算** |
| 不带 `Authorization` | 公共演示账户 `demo` | 未登录访客共用；第 1~6 轮的历史数据都留在这里，**不迁移** |
| 带无效/过期令牌 | — | 一律 401，不静默降级成访客（否则"退出后还以为自己登录着"） |

`GET /api/account` / `GET /api/positions` / `GET /api/trades` / `POST /api/trades/buy|sell`
**响应形状一字未改**，只是背后的 `user_id` 换了来源（`app/api/deps.py:get_current_user`）。
所以 A 的页面代码零改动，只有 `useAuth` 从"本地假账号"换成真接口。

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
| 账号名 | `nickname` | `username`, `user_name`, `account`（请求体入参叫 `username`，响应里的账户字段仍是 `nickname`） |
| 访问令牌 | `token` | `accessToken`, `jwt`, `auth` |
| 账户类型 | `account_type`（`private` / `public_demo`） | `type`, `is_private` |

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
| 2026-10-25（第 4 天） | **新增运维接口** `POST /api/prices/recalc`（赛后结算）：请求 `{round_no, played_at, items:[{player_id, score, signal}]}`，响应区分 `applied` / `skipped`；幂等去重键 `(player_id, round)`（用 `played_at` 写入 `price_history.ts` 定位轮次）；算价只用 C 的 `update_price`（reason 带"本轮得分"），落库复用 B 的 `app/core/price_update.py`。**已有 10 个对外接口的字段与错误码均无变更**，前端无需改动 | C | B（落库服务被复用，无改动）、D（验收清单 +1 条） |
| 2026-11-14（第 8 轮） | §4.7/§4.8 的 `PLAYER_TRADING_SUSPENDED` 补上**本轮赛程派生**这一层：本队在打的 4 人买/卖都会被拦（`core_engine.current_round` 按 UTC 比赛日取轮次）。**字段与错误码均无变更**，message 更具体；前端同步按同一规则显示与禁用 | A + C | 无（A 按 `code` 提示即可，message 可直接展示） |

## 7. 契约验收（第 1 天）

- [x] A 确认所有字段都能在页面上渲染（不需要额外请求）（2026-10-24，实测 10 接口全通过，见下方 A 签字）
- [x] C 确认价格字段与 `price_history` 结构一致（2026-10-24，见下方 C 签字）
- [x] D 确认 AI 分析接口的输入数据都能从上述接口拼出来（2026-10-23）
- [x] 四人在这份文档下各留一行"确认"记录（2026-10-24，A/B/C/D 签字齐全）
- [x] **D 签字**（2026-10-23，T1-33）：`GET /api/analysis/{player_id}` 的**固定 6 字段**（2026-10-23 决策：不输出 `suggested_price_band`，契约中该字段保留为可缺省）、4 个错误码、"AI 绝不改余额"的只读保证已写入 §4.10；规则版兜底 `code/backend/ai/fallback.py` 已实现并通过自测。（2026-10-24 更正：此行原文写"7 个字段"，与 §4.10 / §6 变更记录统一为 6 字段）
- [x] **B 签字**（2026-10-24，第 2 天契约冻结复查，B 主持）：逐条核对 10 个接口的请求/响应字段，与 §4 一致，**无新增/改名字段**；`role` 为选手真实位置、`rating` 为项目模拟综合评分（UI 必须标注"模拟"）；`hltv_rating` / `kast` / `adr` 已删除且模型、schema、种子数据、AI 上下文里均无残留；第 10 项由 D 的改动已记入 §6 变更记录并可追溯。核对方式：`/openapi.json` 路径清单 + `tests/unit/test_api_players.py` / `test_api_trades.py` 逐字段断言 + 实机 25 项验收全绿
- [x] **A 签字**（2026-10-24，第 2 天契约冻结复查，A 补签）：逐条核对 10 个接口的请求/响应字段，与 §4 一致，**全部字段可在页面渲染、无需额外请求**；`change_pct` / `profit` / `profit_pct` 直接展示后端计算值，前端不重算、不二次截断；`rating` 在市场卡片与详情页均标注「模拟数据，非官方统计」；错误体 `message` 原样展示（无映射表），业务失败**不自动重试**；AI 分析按固定 6 字段渲染、以 `source` 区分 `llm` / `rule_fallback`，AI 故障不阻塞交易展示；地址全部走 `VITE_API_BASE_URL`（源码 grep 无字面本地地址），`VITE_USE_MOCK` 开关已同步 `.env.example` 与 README。核对方式：`code/frontend/src/api/types.ts` 与 §4 逐字段对照 + 前后端实机联调全链路（查行情 → 买 2 股 → 持仓 → 卖 1 股 → 流水 + 余额不足/持仓不足/超上限/非法数量/暂停交易 5 条错误分支）实测通过
- [x] **C 签字**（2026-10-24，第 2 天契约冻结复查，C 补签）：价格相关字段与本文一致，**无新增/改名**。① `players.current_price` 为唯一权威价（定价与交易都读它），`players.prev_price` 保存上一次价格、用于算涨跌幅；② 历史表为 `price_history(price_id, player_id, price, reason, ts)`（与 `database_design.md` §2.5 一致），`ts` 为带时区 UTC（`DateTime(timezone=True)`，接口返回形如 `2026-11-01T00:00:00Z`），按 `ts` 升序返回、空数组不 404；③ `change_pct` 是接口字段（百分数数值、保留 2 位），由取整后的新价反算，保证「价格 ×（1+涨跌幅）」自洽；④ `reason` 为中文短句且必非空，落库列 `VARCHAR(200)`、写入前按 200 字符截断；⑤ 价格更新只写 `players.current_price / prev_price` 与 `price_history`，**不碰 `users.balance` / `positions` / `trades`**；⑥ 信号映射为 `S = clamp(z / Z_FULL_SCALE, -1, 1)`（`Z_FULL_SCALE=3.0`），只影响 S 的取值、**不改变任何字段口径**。核对方式：`code/core_engine/pricing.py` 与 §4.4 逐字段对照 + `tests/unit/test_pricing.py`（10 条）+ `tests/unit/test_simulator.py`（3 条，同 seed 可复现）+ `python scripts/simulate_match.py --seed 42 --json` 实测 `ts` 形态与 JSON 字段 + `code/backend/app/core/price_update.py` 落库字段对照