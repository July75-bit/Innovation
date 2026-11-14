# 测试报告

> **负责人**：D ｜ **截止**：第 6 天 ｜ **状态**：🟡 第 3–5 天已回填自动化 + 浏览器 + 线上验收证据；待第 6 天答辩材料/回归
> **对应交付物清单第 4 项**：测试用例集与测试报告（含交易规则边界测试、定价引擎单元测试）

> 填表规则：**只填真实跑出来的结果**。没跑的写"未执行"，不要写"通过"充数。

## 1. 执行概况

| 项 | 内容 |
| --- | --- |
| 测试日期 | 2026-10-24（第 3 天末 + 第 4 天） |
| 执行人 | D（王泽棠） |
| 代码版本 | `develop` 分支第 3 天提交（含 B 的价格落库、C 的定价实现、A 的前端初版、D 的代码质量重构；`git log --oneline -1`） |
| 环境 | 本地 Windows + conda `playerstock`（Python 3.13.14）；CI：GitHub Actions ubuntu-latest（Python 3.12） |
| 自动化用例总数 | **264**（单元 210 / 集成 21 / 评测 33） |
| 通过 / 失败 / 跳过 | **264 / 0 / 0**（CI ubuntu-latest 与本机 Windows 均全绿；原 BUG-03 编码问题已修，见 §9 BUG-10） |
| 手工用例总数 | ✅ 已执行（T3-04/T4 浏览器证据 16 张，见 §2.5） |
| 通过 / 失败 | 16 张证据截图全过 / 0 |

> 复跑说明（2026-10-25，B 核对）：总数由 **137** 条组成——C 的 `test_simulator.py`（+3，TC-106）、
> `test_price_reason_traceability.py`（+4）、`test_prices_recalc.py`（+5，第 4 天 recalc 接口）、
> B 的 `test_update_prices_script.py`（9 条）、D 的 `test_core_exceptions.py`（+7）、
> C 的 `test_simulate_match_cli.py`（+2）、`test_pricing.py`（11 条）、
> B 的部署预检 `test_config_db_url.py`（+6）与 `test_bootstrap_demo_data.py`（+2）、
> 第 5 天 B 的 `test_cors_config.py`（+8，CORS 策略 + 线上误配回归）、`test_debug_api.py`（+3，只读自检接口）
> 与 `test_trade_rules_unit.py` 增至 11 条（+6，错误文案"下一步"）。
> CI（ubuntu-latest）全绿；本机 Windows 亦全绿——原先那 1 failed + 1 error 是测试代码的编码问题
> （BUG-03），B 已修并复现验证，见 §9。

## 2. 自动化测试结果

### 2.1 单元测试

```text
$ python -m pytest -q          # CI ubuntu-latest
265 passed
$ python -m pytest -q          # 本机 Windows（BUG-03 编码问题已修）
265 passed, 1 warning in 16.70s
```

> 用例数演进：第 4 天 65 → 第 5 天 137 → 第 6 天守卫 39 条 → **265**（单元 211 / 集成 21 / 评测 33；
> 含 auth 22+7、重灌端点 4、余额重建 2 等；`--collect-only` 分目录复核）。

| 文件 | 用例数 | 通过 | 失败 | 跳过 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `tests/unit/test_health.py` | 2 | 2 | 0 | 0 | |
| `tests/unit/test_api_players.py` | 7 | 7 | 0 | 0 | 市场/详情/价格历史/账户/持仓 |
| `tests/unit/test_api_trades.py` | 6 | 6 | 0 | 0 | B 第 2 天新增，守交易返回契约 |
| `tests/unit/test_trades_rule.py` | 14 | 14 | 0 | 0 | 9 条 skip 已全部转绿 |
| `tests/unit/test_trade_rules_unit.py` | 11 | 11 | 0 | 0 | 纯规则函数；第 5 天 +6 条守"错误文案要给下一步"（最多可买/还能买/可卖） |
| `tests/unit/test_trades_concurrency.py` | 3 | 3 | 0 | 0 | B 第 2 天新增，并发/条件更新 |
| `tests/unit/test_price_update.py` | 6 | 6 | 0 | 0 | B 第 3 天新增，价格落库脚本（只改 players/price_history） |
| `tests/unit/test_update_prices_script.py` | 9 | 9 | 0 | 0 | B 第 3 天新增：`--from-json` / 跳过 suspended / 同 seed 可复现 / reason 幂等不双写 / 非法输入 |
| `tests/unit/test_pricing.py` | 11 | 11 | 0 | 0 | C 第 3 天实现（第 4 天增至 11 条）：含 3σ 归一化、`Z_FULL_SCALE` 开关与 reason 带得分断言 |
| `tests/unit/test_simulator.py` | 3 | 3 | 0 | 0 | C 第 3 天新增，TC-106：同 seed 序列逐条相等 / 单场稳定 / 换 seed 必变 |
| `tests/unit/test_simulate_match_cli.py` | 2 | 2 | 0 | 0 | C 第 3 天补：`simulate_match.py` CLI 冒烟（8 条输出 + `ts` ISO 8601） |
| `tests/unit/test_ai_fallback.py` | 6 | 6 | 0 | 0 | 规则版兜底 |
| `tests/unit/test_llm_agent.py` | 13 | 13 | 0 | 0 | 注入假 client，不碰网络 |
| `tests/unit/test_api_ai.py` | 7 | 7 | 0 | 0 | `/api/analysis` 接口契约/只读/降级 |
| `tests/unit/test_core_exceptions.py` | 7 | 7 | 0 | 0 | T4-06：卖出暂停/未知选手、缺字段 422、未知价格历史 404、卖超回滚 |
| `tests/unit/test_config_db_url.py` | 6 | 6 | 0 | 0 | B 部署预检新增：`postgres://`/裸 `postgresql://` 补成 `+psycopg2`、显式驱动不改写、建引擎解析到 psycopg2、SQLite 相对路径归一化 |
| `tests/unit/test_cors_config.py` | 8 | 8 | 0 | 0 | 第 5 天 B 新增：CORS 策略（配了域名→白名单 / 显式 `*`→放开+告警 / 空→退化+告警 / **线上仍用本地默认值→退化+告警**）、尾斜杠归一化，依据 NFR-S-04 |
| `tests/unit/test_debug_api.py` | 3 | 3 | 0 | 0 | 第 5 天 B 新增：只读自检接口 `GET /api/debug/db`（只回元信息、不泄露连接串、`DEBUG_ENDPOINTS=0` 可关） |

### 2.2 集成测试

| 文件 | 用例数 | 通过 | 失败 | 备注 |
| --- | --- | --- | --- | --- |
| `tests/integration/test_e2e_flow.py` | 2 | 2 | 0 | 全链路（查行情→买入→持仓→流水→卖出→账户→AI 建议）+ AI 结构/降级/只读；第 3 天已拆 2 个 skip |
| `tests/integration/test_price_reason_traceability.py` | 4 | 4 | 0 | TC-110：`--from-json` / 进程内引擎 / 落库后 `/prices` 可读 S+得分 / 200 字截断 |
| `tests/integration/test_prices_recalc.py` | 5 | 5 | 0 | TC-122：`POST /api/prices/recalc` 幂等去重 / 暂停跳过 / 404 / 422（C 第 4 天） |
| `tests/integration/test_bootstrap_demo_data.py` | 2 | 2 | 0 | 一键灌数（`scripts/bootstrap_demo_data.py`）：独立临时库跑到「每名可交易选手 ≥N 点」，且 `--keep` 可重复追加（BUG-10 已修，见 §9） |

### 2.3 覆盖率（课程 p.177，第 4 天新增）

> 命令：`pip install --target _cov pytest-cov` → `PYTHONPATH=_cov python -m coverage run --source=app,core_engine -m pytest` → `python -m coverage report -m`。
> 只统计 `code/backend/app` + `code/core_engine` 的源码语句，不含测试代码；数字为 2026-10-24 实测（当时 104 条用例；后续新增用例未重跑覆盖率）。

| 范围 | 语句数 | 未覆盖 | 覆盖率 |
| --- | --- | --- | --- |
| **全部（app + core_engine）** | 1515 | 60 | **96%** |
| 定价 `core_engine/pricing.py` | 113 | 21 | 81% |
| 模拟器 `core_engine/simulator.py` | 58 | 8 | 86% |
| 价格落库 `app/core/price_update.py` | 64 | 5 | 92% |
| 交易规则 `app/core/rules.py` | 23 | 0 | 100% |
| 模型 + 响应 schema | 238 | 0 | 100% |

> 结论：核心逻辑 **97% ≥ 课程要求的 60%**（2026-11-07 复测：1515 语句 / 60 未覆盖）；未覆盖主要是 `database.py` 的初始化/异常分支与定价的极端 clamp 分支，属可接受范围。

### 2.4 前端构建 / 静态检查 / 单测（CI 前端 job 的等价本地复跑）

> CI 前端 job 的三步是 `npm ci` → `npm run lint` → `npm run build`。
> 2026-10-24 在 `code/frontend` 本地复跑（Node v24.20.0 / npm 11.19.0）：

| 步骤 | 命令 | 结果 |
| --- | --- | --- |
| 安装依赖 | `npm ci` | ✅ `added 380 packages in 16s` |
| 构建 | `npm run build`（`vue-tsc` 类型检查 + `vite build`） | ✅ exit 0，58 modules，400ms；产物 114 kB（gzip 45 kB） |
| 静态检查 | `npm run lint`（oxlint + eslint；本地改用不带 `--fix` 的等价检查） | ✅ oxlint `0 warnings / 0 errors`（23 文件）；eslint exit 0 |
| 单元测试 | `npx vitest run`（CI 未纳入，顺带补跑） | ✅ 4 passed（`src/utils/__tests__/format.spec.ts`） |

> 说明：`npm run lint` 脚本自带 `--fix`，CI 上会顺手改文件但不影响退出码；
> 本地为避免改动 A 的源码，用不带 `--fix` 的检查模式。

**最新一轮（第 5 天收尾后的手工合并）由 CI 验证**：本机 npm registry 不可达（无 `node_modules`），
`PlayerDetailView.vue` 的手工合并只能靠 CI 判定 → **CI run #70（`4e45433`）前端 job 绿**：
`npm ci` → `npm run lint` → `npm run build`（含 `vue-tsc` 类型检查）全部通过，耗时 20s。
证据：<https://github.com/July75-bit/Innovation/actions/runs/42326740664>
> 这一节只证明**代码能装、能编译、能过静态检查**；浏览器交互已由 §2.5 的 16 张截图补齐（T3-04 / T4）。

### 2.5 浏览器验收证据（T3-04 / T4，2026-10-24）

> 采集方式：真实后端（uvicorn :8000，seed + 8 轮模拟价格）+ 真实浏览器截图（1280×900 全页）；
> 目录：`docs/acceptance/evidence/`（README 有逐张关键断言）。

| 证据 | 对应验收 |
| --- | --- |
| [01-market.png](evidence/01-market.png) | T3-04 行情页：8 名选手、涨跌色、模拟数据标注、连接成功徽标 |
| [02-detail-chart-ai.png](evidence/02-detail-chart-ai.png) | **T4-01** 折线图（10 点）+ **T4-02** 最近变动 reason + **T4-04** AI 建议卡（6 字段） |
| [03-buy2-success.png](evidence/03-buy2-success.png) | T3-04 买入 2 股成功（余额 5000→4747.46） |
| [04-positions.png](evidence/04-positions.png) | T3-04 持仓页（数量/均价/现价/市值/盈亏） |
| [05-sell1-success.png](evidence/05-sell1-success.png) | T3-04 卖出 1 股成功（余额→4873.73） |
| [06-trades.png](evidence/06-trades.png) | T3-04 交易流水（倒序 + 每笔字段） |
| [07-err-insufficient-balance.png](evidence/07-err-insufficient-balance.png) … [11-suspended.png](evidence/11-suspended.png) | T3-03 五条错误分支（中文 message 原样展示） |
| [12-state-loading.png](evidence/12-state-loading.png) / [13-state-empty.png](evidence/13-state-empty.png) / [14-state-offline-error.png](evidence/14-state-offline-error.png) | **T4-05** 加载中 / 空数据 / 失败三态（断网真实停后端触发） |
| [15-t4-02-point-reason.png](evidence/15-t4-02-point-reason.png) | **T4-02** 每点 reason：悬停 tooltip + 价格变动明细列表（10 点逐点展示时间/价格/reason） |
| [16-tc307-refresh-persist.png](evidence/16-tc307-refresh-persist.png) | **TC-307** 深链 `/players/1` F5 刷新后数据仍由后端重建 |

> 结论：**M3（浏览器交易闭环）与 M4（图表+原因+AI 卡）均已有可复核证据**；剩余未验项只在线上部署（第 5 天）。

## 3. 交易规则边界测试结果（P0 必过）

| ID | 用例 | 结果 | 实际现象 / 截图 |
| --- | --- | --- | --- |
| TC-001 | 正常买入 | ✅ | `test_buy_normal`；余额 5000 → 4748.00、持仓 +2、流水 +1（e2e 同链路） |
| TC-002 | 余额不足 | ✅ | `test_buy_insufficient_balance`：400 `INSUFFICIENT_BALANCE`，三者不变 |
| TC-003 | 数量为 0 | ✅ | `test_buy_invalid_quantity[0]`：422 `VALIDATION_ERROR` |
| TC-004 | 数量为负 | ✅ | `test_buy_invalid_quantity[-1]`：422 |
| TC-005 | 数量为小数 | ✅ | `test_buy_invalid_quantity[1.5]`：422 |
| TC-006 | 选手不存在 | ✅ | `test_buy_invalid_player`：404 `PLAYER_NOT_FOUND`（e2e 同断言） |
| TC-007 | 超持仓上限 | ✅ | `test_buy_exceeds_position_limit`：400 `POSITION_LIMIT_EXCEEDED` |
| TC-008 | 正常卖出 | ✅ | `test_sell_normal` + e2e：卖出后余额增加、持仓减少、流水 +1 |
| TC-009 | 持仓不足 | ✅ | `test_sell_more_than_held`：400 `INSUFFICIENT_POSITION`，不产生负持仓 |
| TC-010 | 暂停交易 | ✅ | `test_buy_suspended_player`：400 `PLAYER_TRADING_SUSPENDED` |
| TC-011 | 用最新价成交 | ✅ | `test_trade_uses_latest_price`：成交价 = 数据库 `current_price` |
| TC-012 | 事务回滚 | ✅ | `test_transaction_rollback_on_failure`：失败后余额/持仓/流水均不变 |

### 3.1 核心异常矩阵（T4-06，第 4 天新增）

| ID | 用例 | 结果 | 证据 |
| --- | --- | --- | --- |
| TC-120 | 卖出暂停选手 / 未知选手、买入缺字段 422、未知价格历史 404、卖超持仓回滚 | ✅ | `tests/unit/test_core_exceptions.py` 7 条（5 个用例，含 3 组缺字段参数化） |

## 4. 定价引擎测试结果

| ID | 用例 | 期望 | 实际 | 结果 |
| --- | --- | --- | --- | --- |
| TC-101 | 上涨 | 110.00 | 110.00（`test_price_rises_when_score_positive`） | ✅ |
| TC-102 | 下跌 | 90.00 | 90.00（`test_price_falls_when_score_negative`） | ✅ |
| TC-103 | 不变 | 100.00 | 100.00（`test_zero_demand_signal_keeps_price_when_score_zero`） | ✅ |
| TC-104 | 触底保护 | ≥ floor | 1.00（`test_price_never_below_floor` / `test_floor_applies_after_clamp`） | ✅ |
| TC-106 | 同 seed 可复现 | 一致 | `test_simulator.py` 3 条：同 seed 序列逐条相等 / 单场稳定 / 换 seed 不同 | ✅ |
| TC-107 | 历史升序 | 升序 | e2e + `test_apply_updates_writes_price_and_history` | ✅ |
| TC-108 | 3σ 归一化 | z=1.5→S=0.5 | 1σ→0.333、2σ→0.667、3σ→1.0、>3σ 饱和；`Z_FULL_SCALE=1.0` 时 1σ 即满格 | ✅ `test_standardize_score_three_sigma_scale` / `test_z_full_scale_one_matches_literal_mapping` |
| TC-109 | 对称 clamp ±20% | 涨跌都封顶 | `test_step_is_capped_symmetrically` | ✅ |
| TC-110 | 价格历史 reason 可追溯（方案 A） | `/prices` 每条模拟调价 reason 含 `S=` + 本轮得分（C 现用措辞「本轮得分 76.6，S=-1.00」）；重启后仍可读 | `test_price_reason_traceability.py` 4 条（from-json / 引擎 / 落库+API / 200 字截断） | ✅ |

> 说明：C 第 3 天已实现 `update_price` / `standardize_score` 与 `simulate_match.py`，5 条 skip 全部转绿（`test_pricing.py` 共 10 条）；
> TC-101~110 已全部有自动化断言（TC-106 由 `test_simulator.py` 覆盖，3 条）。
> TC-110 对应决策：**不新增 `score` 列/`matches` 表，归因写进 `reason`**（选项 A，见 `architecture.md` §5 / `test_plan.md` §4.2）。

## 5. AI 降级测试结果

| ID | 用例 | 结果 | 证据 |
| --- | --- | --- | --- |
| TC-201 | 正常分析 | ✅ | `test_api_ai.py` + e2e：200，`action ∈ {BUY,SELL,HOLD}`，假 client 合法输出时 `source=llm` |
| TC-202 | 无密钥降级 | ✅ | 清空 `llm_api_key` → 200 + `source=rule_fallback`（单元层 + 接口层） |
| TC-203 | 非法输出兜底 | ✅ | 假 client 返回非 JSON → 200 + 规则版；不 500 |
| TC-204 | 超时保护 | 🟡 | 注入超时 client → 200 + 规则版（`test_llm_timeout_still_returns_200_fallback`）；真实 20s 延迟未压测 |
| TC-205 | AI 不改余额 | ✅ | `test_analysis_never_modifies_balance_or_positions` + e2e：调用前后 `/api/account`、`/api/positions` 完全不变 |
| TC-206 | 密钥不外泄 | 🟡 | 接口层已断言响应不含密钥；前端 bundle 与线上抓包待第 5 天 |

## 6. 线上验收结果

> 服务地址：前端 `https://playerstock-frontend-mdlk.onrender.com` ／
> 后端 `https://playerstock-backend-mdlk.onrender.com`（Swagger `/docs` 正常）／
> 数据库 Render Postgres 18（`playerstock-db`）。
> 线上已与 `develop` 对齐；B 于 2026-10-25 用 HTTP 直接复核，原始输出见
> `docs/acceptance/evidence/online/backend-debug-db.md`。

| ID | 用例 | 结果 | 证据 |
| --- | --- | --- | --- |
| TC-401 | 线上健康检查 | ✅ | `GET /api/health` → 200 `{"status":"ok","service":"playerstock-backend"}`；`/docs` 200 |
| TC-402 | CORS 正常 | ✅ | **白名单已生效**：`Origin: https://playerstock-frontend-mdlk.onrender.com` → 响应回显该域名；陌生来源无 `access-control-allow-origin`（不再是 `*`）。前端能取到 8 名选手与价格（A 的线上截图）。详见 `evidence/online/backend-debug-db.md` §2 |
| TC-403 | 线上交易闭环 | ✅ | **2026-10-25 线上实测**：`GET /api/account` 5000.00 → 买 #1 × 2 @ **108.75**（= 当时最新价）→ 4782.50 → 卖 1 → 4891.25 → 并发两个「卖 1」→ **[200, 400]** 只入账一次 → 5000.00；持仓归零、流水 3 条（#1 BUY ×2 / #2 SELL ×1 / #3 SELL ×1）。同轮把 6 类错误分支全打了一遍（余额不足 / 超上限 / 非法数量 ×3 / 选手不存在 / 暂停交易 / 持仓不足），错误码与契约 §5 完全一致。执行命令：`python scripts/smoke_test_api.py --base https://playerstock-backend-mdlk.onrender.com` |
| TC-404 | 重启后数据持久 | ✅ | **2026-10-25 重新部署后实测**（Manual Deploy 后端 + 前端，现网已对齐 `develop`）：部署前后逐项一致 —— 余额 5000.00、总资产 5000.00、持仓 0 条、流水 **3 条**（#1 BUY ×2 @108.75→4782.50 / #2 SELL ×1→4891.25 / #3 SELL ×1→5000.00）、`/api/players/1/prices` 仍 **11 点**且末点 108.75。→ **Postgres 生效，不是临时 SQLite**（免费实例若用 SQLite，重新部署后这些行会全部消失） |
| TC-405 | 子路由刷新 | ✅ | **两侧都成立**：① 服务端 `GET /players/1` → 200、`GET /` → 200（`render.yaml` SPA rewrite）；② `/market` 的 bug 已修并**上线生效**——原问题：市场页路由是 `/`，`/market` 无匹配且无兜底，按 F5 只剩页头（BUG-11）；修复后 `/market → /` 重定向 + `/:pathMatch(.*)*` 兜底，**线上 bundle 里已检索到 `/market`、`pathMatch`、`redirect` 三个标记**（`assets/index-DQQqv-MS.js`），即已部署代码含此修复。A 的浏览器证据显示详情页/折线图 11 点/最近变动原因均正常。复跑命令见 `evidence/online/backend-debug-db.md` §3 |
| TC-406 | 无密钥全站可用 | ✅ | 线上未配 `LLM_API_KEY`：`GET /api/analysis/1` → 200，`action=HOLD`、`source=rule_fallback`；行情/账户/价格历史均正常 |

> 线上证据（B 上传，D 已归档）：
> [account 5000](evidence/online/online-account-5000.png)、[prices 11 点](evidence/online/online-prices-11points.png)、[positions 空](evidence/online/online-positions-empty.png)；
> `online-trades-before-tc403.png` 是 TC-403 之前的**历史状态**（流水为空），不作为验收证据——现网 `GET /api/trades` 实测为 3 条（见 TC-404）。
>
> 线上数据核对（B，`GET /api/players/1/prices`）：**11 个点**、`ts` 升序、
> 末点 `108.75` = `current_price`、`reason` 为「本轮得分 xx，S=±x.xx」；
> 8 人价格与本地 `bootstrap_demo_data.py --rounds 9` 的输出逐条一致（108.75/131.45/85.08/58.11/127.04/105.27/136.50/74.45）。
>
> 重新部署后另核：`access-control-allow-origin: *`（当时线上跑的是硬编码 `*` 的那版代码；
> 2026-10-25 已改为 `resolve_cors_origins()` 配置驱动，见 `compliance.md` §4.1 / `deployment.md` §6，
> **后端重新部署后**按 `CORS_ORIGINS` 生效——配了前端域名就只放行它，没配则仍为 `*` 且日志告警）、
> 前端 HTML 引用的是新构建产物（`assets/index-we8cxpp9.js`）、
> 带 `Origin: <前端域名>` 请求 `/api/players` 仍返回 8 名选手 → 前后端版本均已更新。
>
> **2026-11-07 重新部署复验（TC-404 的人证，B）**：Manual Deploy → Live 前后各截一组
> account / trades / prices（[before-1](evidence/online/online-persistence-before-1-account.png) ·
> [before-2](evidence/online/online-persistence-before-2-trades.png) ·
> [before-3](evidence/online/online-persistence-before-3-prices.png) ／
> [after-1](evidence/online/online-persistence-after-1-account.png) ·
> [after-2](evidence/online/online-persistence-after-2-trades.png) ·
> [after-3](evidence/online/online-persistence-after-3-prices.png)）。
> 脚本逐项对账（`scripts/persistence_check.py --diff`，退出码 0）：**部署前 7 条流水逐行原样保留、
> 11 个价格点 (ts,price) 逐点一致、总资产守恒 5000.00**；期间新增 1 笔成交（m0NESY BUY ×10 @85.08 = 850.80），
> 余额 5000.00 → 4149.20 与之**算术闭合** → 数据没丢，且部署后仍可写。
> 详见 `evidence/online/persistence-redeploy.md`。

## 7. 本地持久化验证（T3-05，2026-10-24）

> 目的：验证「重启后端后数据仍在」，而不是只写进内存/临时库。做法：真实 `uvicorn` 进程 + 独立 SQLite 文件（`DATABASE_URL` 指向工作区临时库），**杀掉进程再起一个新进程**，对比重启前后的余额/持仓/流水/价格历史。

**执行命令（可复现）**

```powershell
$env:DATABASE_URL = "sqlite:///D:/projects/innovation/_t305.db"
python scripts/seed_db.py                  # 建表 + 8 名选手 + demo 账户
cd code/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

```powershell
# 进程 A：健康检查 → 买入 2 股（价 126.00）→ 记录四个读接口
Invoke-RestMethod http://127.0.0.1:8010/api/health
Invoke-RestMethod -Method Post http://127.0.0.1:8010/api/trades/buy `
  -ContentType 'application/json' -Body '{"player_id":1,"quantity":2}'
Invoke-RestMethod http://127.0.0.1:8010/api/account
Invoke-RestMethod http://127.0.0.1:8010/api/positions
Invoke-RestMethod http://127.0.0.1:8010/api/trades
Invoke-RestMethod http://127.0.0.1:8010/api/players/1/prices
# 然后 Stop-Process 杀掉进程 A，重新起进程 B，再查同样四个接口
```

**实测输出（2026-10-24，D 本机）**

```text
BEFORE_RESTART health=ok buy_balance=4748.0 balance=4748.0 total_asset=5000.0 positions=1 qty=2 trades=1 price_points=2
AFTER_RESTART  health=ok balance=4748.0 total_asset=5000.0 positions=1 qty=2 trades=1 price_points=2
SAME balance=True total=True qty=True trades=True points=True
```

**结论**：进程级重启前后，余额（4748.00）、总资产（5000.00）、持仓（ZywOo ×2）、流水（1 条）、价格历史（2 点）完全一致 → **T3-05 ✅**。

> 注意：这验证的是本地 SQLite 持久化；线上 Render 免费实例的磁盘仍是临时的，必须用 Postgres（见 `deployment.md` §4），线上重启验收对应 TC-404（第 5 天）。

## 8. 性能实测（对照非功能需求）

### 8.1 本地基线（真实 `uvicorn :8011` + 临时 SQLite）

| 指标 | 目标 | 实测 | 结论 |
| --- | --- | --- | --- |
| 行情列表响应 | ≤ 300ms | **24.17ms**（P95，20 次采样） | ✅ |
| 买入/卖出接口响应 | ≤ 500ms | **买 36.24ms / 卖 28.86ms**（P95） | ✅ |
| AI 分析响应 | ≤ 8s（上限 20s） | **25.15ms**（`rule_fallback`；有密钥的 LLM 延迟待第 5 天线上） | ✅ |
| 前端首屏 | ≤ 3s | 未测（本机无浏览器依赖，待第 5 天线上） | 🟡 |
| 价格历史图渲染（≥100 点） | 不卡顿 | 未测（待第 5/6 天浏览器实测） | 🟡 |

> 环境：本地真实 `uvicorn :8011` + 临时 SQLite（`bootstrap_demo_data.py` 灌数），每个接口 20 次采样取 P95；
> AI 路径为无密钥兜底（`rule_fallback`）；前端两项待浏览器/线上补测。

### 8.2 线上实测（2026-10-25，B，Render 公网）

> 方法：先打一次 `/api/health` 预热（免费实例冷启动不算进接口耗时），再连打 5 次取中位数；
> 买卖是一次**净额为 0** 的一买一卖（买 1 股再卖 1 股，余额回到 5000.00、持仓清空，只多 2 条流水）。

| 指标 | 目标 | 线上实测（中位） | 结论 |
| --- | --- | --- | --- |
| 行情列表响应 | ≤ 300ms | **171.8ms**（min 129.4 / max 204.6） | ✅ |
| 价格历史响应 | — | 133.7ms | — |
| 账户响应 | — | 127.4ms | — |
| 买入接口响应 | ≤ 500ms | **308.8ms**（成交价 108.75） | ✅ |
| 卖出接口响应 | ≤ 500ms | 196.0ms | ✅ |
| AI 分析响应 | ≤ 8s | **198.0ms**（`rule_fallback`，无密钥） | ✅（配真模型后见 §8.3） |
| 前端首屏 | ≤ 3s | **≈437.8ms**（HTML 263ms + JS/CSS 174.8ms，gzip 合计 100.5KB） | ✅（以资源下载近似，浏览器渲染未测） |
| 价格历史图渲染（≥100 点） | 不卡顿 | 未测（需浏览器；当前每人 10–11 点） | 🟡 |

> 线上比本地慢一个数量级（168ms vs 24ms），主要是 Render 免费实例的跨区网络与冷容器开销，
> 仍远低于目标值。**结论：四项非功能指标线上全部达标**；折线图渲染一条留待浏览器验证。

### 8.3 线上 LLM 版实测（2026-11-07，B，DeepSeek 官方 API）

> 背景：AI 从"规则兜底"切到真模型后补测。先试 OpenCode Zen 免费档失败（`429 FreeUsageLimitError`，
> 换 4 个免费模型均 429），改用 **DeepSeek 官方 API**：
> `LLM_BASE_URL=https://api.deepseek.com/v1`、`LLM_MODEL=deepseek-flash`。
> 方法：`/api/health` 预热后，对 **5 名不同选手**各调一次 `/api/analysis/{id}`。

| 指标 | 目标 | 实测 | 结论 |
| --- | --- | --- | --- |
| AI 分析响应（真模型） | ≤ 8s（上限 20s） | **中位 2461ms**（最快 1839 / 最慢 3930，n=5） | ✅ |
| `source` 字段 | `llm` | **5/5 全部 `llm`** | ✅ |
| 契约 6 字段 | 不变 | `action/disclaimer/player_id/reason/risk_level/source` 齐全 | ✅ |
| 模型判断多样性 | 非固定文案 | HOLD×4 + **BUY×1**；risk HIGH×3 / MEDIUM×2；reason 各不相同 | ✅ |
| 其它接口未受影响 | 行情 ≤300 / 买卖 ≤500ms | players 813ms（冷启动）、trades 430ms、prices 291ms、account 1310ms（冷） | ✅ 预热后达标 |

> **与规则版的差异（答辩要点）**：同一选手规则版给 `risk=LOW`，模型版给 `risk=HIGH` 并写出更长理由——
> 说明 AI 是独立建议者；两者共用同一 6 字段契约，前端只按 `source` 区分展示。
> **失败仍自动回落规则版**（超时上限 20s），演示不会卡死。
> 成本参考：单次约 684 输入 + 200 输出 tokens，`deepseek-flash` 高峰价约 **¥0.003/次**，答辩当天十次以内忽略不计。

### 8.3 线上只读压测（2026-11-14，D）

> 目的：回答能同时跑多少用户。方法、原始数据与完整分析见 [load_test_report.md](load_test_report.md)，
> 脚本 	ests/perf/load_test.py（只读、带熔断，可复跑）。

| 指标 | 实测 | 说明 |
| --- | --- | --- |
| 饱和吞吐 | **≈ 38 req/s** | 40→60→80 并发吞吐停在 35–39，P50 从 0.9s 涨到 1.8s |
| P95 ≤ 1s 的并发 | **≈ 10** | 10 并发时 P95 990ms |
| 错误率 | **0.0%** | 全档位无 4xx/5xx/超时 |
| 估算可支撑用户 | **≈ 190 人同时在线** | 浏览型假设：每 10 秒一次动作、每次 2 请求 |
| 瓶颈 | Render Free **0.1 vCPU 单实例** | 加并发只排队不提速；非代码问题 |

> 局限：只测只读接口；交易（写）与 AI（2.5s/次）未压；跨区 WAN 延迟（≈400ms）计入 P50/P95。

## 9. 缺陷清单

> 只登记**真实发现并修掉**的缺陷；每条都给了能复跑的用例或实测记录。当前 P0/P1 全部清零。
> **已按课程要求登记为 GitHub Issue：[#22–#35](https://github.com/July75-bit/Innovation/issues?q=is%3Aissue+label%3Abug) + [#37](https://github.com/July75-bit/Innovation/issues/37)**（共 15 条，与下表 BUG-01~15 一一对应；创建即**关闭**、带 `bug`+`P0/P1/P2` 标签、正文含现象/根因/修法/守卫测试——BugTracker 展示的是"发现→修复→关闭"的完整生命周期）。

| ID | 描述 | 等级 | 模块 | 负责人 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| BUG-01 | **并发卖出超卖且重复入账**：两条连接各卖 2 股、实际只持 3 股，结果卖出 4 股、余额 5000.00 → 5504.00，还剩 1 股（凭空多卖一股） | P0 | 交易 `api/trades.py` | B | 已修 | 根因是"先 SELECT 判断再 UPDATE"。改为条件更新：减仓 `WHERE quantity > n`、卖光 `DELETE ... AND quantity = n`。`test_trades_concurrency.py` 3 条；修复前后实测对比见 `database_design.md` §3.1 |
| BUG-02 | 买入校验顺序违反契约 §4.7：先查持仓上限、后查余额，用户没钱却提示"超过持仓上限 50 股" | P1 | 交易 | B | 已修 | 顺序改为 选手→数量→可交易→余额→上限；`test_buy_checks_balance_before_position_limit` |
| BUG-03 | 清仓把 `positions.quantity` 更新成 0，触发 `ck_positions_quantity_range`（1–50）CHECK，卖光最后一笔报 500 `INTERNAL_ERROR` | P1 | 交易 | B | 已修 | 卖光分支改走 `DELETE`；`test_sell_normal` 的"卖光后持仓行删除"覆盖 |
| BUG-04 | 价格 `reason` 的"得分"可能被拼两遍（C 拼一次 + B 再拼一次） | P2 | 价格落库 | B | 已修 | `with_score_in_reason()` 幂等化（以"得分"为标记，命中即透传）；`test_score_is_not_duplicated_when_c_already_added_it` / `test_plan_from_json_passes_through_c_reason` |
| BUG-05 | 临时定价规则污染价格历史：`reason` 被写成"（定价引擎由 C 接管后替换）"，会直接展示给前端和 AI | P1 | 价格落库 | B | 已修 | C 引擎落地后改走真实链路，临时规则整段删除；`test_update_prices_script.py` 9 条 |
| BUG-06 | 暂停交易（`suspended`）的选手仍被改价，与"比赛中暂停交易"规则冲突 | P1 | 价格落库 | B | 已修 | `plan_from_engine` 跳过非 trading 并在输出中说明；`test_suspended_players_are_skipped` |
| BUG-07 | `price_history.reason` 超过 `VARCHAR(200)` 会写库失败（长 reason 场景） | P2 | 价格落库 | B | 已修 | 统一截断到 200 并加省略号；`test_reason_is_truncated_to_column_limit` |
| BUG-08 | **部署阻断**：SQLAlchemy 2.1 起 `postgresql://` 默认驱动换成 psycopg 3，而项目只装 `psycopg2-binary`；Render 按 `render.yaml` 填连接串会 `ModuleNotFoundError: No module named 'psycopg'`，服务直接起不来 | P0（部署） | 配置 `core/config.py` | B | 已修 | 把裸 `postgres://` / `postgresql://` 归一化为 `postgresql+psycopg2://`（显式驱动不改写）；`test_config_db_url.py` 6 条，含"建引擎必须解析到 psycopg2" |
| BUG-09 | SQLite 开启 WAL 后生成的 `*.db-wal` / `*.db-shm` 未被 `.gitignore` 覆盖，跑一次后端就出现在 `git status`，容易被 `git add -A` 顺手提交 | P2 | 仓库卫生 | B | 已修 | `.gitignore` 补两条规则并验证 `git check-ignore` 命中 |
| BUG-10 | Windows 中文控制台（GBK）下 `test_bootstrap_demo_data.py` 让 pytest 抛 `UnicodeDecodeError 0xd2`，本机 1 failed + 1 error；CI 的 ubuntu 不暴露 | P1 | 测试代码 / `seed_db.py` | B | 已修 | 根因：`seed_db.py` 没把 stdout 切成 UTF-8，子进程按 GBK 输出、pytest 的 fd 捕获按 UTF-8 解码。修法：① `seed_db.py` 统一 `reconfigure(encoding="utf-8")`；② 测试给子进程显式 `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`。已用旧版脚本复现出 `0xd2` 并验证修复后 `PYTHONIOENCODING=gbk` 下也全过 |
| BUG-11 | **线上 `/market` 直接访问/刷新白屏**：路由表里市场页在 `/`，`/market` 没有任何路由匹配，又没有兜底路由；静态站 rewrite 仍返回 `index.html`，于是"没有 404、也没有页面"，只剩头部——比 404 更像站点挂了 | P2 | 前端路由 `router/index.ts` | B（A 的文件，经 A 授权代改） | 已修 | 加 `/market` → `/` 重定向 + `/:pathMatch(.*)*` → `/` 兜底；新增 `src/router/__tests__/router.spec.ts` 4 条用例（`/market` 与未知路径都要落到市场页、正常子路由不受影响）。`vitest` 12 passed、`npm run build` exit 0、oxlint 0/0、eslint exit 0。**需重新部署前端后线上复验** |
| BUG-12 | **线上前端被跨域拦掉**：后端的 CORS 已改成"按 `CORS_ORIGINS` 白名单"，但 Render 上没填这个变量 → 按 `config.py` 默认值只放行 `localhost:5173`，浏览器请求 `*-backend.onrender.com` 拿不到 `access-control-allow-origin`，页面显示"连接失败" | P0（线上可用性） | 配置 `core/config.py` + `app/main.py` + `render.yaml` | B | 已修（**线上已复验**） | 三处一起补：① `render.yaml` 把 `CORS_ORIGINS` 写成前端公网地址（部署配置进仓库）；② `resolve_cors_origins()` 增加"线上却还是本地默认值 → 退化 `*` 并 WARNING"；③ `cors_origin_list` 去掉尾部斜杠。`test_cors_config.py` 8 条。**线上实测**：`Origin: 前端域名` → 回显该域名；`Origin: evil.example.com` → 无该头（白名单生效，不是 `*`），见 `evidence/online/backend-debug-db.md` §2 |
| BUG-13 | **测试里的"日期炸弹"**：`test_prices_recalc.py` 把 `PLAYED_AT` 写死成 `2026-11-07`，而 `conftest` 用 `now-2h` / `now-1h` 造种子历史——当机器时间正好是 2026-11-07 时，那两条历史落进本轮去重窗口 `[played_at, played_at+1d)`，接口把两名选手都判成"该轮已计价"，2 条用例整片红；换一天跑又全绿 | P2 | 测试代码 `test_prices_recalc.py` | C（B 代改） | 已修 | 改为"**未来 30 天**"的相对日期（`datetime.now(UTC).date() + 30d`），并同步断言里的日期。教训：**测试里不要写死"今天附近的日期"**，它会和时间耦合 |
| BUG-14 | **答辩稿生成脚本写死绝对路径**：`build_deck.py` 里 `ROOT = Path(r"D:\projects\innovation\Innovation")`，换台机器/换个 clone 目录就 `FileNotFoundError`，PDF 无法重新生成；且稿内数字停留在"120 条用例 / 10 条缺陷" | P2 | 脚本 `docs/presentation/build_deck.py` + 稿件 | D（B 代改） | 已修 | `ROOT` 改为按 `__file__` 反推仓库根；稿内数字同步为 **137 条 / 13 条缺陷 / 8 个路由模块 / Vue 3.5·TS 6.0·Vite 8.2**，并用 Edge headless 重新导出 `defense.pdf` |
| BUG-15 | **重灌/重置会删掉注册账号（数据丢失）**：用户实测"注册的账户第二天就消失，登录提示账号不存在"。根因：`scripts/seed_db.py --reset` 与 `POST /api/debug/reseed` 都用 `Base.metadata.drop_all()`，把 `users` 表连同账号、口令散列、令牌一起删了——只要有人跑一次"重置演示数据"，所有私人账号归零 | P1（数据丢失） | 脚本 `scripts/seed_db.py` + 接口 `app/api/debug.py` | B | 已修 | 两处都改成**只清业务数据**（positions/trades/price_history/players，先子后父），`users` 原样保留（用户名/`password_hash`/`salt`/令牌行不动）；余额统一复位到 `initial_balance`（行情回种子价、钱也回起点才自洽）。新增回归 `test_reseed_keeps_registered_account`：注册→买 3 股→重灌→**原密码仍能登录**、余额 5000、流水清空。端到端另验：`seed_db --reset` 后手工插入的账号仍在、余额被复位 |

## 10. 未覆盖与已知限制

| 项 | 原因 | 影响 | 后续 |
| --- | --- | --- | --- |
| 价格归因结构化（score 列） | 方案 A：本期用 `reason` 文本承载 S/得分，不新增列/表 | 不能按得分做 SQL 统计 | 课程后如需统计报表再走契约 §6 评估选项 B |
| 线上截图归档 | TC-401/403/404/406 已有 HTTP 证据；TC-402/405 的浏览器截图待 A 归档（服务端已复核 200） | 不影响功能验收 | 第 6 天补图 |
| 代码质量静态扫描 | 已完成（第 3 天） | — | 见 `code_quality_report.md`：D 负责文件 0 残留；剩余 51 项按归属移交 B/C；CI 门槛已按目录分档 |
| 并发压测 | 6 天时间不足 | 未验证高并发 | 已用事务 + 校验兜底，文档说明 |
| 真实赛事数据 | 接口不可用 | 用模拟数据 | 架构留适配器 |
| 浏览器兼容性 | 只测 Chrome/Edge | 未测 Safari | 演示只用 Chrome |
| 移动端适配 | 非重点 | 手机端体验一般 | 如实说明 |

## 11. 结论

- P0 缺陷：**0** 个（自动化层 **265** 条，CI 与本机全绿；浏览器证据见 §2.5）
- P1 缺陷：**0** 个（BUG-10 编码问题已修并复现验证；BUG-12 线上 CORS 事故已修复并线上复验；BUG-15 账号被重灌删除已修）
- **结论：可交付** —— M3/M4/M5 均已达成；**265** 条自动化（单元 211 / 集成 21 / 评测 33；auth 22+7、重灌端点 4、余额重建 2 等入账，2026-11-07）+ 核心逻辑覆盖率 **96%**（1543 语句 / 61 未覆盖的 19:30 口径；末轮新增 `account/rebuild` 与 reseed 改造后待 D 复测） +
  线上验收 **TC-401~406 全部 ✅**（CORS 白名单生效、`/market` 修复已上线、重新部署后数据仍在）+
  缺陷清单 **15 条全部已修**（含 3 个 P0：并发超卖 / 部署驱动 / 线上 CORS；含 1 条 P1 数据丢失：重灌误删账号）+
  `deployment.md` 检查单 **37/37** 全勾；汇报材料 `defense.pdf` **16 页**（含 01B/01C/01D 三页，2026-11-07 重导）。
- 答辩当天仍需执行（非交付物缺口）：**彩排 ≥2 次并计时**（8+2+5 ≤15 分钟）、演示前 15 分钟跑 `prewarm.py` 预热、
  若不想在演示里出现历史持仓则上台前重置演示数据（见 `demo-script.md` §0/§0.1）。
- 已知限制如实列在 §10（外部交叉测试为延期说明、并发压测未做、LLM 版 AI 未压测）。
- 签字：A____ B____ C____ **D 王泽棠（2026-11-07，自动化 + 代码质量 + 线上验收）**

## 12. 附件

- [x] 线上地址与截图：前端 `https://playerstock-frontend-mdlk.onrender.com`、后端 `https://playerstock-backend-mdlk.onrender.com`；证据 `docs/acceptance/evidence/online/`
- [x] 浏览器验收证据：`docs/acceptance/evidence/`（16 张 + README）
- [x] pytest 输出文本 → 见 §2.1 / §2.2（本机 265 passed / 0 skipped；BUG-10 已修）
- [x] 数据持久化验证（T3-05）→ 见 §7（重启前后四项一致，含复现命令）
- [x] 部署持久化验证截图（线上）→ TC-404（重新部署前后 3 条流水/11 个价格点一致）
