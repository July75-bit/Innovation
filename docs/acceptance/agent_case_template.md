# 智能体测试用例模板实例（课件 p.189 模板）

> **对应课件**：SWIEP.pdf p.189 给的用例模板字段：`id / title / layer / priority / trace / preconditions / input / steps / expected / status`。
> 我们的用例以 **pytest 函数**承载（字段映射见 `agent_test_layers.md` §六），本文件按课件模板**逐字段**写出 3 个代表例，
> 方便对照评分：评委能直接把 `id` 对到 `tests/eval/` 里的函数名。

---

## 例 1：边界诚实（L3 集成 · P0）

```yaml
id: IT-AI-01
title: 不存在的选手不进入模型，直接 404
layer: 集成 (L3)
priority: P0
trace: [FR-AI-01, 契约 §4.10]
preconditions:
  - TestClient 注入临时 SQLite（tests/conftest.py 的 client 夹具）
  - 真实 db 中不存在 player_id=999
input:
  player_id: 999
steps:
  - GET /api/analysis/999
expected:
  - status == 404
  - body.code == PLAYER_NOT_FOUND
  - "action" not in body          # 没有编造建议
  - "reason" not in body
  - 响应耗时 < 500ms 且不触发 LLM  # 说明没进模型
status: active
实现: tests/unit/test_api_ai.py::test_analysis_unknown_player_returns_404
```

## 例 2：降级契约（L3 集成 · P0）

```yaml
id: IT-AI-02
title: 模型输出非法/超时 → 200 + source=rule_fallback，6 字段齐全
layer: 集成 (L3)
priority: P0
trace: [契约 §4.10, NFR-可用性]
preconditions:
  - 注入 fake_llm 返回非法 JSON（tests/conftest.py 的 fake_llm 夹具）
input:
  player_id: 1
steps:
  - GET /api/analysis/1
expected:
  - status == 200
  - body.source == "rule_fallback"
  - set(body) == {player_id, action, reason, risk_level, source, disclaimer}
  - body.disclaimer 含「不构成投资建议」
  - 账户余额与持仓不变（只读性）
status: active
实现: tests/unit/test_api_ai.py::test_llm_dirty_output_still_returns_200_fallback
```

## 例 3：红队结构防御（L5 · P0）

```yaml
id: RT-AI-03
title: 模型夹带额外字段 / 伪造 source 一律丢弃
layer: L5 红队
priority: P0
trace: [契约 §4.10, 安全-1]
preconditions:
  - fake_llm 返回 {"action":"HOLD","risk_level":"MEDIUM","suggested_price_band":[1,9999],"source":"hacked"}
input:
  player_id: 1
steps:
  - analyze(context, chat=fake_llm)
expected:
  - set(result) == 6 个字段
  - result.source == "llm"          # 由服务端决定，不取模型值
  - "suggested_price_band" not in result
  - result.disclaimer == DISCLAIMER # 不可被模型覆盖
status: active
实现: tests/eval/test_agent_redteam.py::test_redteam_extra_fields_are_dropped
```

---

## 字段映射（我们的 pytest 写法 ↔ 课件模板）

| 课件字段 | 我们落点 |
| --- | --- |
| `id` | 函数名（如 `test_redteam_extra_fields_are_dropped`）+ 本文件的 `IT-AI-xx` / `RT-AI-xx` 编号 |
| `title` | 函数 docstring 第一行 |
| `layer` | 目录：`tests/unit`（L1/L2/L3）、`tests/eval`（L4/L5） |
| `priority` | `test_plan.md` §4 的优先级列；红队/安全一律 P0 |
| `trace` | `test_plan.md` 的「对应 FR」列 + `api_contract.md` 章节 |
| `preconditions` | pytest fixture（`client` / `fake_llm` / `tmp_path`） |
| `input` | 函数参数 / 构造的 context |
| `steps` | 函数体（AAA：Arrange–Act–Assert） |
| `expected` | `assert` 语句 |
| `status` | `test_plan.md` 状态列；已知缺陷曾用 xfail，现已全部修复无 xfail |

> **为什么用 pytest 而不是 YAML 驱动**：YAML 模板便于评审阅读，但真正执行要另写解释器；
> 我们把「模板字段」写进 docstring + 本文件做对照，执行仍用 pytest——**一份用例、两个视角**，不重复维护。
