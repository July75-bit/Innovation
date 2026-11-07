# Agent 工作流模式选型与完善路线（产品视角）

> 参考：bettermorn/AIAgent `docs/AIAgentConcept.md`（常见 Agent 工作流模式对比、设计通用建议）
> 角色：程序产品经理 ｜ 日期：2026-10-24 ｜ 状态：待评审
> 关联文档：`docs/algorithm/ai_agent_prompt.md`、`docs/software/architecture.md`、`docs/software/api_contract.md` §4.10

## 1. 现状盘点

| 维度 | 现状 |
|---|---|
| Agent 类型（按自主程度分级） | 辅助决策型（Copilot）：只输出 BUY/SELL/HOLD 建议，用户确认后手动交易，AI 不修改余额/持仓 |
| 已采用模式 | 基础单次调用；异常恢复（无密钥/超时/脏输出 → 规则版兜底）；Human-in-the-Loop（产品层天然存在） |
| 已符合的生产建议 | 统一结构化输出（固定 6 字段）；单次调用超时（20s）；密钥只在后端；AI 故障不升级为 4xx/5xx |

结论：定位正确。资金类高风险决策应采用「Agent 辅助 + 规则约束 + 人工确认」，与本项目合规声明（不自动交易）一致。

## 2. 模式选型

### 2.1 应补强

| 模式 | 为什么适合 | 落点 |
|---|---|---|
| Reflection | 现校验只管格式不管内容；reason 数值可能是幻觉。加 Critic：数值可在 context 溯源、action 与 risk_level 自洽；不通过带反馈重试 1 次（步数上限 2），仍失败走规则版 | `code/backend/ai/llm_agent.py` 新增 `_critique()` |
| Router | 分析入口增多（单选手 / 组合诊断 / 大盘报告）后按意图分发，避免单一大 prompt | `code/backend/app/api/ai.py` 路由层 |
| 并行 Agent | 赛后大盘日报：全部选手并行分析 + 汇总，容忍部分失败 | `scripts/daily_report.py`（新增） |
| RAG（可选） | 检索 `mechanism_design.md` / 定价模型文档，回答「为什么涨价」，与价格原因溯源互补 | 后端新增问答端点 |

### 2.2 明确不采用（及理由）

- ReAct / Plan-and-Execute / Supervisor / 全自主型：本任务是单步、确定上下文的分析任务；引入循环推理带来延迟、成本与幻觉不可控，且与「AI 不自动交易」合规定位冲突。对应文章通用建议第 1 条：简单任务优先使用简单流程。

## 3. 完善路线图

### P0（~1 天）
1. `_critique(result, context)`：reason 数值溯源校验 + 枚举自洽；失败注入评审意见重试 1 次；最终失败 `source="rule_fallback"`（可细分标记 critic 拦截）。
2. 调用审计日志：player_id、耗时、重试次数、降级原因、token 估算（logging 起步，后续可建 `ai_advice_log` 表）。
3. 幂等缓存：键 = `player_id + 最新价格 ts`，价格未变直接返回缓存，控成本。

### P1（2–3 天）
1. `GET /api/analysis/portfolio`：Router 模式，组合级建议（`context.py` 已能组装 position）。
2. 护栏配置化：最大重试次数 / 总超时 / 单日 token 预算进 `settings`。

### P2（答辩加分项）
1. 赛后并行大盘日报（并行 Agent + 汇总 Critic + 部分失败容忍）。
2. 可观测性指标：降级率、平均耗时、Critic 拦截率、缓存命中率。

## 4. 护栏与可观测性清单（对齐文章生产建议）

- [x] 单次调用超时（llm_timeout_seconds=20）
- [x] 失败降级策略（rule_fallback，永不阻塞交易）
- [x] 统一输出格式（固定 6 字段 JSON）
- [ ] 最大重试次数（P0：Critic 重试上限 1）
- [ ] 工具调用审计日志（P0）
- [ ] 幂等键（P0：缓存键）
- [ ] 最大 token 消耗 / 单日预算（P1）
- [ ] 可观测性面板指标（P2）

## 5. 验收口径

- P0 验收：构造「reason 引用不存在数值」的脏输出用例，Critic 能拦截并最终回落规则版；审计日志含降级原因；同价格重复请求命中缓存。
- 单测落点：`tests/unit/test_llm_agent.py` 扩展 Critic 分支（沿用可注入 chat 的既有设计，无需网络）。
