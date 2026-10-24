# 测试计划

> **负责人**：D ｜ **截止**：第 4 天定稿，第 5–6 天执行 ｜ **状态**：✅ 已填写（用例已列，第 4–6 天执行打勾）
> **对应课程指标**：#9 测试计划与报告、#10 单元/集成/系统测试；交付物清单第 4 项

## 1. 测试目标

验证三件事，其余都是附加：

1. **交易规则绝对正确**：余额、持仓、流水三者一致，不超卖、不超上限、不出现负余额；
2. **AI 不会拖垮系统**：模型不可用时交易与行情照常可用；
3. **线上环境真的能用**：不是"本地能跑"，是"老师打开网址能用"。

## 2. 测试层次与范围

| 层次 | 范围 | 工具 | 负责人 | 目录 |
| --- | --- | --- | --- | --- |
| 单元测试 | 定价算法、交易校验函数 | pytest | B、C | `tests/unit/` |
| 接口测试 | 全部 10 个 API 的正常/异常分支 | pytest + TestClient | B、D | `tests/unit/` |
| 集成测试 | 完整交易闭环、AI 降级 | pytest | D | `tests/integration/` |
| 系统测试 | 浏览器端到端手工验证 | 手工 + 清单 | A、D | 本标准第 5 节 |
| 验收测试 | 对照用户故事 AC 逐条验证 | 手工 | 全员 | `docs/requirements/user_stories.md` |
| 线上验收 | 部署后全流程 | 手工 | 全员 | `docs/software/deployment.md` 第 5 节 |

## 3. 测试环境

| 项 | 本地 | 线上 |
| --- | --- | --- |
| OS | Windows 11 | Render（Linux） |
| Python | 3.12/3.13 | 3.12.6 |
| Node | LTS | 20 |
| 数据库 | SQLite 本地文件 | SQLite + 持久盘 / PostgreSQL |
| 数据 | `data/seed_players.json`（8 名选手） | 同 |
| LLM | 可无密钥（走兜底） | 同 |

## 4. 测试用例清单

> `TC-xxx` 编号与 `docs/requirements/functional_spec.md` 的 FR 编号对应。

### 4.1 交易规则（最高优先级）

| ID | 用例 | 输入 | 期望 | 对应 FR | 关联风险 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-001 | 正常买入 | 余额 5000，价 126.00，买 2 | 余额 4748.00，持仓 +2，流水 +1 | FR-M1-03 | — | ✅ `test_trades_rule.py::test_buy_normal` + e2e 买入链路 |
| TC-002 | 余额不足买入 | 余额 50，价 126.00，买 1 | 400 `INSUFFICIENT_BALANCE`，三者不变 | FR-M1-03 | R06 | ✅ `test_buy_insufficient_balance` |
| TC-003 | 数量为 0 | quantity=0 | 422 | FR-M1-03 | — | ✅ `test_buy_invalid_quantity[0]` |
| TC-004 | 数量为负 | quantity=-1 | 422 | FR-M1-03 | — | ✅ `test_buy_invalid_quantity[-1]` |
| TC-005 | 数量为小数 | quantity=1.5 | 422 | FR-M1-03 | — | ✅ `test_buy_invalid_quantity[1.5]` |
| TC-006 | 选手不存在 | player_id=999 | 404 `PLAYER_NOT_FOUND` | FR-M1-03 | — | ✅ `test_buy_invalid_player` + e2e 404 断言 |
| TC-007 | 超过持仓上限 | 已持 50，再买 1 | 400 `POSITION_LIMIT_EXCEEDED` | FR-M1-03 | — | ✅ `test_buy_exceeds_position_limit` |
| TC-008 | 正常卖出 | 持 3，卖 1 | 余额 +，持仓 2，流水 +1 | FR-M1-04 | — | ✅ `test_sell_normal` + e2e 卖出链路 |
| TC-009 | 持仓不足卖出 | 持 0，卖 1 | 400 `INSUFFICIENT_POSITION`，不产生负持仓 | FR-M1-04 | R06 | ✅ `test_sell_more_than_held` |
| TC-010 | 暂停交易 | status=suspended 时买卖 | 400 `PLAYER_TRADING_SUSPENDED` | FR-M1-03/04 | — | ✅ `test_buy_suspended_player` |
| TC-011 | 价格变动后成交 | 更新价格后立即买入 | 按**最新价**成交 | FR-M1-03 | — | ✅ `test_trade_uses_latest_price` |
| TC-012 | 事务回滚 | 制造写入失败（如非法 player 外键） | 余额/持仓/流水都未变 | FR-M1-03 | R06 | ✅ `test_transaction_rollback_on_failure` |

> **执行记录（2026-10-24 第 3 天，D）**：全仓 `python -m pytest` → **65 passed / 5 skipped**（`test_trades_rule.py` 14 项、`test_api_trades.py` 6 项、`test_trades_concurrency.py` 3 项、`test_e2e_flow.py` 2 项）；TC-001~012 全部有自动化覆盖。
> 显式 skip 只剩定价 5 条（TC-101~107，等 C 的 PR）。测试总数 70（65+5），逐文件明细见 `test_report.md` §2。

### 4.2 定价引擎

| ID | 用例 | 输入 | 期望 | 对应 FR | 状态 |
| --- | --- | --- | --- | --- | --- |
| TC-101 | 表现上升价格上涨 | P=100, S=+0.5, α=0.2 | 110.00 | FR-M2-03 | ✅ `test_pricing.py::test_price_rises_when_score_positive` |
| TC-102 | 表现下降价格下跌 | P=100, S=-0.5, α=0.2 | 90.00 | FR-M2-03 | ✅ `test_price_falls_when_score_negative` |
| TC-103 | 无信号价格不变 | S=0, D=0 | 100.00 | FR-M2-03 | ✅ `test_zero_demand_signal_keeps_price_when_score_zero` |
| TC-104 | 触及价格下限 | P=2, S=-1, α=5 | ≥ floor，且不为负 | FR-M2-03 | ✅ `test_price_never_below_floor` + `test_floor_applies_after_clamp` |
| TC-105 | 非法入参 | P=0 | `ValueError` | FR-M2-03 | ✅ `test_invalid_current_price_raises` |
| TC-106 | 模拟可复现 | 同 seed 跑两次 | 结果完全一致 | FR-M2-01 | 🟡 模拟器已实现（`generate_match(seed=...)`），但**缺同 seed 可复现的自动化断言**，建议 C 补 |
| TC-107 | 历史升序 | 多次更新后查询 | ts 严格升序 | FR-M2-04 | ✅ e2e 价格历史升序断言 + `test_price_update.py::test_apply_updates_writes_price_and_history` |
| TC-108 | 表现信号 3σ 归一化 | z=1.5，`Z_FULL_SCALE`=3.0 / 1.0 | 3.0 时 S=0.5；1.0 时 clamp 为 1.0；z=0 → 0 | FR-M2-02 | ✅ 2026-10-24（C 补：`test_standardize_score_three_sigma_scale` 断言 1σ→0.333/2σ→0.667/3σ→1.0/>3σ 饱和；`test_z_full_scale_one_matches_literal_mapping` 验证开关） |
| TC-109 | 单次变动对称 clamp ±20% | 原始涨幅 > 20% | 涨跌都封顶 ±20%，`reason` 注明已按上限执行 | FR-M2-03 | ✅ `test_step_is_capped_symmetrically` |
| TC-110 | 价格历史 reason 可追溯（方案 A） | C 的 `simulate_match.py --json` 导出 → B 的 `update_prices.py --from-json` 落库 | `/api/players/{id}/prices` 每条模拟调价 reason 同时含 `S=` 与本轮模拟得分；换会话/读库后仍可读（进程级重启由 T3-05 覆盖），价格升序 | FR-M2-04 / FR-M2-05 | ✅ 2026-10-24（`tests/integration/test_price_reason_traceability.py` 4 条：from-json / 进程内引擎 / 落库+API / 200 字截断） |

> **决策（2026-10-24）**：不新增 `score` 列或 `matches` 表（选项 B），改为把 `S(t)` 与本轮模拟得分写进 `reason`（选项 A）。
> 理由：不改表/契约，详情页、AI 上下文、答辩讲解都能直接用到；精确复现靠 `simulate_match.py` 固定 seed + reason 里的得分对齐。
> 当前实现：B 在落库层临时拼接“本轮模拟得分”（`update_prices.with_score_in_reason`），C 接管后由 C 直接拼好、B 只透传（见 `database_design.md` §3.2 分工待办）。详见 `architecture.md` §5 ADR。

> **执行记录（2026-10-24 11:00，D）**：A 前端初版、C 定价实现、B 价格落库脚本合入后，全仓 `python -m pytest` → **79 passed / 0 skipped**；
> 定价 8 条（`test_pricing.py`）+ 价格落库 6 条（`test_price_update.py`）全部转绿；TC-106/108 两条数值断言待 C 补。
>
> **执行记录（2026-10-24 11:00 后，D 复核）**：C 补 3σ 断言（`dfe9f26`）后再跑 → **81 passed / 0 skipped**（`test_pricing.py` 8→10 条）；TC-108 转 ✅，仅剩 TC-106 同 seed 可复现断言待补。
>
> **执行记录（2026-10-24 11:45，D）**：B 的 `--from-json` + reason 拼接（`adcc848`/`24496ee`）合入，加 D 的 TC-110 4 条后全仓 → **92 passed / 0 skipped**（另含 B 的 `test_update_prices_script.py` 7 条）。

### 4.3 AI 智能体

| ID | 用例 | 输入 | 期望 | 对应 FR | 状态 |
| --- | --- | --- | --- | --- | --- |
| TC-201 | 正常分析 | 有效选手 | 200，action ∈ {BUY,SELL,HOLD} | FR-M3-01 | ✅ 2026-10-23（接口层：假 client 合法输出 → `source=llm`） |
| TC-202 | 无密钥降级 | 清空密钥 | 200，`source=rule_fallback` | FR-M3-03 | ✅ 2026-10-23（单元层 + 接口层） |
| TC-203 | 模型返回非 JSON | mock 脏输出 | 不 500，返回兜底 | FR-M3-02 | ✅ 2026-10-23（单元层 + 接口层） |
| TC-204 | 模型超时 | mock 延迟 > 20s | 按时返回兜底 | FR-M3-04 | 🟡 逻辑/接口层已过（注入超时 client → 200 兜底）；真实 20s 延迟未压测 |
| TC-205 | AI 不改数据 | 调分析接口前后对比 | 余额/持仓完全不变 | FR-M3-01 | ✅ 2026-10-23（接口层：`/api/account` + `/api/positions` 前后完全一致） |
| TC-206 | 密钥不外泄 | 抓包/看前端产物 | 响应与 bundle 中无密钥 | FR-M3-01 | 🟡 接口层已过（响应不含密钥）；前端 bundle 与线上待查 |

> **执行记录（2026-10-23，D）**：`tests/unit/test_llm_agent.py` 13 条 + `tests/unit/test_ai_fallback.py` 6 条，用注入假 client 在无密钥环境跑通。
> **第 3 天接口层补测（2026-10-23，D）**：`GET /api/analysis/{player_id}` 已接入，`tests/unit/test_api_ai.py` 7 条 + `tests/integration/test_e2e_flow.py` 2 条，
> 覆盖 TC-201/202/203/205/206 与全链路联调；AI 故障（超时 / 脏输出）均由假 client 注入验证为 200 + 兜底，不碰真实网络。
> 真实模型路径（有密钥）与 TC-206 的前端产物/线上抓包仍留待部署后（第 5 天）验证。

### 4.4 前端与体验

| ID | 用例 | 期望 | 状态 |
| --- | --- | --- | --- |
| TC-301 | 行情列表渲染 | 8 行，价格 2 位小数，涨跌带色 | ⬜ |
| TC-302 | 买卖后自动刷新 | 余额/持仓/流水同步更新，不用手动刷新 | ⬜ |
| TC-303 | 错误提示 | 后端 message 中文直出 | ⬜ |
| TC-304 | 加载中/无数据/失败三态 | 三种状态都有 UI | ⬜ |
| TC-305 | 折线图 | ≥10 个点，时间升序 | ⬜ |
| TC-306 | AI 建议卡 | action 徽标 + 理由 + 风险等级 + 免责声明 | ⬜ |
| TC-307 | 刷新页面数据仍在 | F5 后数据不变 | ⬜ |

### 4.5 部署与系统

| ID | 用例 | 期望 | 状态 |
| --- | --- | --- | --- |
| TC-401 | 线上健康检查 | `/api/health` 返回 ok | ⬜ |
| TC-402 | 线上 CORS 正常 | 前端无跨域报错 | ⬜ |
| TC-403 | 线上交易闭环 | 买卖成功入库 | ⬜ |
| TC-404 | 重启后数据持久 | 重新部署后数据仍在 | ⬜ |
| TC-405 | 前端子路由刷新 | `/positions` 刷新不 404 | ⬜ |
| TC-406 | 无密钥全站可用 | 拔掉密钥后交易/行情正常 | ⬜ |

## 5. 手工系统测试流程（浏览器）

按顺序走一遍，任何一步失败都记入缺陷：

1. 打开首页 → 看到 8 名选手、价格、涨跌幅、评分
2. 点进 ZywOo 详情 → 看到价格、折线图、涨跌原因
3. 记录当前余额（应为 5000）
4. 买入 2 股 → 余额 4748.00、持仓出现 ZywOo ×2、流水新增 BUY
5. **按 F5 刷新** → 数据保持
6. 卖出 1 股 → 余额增加、持仓 1 股、流水新增 SELL
7. 尝试买入 9999 股 → 显示"余额不足"
8. 尝试卖出 999 股 → 显示"持仓不足"
9. 点 AI 分析 → 看到 BUY/SELL/HOLD + 理由 + 风险等级 + 免责声明
10. 关闭网络/断开后端 → 页面显示失败态而不是白屏
11. 线上地址重复 1–9 步

## 6. 缺陷分级与出口标准

| 等级 | 定义 | 例子 |
| --- | --- | --- |
| P0 阻断 | 交易不能进行 / 数据错乱 | 余额变负、超卖、页面白屏 |
| P1 严重 | 主流程可用但有错 | 买入后不刷新、AI 接口 500 |
| P2 一般 | 体验问题 | 数字格式、颜色、错别字 |
| P3 建议 | 优化项 | 动画、排序 |

**出口标准（满足才允许答辩）**：

- [ ] P0 缺陷 = 0
- [ ] P1 缺陷 = 0（或已明确记录为已知问题并说明原因）
- [ ] 全部 TC-0xx（交易规则）通过
- [ ] 全部 TC-4xx（部署）通过
- [ ] 线上演示流程完整走通 ≥2 次
