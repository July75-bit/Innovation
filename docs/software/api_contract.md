# 前后端接口契约（API Contract）

> **负责人**：B（定稿） ｜ **截止**：**第 1 天必须确认**，之后不得随意改字段 ｜ **状态**：⬜ 待四人签字确认
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
| 2 | GET | `/api/players` | 市场选手列表 | A + B | ⬜ |
| 3 | GET | `/api/players/{player_id}` | 单个选手详情 | A + B | ⬜ |
| 4 | GET | `/api/players/{player_id}/prices` | 价格历史 | A + B + C | ⬜ |
| 5 | GET | `/api/account` | 账户余额 | A + B | ⬜ |
| 6 | GET | `/api/positions` | 持仓列表 | A + B | ⬜ |
| 7 | POST | `/api/trades/buy` | 买入 | A + B | ⬜ |
| 8 | POST | `/api/trades/sell` | 卖出 | A + B | ⬜ |
| 9 | GET | `/api/trades` | 交易流水 | A + B | ⬜ |
| 10 | GET | `/api/analysis/{player_id}` | AI 分析建议 | A + B + D | ⬜ |

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
    "name": "Shadow",
    "display_name": "影刃",
    "team": "NOVA",
    "current_price": 103.50,
    "prev_price": 100.00,
    "change_pct": 3.50,
    "rating": 82,
    "status": "trading"
  }
]
```

> `status ∈ {trading, suspended}`；`change_pct` 后端算好，前端不要自己算。

### 4.3 `GET /api/players/{player_id}`

```json
{
  "player_id": 1,
  "name": "Shadow",
  "display_name": "影刃",
  "team": "NOVA",
  "current_price": 103.50,
  "prev_price": 100.00,
  "change_pct": 3.50,
  "rating": 82,
  "status": "trading",
  "latest_reason": "模拟比赛表现提升（近 3 场均分 88，S=+0.42）"
}
```

404 → `PLAYER_NOT_FOUND`。

### 4.4 `GET /api/players/{player_id}/prices`

```json
{
  "player_id": 1,
  "points": [
    { "ts": "2026-01-01T10:00:00Z", "price": 100.00, "reason": "初始价格" },
    { "ts": "2026-01-01T10:05:00Z", "price": 103.50, "reason": "模拟比赛表现提升" }
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
    "name": "Shadow",
    "quantity": 10,
    "avg_cost": 98.00,
    "current_price": 103.50,
    "market_value": 1035.00,
    "profit": 55.00,
    "profit_pct": 5.61
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
  "balance": 4800.00,
  "player_id": 1,
  "quantity": 2,
  "price": 100.00,
  "trade_id": 17
}
```

失败 400 示例：

```json
{ "success": false, "message": "余额不足，当前余额 50.00，需要 100.00", "code": "INSUFFICIENT_BALANCE" }
```

校验顺序（B 必须按此顺序，便于前端给准确提示）：

1. `player_id` 存在 → 否则 404
2. `quantity` 为正整数 → 否则 422
3. 选手 `status == trading` → 否则 400
4. 余额充足 → 否则 400
5. 买入后持仓 ≤ 50 → 否则 400
6. 事务内扣款 + 加持仓 + 写流水 → COMMIT

### 4.8 `POST /api/trades/sell`

请求同买入。成功：

```json
{
  "success": true,
  "message": "卖出成功",
  "balance": 4900.00,
  "player_id": 1,
  "quantity": 1,
  "price": 100.00,
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
    "name": "Shadow",
    "side": "SELL",
    "quantity": 1,
    "price": 100.00,
    "amount": 100.00,
    "balance_after": 4900.00,
    "created_at": "2026-01-01T10:10:00Z"
  }
]
```

`side ∈ {BUY, SELL}`。

### 4.10 `GET /api/analysis/{player_id}`

```json
{
  "player_id": 1,
  "action": "BUY",
  "reason": "近 3 场表现评分由 74 升至 82，价格上涨 3.5% 但低于表现提升幅度",
  "risk_level": "MEDIUM",
  "suggested_price_band": { "low": 100.00, "high": 108.00 },
  "source": "llm",
  "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
}
```

- `action ∈ {BUY, SELL, HOLD}`，`risk_level ∈ {LOW, MEDIUM, HIGH}`
- `source ∈ {llm, rule_fallback}`：**无论模型是否可用，本接口都必须 200 且结构合法**
- 本接口**永不**修改余额/持仓，只读

---

## 5. 字段命名对照（防扯皮表）

| 含义 | ✅ 统一叫法 | ❌ 不要出现 |
| --- | --- | --- |
| 选手主键 | `player_id` | `id`, `pid`, `playerId` |
| 当前价格 | `current_price` | `price`, `currentPrice`, `now_price` |
| 上一价格 | `prev_price` | `last_price` |
| 涨跌幅（%） | `change_pct` | `change`, `pct`, `chg` |
| 表现评分 | `rating` | `score`, `performance` |
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
| | 初版定稿 | B | A/B/C/D |

## 7. 契约验收（第 1 天）

- [ ] A 确认所有字段都能在页面上渲染（不需要额外请求）
- [ ] C 确认价格字段与 `price_history` 结构一致
- [ ] D 确认 AI 分析接口的输入数据都能从上述接口拼出来
- [ ] 四人在这份文档下各留一行"确认"记录
