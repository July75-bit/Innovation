# 软件功能规范书（SRS · 功能需求）

> **负责人**：D 牵头，B 补接口条目，A 补页面条目 ｜ **截止**：第 2 天结束 ｜ **状态**：✅ 已填写（2026-10-24 补 §3 UML 领域类图；各模块异常分支第 6 天统一核对）
> **对应课程指标**：#2 需求分析、#7 各阶段交付物、#9 规范工程文档

## 1. 系统范围

三个模块 + 一个稳定层：

| 编号 | 模块 | 说明 | 负责人 |
| --- | --- | --- | --- |
| M1 | 交易平台 | 行情列表、选手详情、买入卖出、余额、持仓、流水 | A + B |
| M2 | 定价引擎 | 模拟比赛 → 表现信号 → 价格更新 → 价格历史与归因 | C |
| M3 | 智能体分析 | 基于行情生成 BUY/SELL/HOLD 建议 + 理由 + 风险 | D |
| M4 | 稳定层（兜底） | 虚拟币、交易规则、事务一致性；AI 不可用也不影响交易 | B |

## 2. 功能需求清单

> 编号规则 `FR-Mx-nn`；每条必须有：输入、处理、输出、验收方式。
> 表格里的"实现状态"在第 6 天统一核对。

### M1 交易平台

| 编号 | 功能 | 输入 | 处理 | 输出 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| FR-M1-01 | 行情列表 | — | 查询全部选手 | 名称、当前价、涨跌幅、表现评分 | 页面能看到 ≥5 名选手 | ⬜ |
| FR-M1-02 | 选手详情 | player_id | 查询选手 + 最近价格变化原因 | 价格、评分、reason | 打开详情能看到原因文案 | ⬜ |
| FR-M1-03 | 买入 | player_id, quantity | 校验 → 扣款 → 加持仓 → 写流水（同事务） | success/message/balance | 余额与持仓同步变化 | ⬜ |
| FR-M1-04 | 卖出 | player_id, quantity | 校验 → 加款 → 减持仓 → 写流水（同事务） | success/message/balance | 卖空被拒绝 | ⬜ |
| FR-M1-05 | 账户余额 | — | 查余额与总资产 | balance / total_asset | 初始 5000 | ⬜ |
| FR-M1-06 | 持仓列表 | — | 聚合持仓 + 最新价 | 数量、均价、当前估值 | 空持仓不显示 0 行 | ⬜ |
| FR-M1-07 | 交易流水 | — | 按时间倒序 | side/quantity/price/time | 每笔买卖都能追溯 | ⬜ |
| FR-M1-08 | 历史价格图 | player_id | 取价格序列 | 折线图 | 至少 10 个点 | ⬜ |

### M2 定价引擎

| 编号 | 功能 | 输入 | 处理 | 输出 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| FR-M2-01 | 模拟比赛数据 | seed | 生成得分/胜负/评级 | MatchResult | 固定 seed 结果可复现 | ⬜ |
| FR-M2-02 | 表现信号 | 最近 N 局数据 | z-score → **3σ 归一化**（`S = clamp(z / Z_FULL_SCALE, -1, 1)`，默认 `Z_FULL_SCALE=3.0`；设为 1.0 即字面口径）→ clamp 到 [-1,1] | S(t) | 不同表现得分不同 | ⬜ |
| FR-M2-03 | 价格更新 | P(t), S(t), D(t) | 方案 A 公式 | 新价格 + reason | 价格不跌破下限 | ⬜ |
| FR-M2-04 | 价格历史落库 | 新价格 | 写 price_history | 可查询序列 | 时间升序 | ⬜ |
| FR-M2-05 | 涨跌归因 | 价格变动 | 生成自然语言原因 | reason | 至少 1 升 1 降案例 | ⬜ |

**M2 参数范围与 clamp 策略**（C 补全；与 `docs/algorithm/pricing_model.md` §2 / §3 一致）

| 参数 | 默认 | 合法范围 | 越界行为 | 说明 |
| --- | ---: | --- | --- | --- |
| 表现权重 α | 0.15 | ≥ 0 | 负数 → `ValueError` | 建议 ≤ 0.3（满格 = ±α，0.3 即单次 ±30%，演示波动过大） |
| 需求权重 β | 0.0 | ≥ 0 | 负数 → `ValueError` | 初版固定 0，公式与接口预留 |
| 价格下限 floor | 1.0 | > 0 | ≤ 0 → `ValueError` | 保证价格永不为零/负 |
| 滚动窗口 N | 5 | ≥ 1（整数） | < 1 → `ValueError` | 历史不足 N 场时用已有数据，不补 0；空历史 → S=0 |
| 单次变动上限 | ±20% | 常量，写死 | 不可配 | 对称 clamp；α=0.15 时理论不触发（\|αS\| ≤ 15%） |
| 满格 σ 数 | 3.0 | 建议 0.5–10 | **无校验**，≤ 0 会除零 | 开发期开关：设为 1.0 即 `clamp(z,-1,1)` 字面口径 |
| 得分 | 0–100 | 0–100 | 非有限值 → `ValueError` | 生成阶段已截断，保证 z-score 输入合法 |
| 需求信号 D | 0.0 | [-1, 1] | 超出被 clip | 净买入占比，β=0 时不影响价格 |

**clamp 三层顺序**（任何一层都不会让价格 ≤ 0 或单次跳变超限）：

1. 信号层：`S = clip(z / 3, -1, 1)` —— 信号到不了 ±1 以上；
2. 变动层：`step = clip(α·S + β·D, -0.20, +0.20)` —— 单次变动封顶 ±20%（对称）；
3. 价格层：`new_price = max(floor, round(P × (1 + step), 2))` —— 触底停在 floor，并保留 2 位小数。

三层都有单测：`tests/unit/test_pricing.py`（对称 clamp / floor 触发 / 非法入参 / 3σ 归一化，共 11 条）。
参数优先级：**显式传参 > settings（后端配置）> 环境变量（`PRICING_ALPHA/BETA/FLOOR`）> 模块常量**。

### M3 智能体分析

| 编号 | 功能 | 输入 | 处理 | 输出 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| FR-M3-01 | 生成建议 | player_id | 取行情 → 调模型 → 校验 JSON | action/reason/risk | 三者之一 | ⬜ |
| FR-M3-02 | 非法输出兜底 | 模型异常输出 | 校验失败 → fallback | source=rule_fallback | 不返回 500 | ⬜ |
| FR-M3-03 | 无密钥降级 | 空密钥 | 跳过模型直接规则版 | 合法结构 | 交易不受影响 | ⬜ |
| FR-M3-04 | 超时保护 | — | 超时中断 | 友好错误或兜底 | 前端不挂死 | ⬜ |

## 3. 领域模型（UML 领域类图）

> 对应课程第 1 天第 2 部分要求："提交 `functional_spec.md` / `nonfunctional_spec.md`，第二周用 3 分钟展示**领域类图与功能分解**"。
> 功能分解见 §2 的 M1/M2/M3 功能需求清单；本节给领域类图（与 `docs/software/database_design.md` §1 的 ER 图同源，字段口径以 `docs/software/api_contract.md` 为准）。

```mermaid
classDiagram
    direction LR

    class User {
        +int user_id
        +str nickname
        +Decimal balance
        +Decimal initial_balance
    }
    class Player {
        +int player_id
        +str name
        +str display_name
        +str team
        +str role
        +Decimal current_price
        +Decimal prev_price
        +int rating
        +PlayerStatus status
    }
    class Position {
        +int user_id
        +int player_id
        +int quantity
        +Decimal avg_cost
        +market_value() Decimal
        +profit() Decimal
    }
    class Trade {
        +int trade_id
        +int user_id
        +int player_id
        +TradeSide side
        +int quantity
        +Decimal price
        +Decimal amount
        +Decimal balance_after
        +datetime created_at
    }
    class PriceHistory {
        +int price_id
        +int player_id
        +Decimal price
        +str reason
        +datetime ts
    }
    class TradingService {
        <<service>>
        +buy(user_id, player_id, quantity) Trade
        +sell(user_id, player_id, quantity) Trade
        +validate_balance(amount) void
        +validate_position(held, quantity) void
    }
    class PricingService {
        <<service>>
        +update_price(price, signal) PriceUpdate
        +standardize_score(recent) float
    }
    class AdviceService {
        <<service>>
        +build_context(player_id) dict
        +analyze(context) Advice
        +rule_based_advice(context) Advice
    }
    class TradeSide {
        <<enumeration>>
        BUY
        SELL
    }
    class PlayerStatus {
        <<enumeration>>
        trading
        suspended
    }
    class Action {
        <<enumeration>>
        BUY
        SELL
        HOLD
    }
    class RiskLevel {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
    }

    User "1" --> "0..*" Position : 持有
    Player "1" --> "0..*" Position : 被持有
    User "1" --> "0..*" Trade : 产生
    Player "1" --> "0..*" Trade : 被交易
    Player "1" --> "0..*" PriceHistory : 有历史
    Trade --> TradeSide
    Player --> PlayerStatus
    AdviceService ..> Action
    AdviceService ..> RiskLevel

    TradingService ..> User
    TradingService ..> Player
    TradingService ..> Position
    TradingService ..> Trade
    PricingService ..> Player
    PricingService ..> PriceHistory
    AdviceService ..> Player
    AdviceService ..> Position
    AdviceService ..> PriceHistory
```

**类到实现的映射（3 分钟汇报可直接照这张表讲）**

| 领域类 / 服务 | 代码 / 数据表 | 说明 |
| --- | --- | --- |
| `User` / `Player` / `Position` / `Trade` / `PriceHistory` | `app/models/*.py` ↔ `users` / `players` / `positions` / `trades` / `price_history` 5 张表 | 实体类与表一一对应，关系见 `database_design.md` §1 |
| `TradingService` | `app/api/trades.py` + `app/core/rules.py` | 事务边界：余额/持仓/流水同事务；失败整体回滚，余额不会扣成负数 |
| `PricingService` | `code/core_engine/pricing.py` | 纯计算，不写库；返回新价格 + 归因 `reason`，由调用方落 `price_history` |
| `AdviceService` | `code/backend/ai/context.py` + `llm_agent.py` + `fallback.py` | **只读**：只 SELECT，不 commit；模型不可用时规则版返回同一结构 |
| `TradeSide` / `PlayerStatus` / `Action` / `RiskLevel` | 常量与枚举校验 | 契约冻结的枚举值；非法值一律拒绝或回落 |

**设计边界**：AI 只产出 `Action` 建议，不进入 `TradingService`；交易正确性由 `TradingService` 的规则与事务保证（见 `docs/software/architecture.md` §5 ADR）。

## 4. 非核心/可选功能（有余力再做）

- 每日签到补虚拟币
- 收益率排行榜
- 赛季结算奖励
- 资产净值时间序列图
- LMSR 做市商（方案 C 彩蛋）

## 5. 需求 ↔ 测试 追溯

每个 FR 编号必须能在 `docs/acceptance/test_plan.md` 找到至少一条对应用例，验收时逐条勾选。

## 6. TODO

- [ ] B 补全 M1 的异常分支（余额不足/持仓不足/非法数量/无效选手/暂停交易）
- [x] C 补全 M2 的参数范围与 clamp 策略（见 M2 章节后的「参数范围与 clamp 策略」表 + 三层 clamp 顺序；与 `pricing_model.md` §2/§3 一致）
- [ ] D 补全 M3 的降级链路时序
