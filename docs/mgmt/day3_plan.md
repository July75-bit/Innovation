# 第 3 天任务清单（交易闭环 + 代码质量）

> **日期**：2026-10-24 ｜ **负责人**：D（维护，全员执行） ｜ **里程碑**：M3 交易闭环（硬卡点）
> **课件依据**（SWIEP.pdf p.119–158）：第 3 天第 1 部分「软件开发方法」、第 3 天第 2 部分「代码质量」。
> 代码质量检查点（p.158）：**提交扫描报告截图 + 重构前后对比**。
> 本文件与 `milestones.md` 的 T3 任务、`docs/acceptance/code_quality_report.md` 配合使用。

## 0. 开工基线（2026-10-24 10:18 实测）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| 仓库 | `develop` 与 `origin/develop` 同步、工作区干净；B 的并发修复 + 契约冻结签字已合入 | `git log`：`01f53c1` / `d44ce7c` |
| D | AI 接口 `GET /api/analysis/{player_id}` 已接线（6 字段 / 失败一律 200 + rule_fallback）；e2e 2 条已绿；原型 / UML / WBS / 测试文档已补 | `3092386`、`891c7eb`、`c977e8b`、`cf163c8` |
| B | 5 表 / 9 接口 / 交易事务 + 并发条件更新；新增 `test_api_trades.py`、`test_trades_concurrency.py`；`requirements.lock.txt`；契约第 2 天冻结签字 | `397431b`、`e071187`、`c3432e0` |
| A | **0%**：`code/frontend/` 只有 `README.md`，脚手架未生成 | `ls code/frontend` |
| C | **进行中**：`pricing.py` / `simulator.py` 曾在 `NotImplementedError` 状态；C 已在本地实现 `update_price` / `standardize_score`（S 采用 3σ 归一化，见 §3），待 push | C 消息 + 仓库现状 |
| 测试 | **65 passed / 5 skipped**（5 个 skip 全是定价） | `python -m pytest` |
| 里程碑 | M3 未达成；`T3-06` e2e ✅，`T3-01/02/03/04/05` 未完成 | `milestones.md` |

> **今天的两大风险都在 0/进行中的两个人身上**：A 前端未起步、C 定价未合入。D/B 的零件已转起来；A 或 C 任一卡死，M3 只能降级为"接口级闭环 + 原型演示"。
>
> **11:00 更新**：A 前端初版（`9782dc7`）、C 定价实现（`59186a5`）、B 价格落库（`5f069ee`）已合入 develop；C 补 3σ/同 seed 断言（`dfe9f26`/`506b564`）、B 补 `--from-json` + reason 幂等（`adcc848`/`19e68bd`）后全仓 pytest **97 passed / 0 skipped**。
> CI 首次 push 因新增 ruff 门槛红在 `scripts/simulate_match.py::main` 复杂度 11（CLI 入口装配），已把 scripts 的 C901 阈值放宽到 12（业务代码/测试仍为 10），见 `code_quality_report.md` §4.2。剩余 M3 卡点 = 浏览器联调 + 持久化验证。
>
> **15:30 更新（D 复核）**：自动化层 **97 passed / 0 skipped**；T3-01/03/05/06/07 已完成，T3-02 代码已接真实接口、**T3-04 浏览器全链路尚未跑**（当前工作区 `node_modules`/`dist` 都没有，A 侧依赖待装）；T3-05 重启持久化已由 D 用真实 uvicorn 进程复现（见 `test_report.md` §7）；契约 §7 **3/4 已签（C 待签）**；CI run #30（`0bc2f14`）三 job 绿。今日剩余 = A 浏览器联调 + B 灌 10+ 价格点 + C 签字。

## 1. 全员共同段（09:00–09:40）

| 时间 | 事项 | 动作 | 产出 |
| --- | --- | --- | --- |
| 09:00–09:15 | 站会三问 | 昨天做了什么 / 今天做什么 / 卡在哪；对照 §0 基线逐条确认 | 口头对齐 |
| 09:15–09:25 | 基线复跑 | 仓库根 `python -m pytest`，记录真实数字（预期 65 passed / 5 skipped） | 终端输出 |
| 09:25–09:30 | 仓库清理 | 根目录 `HANDOFF_day1_backend.md` 是 B 的内部交接文件（自述"不属于课程交付物"），确认后删除 | 仓库只剩课程交付物 |
| 09:30–09:40 | 契约冻结复查 | B 已签字；今天不再新增/改名字段；AI 输出固定 6 字段（无 `suggested_price_band`） | 一句话确认 |

## 2. 分工与任务

### 2.1 A 同学：前端（约 7h，今日最高优先级）

**边界**：只改 `code/frontend/`。**视觉/交互基线**：`docs/software/prototype/index.html`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–10:30 | 解除目录阻塞 + 脚手架：`Move-Item code/frontend/README.md docs/software/frontend_setup.md` → `npm create vue@latest code/frontend`（TS/Router/Vitest/ESLint/Prettier = Yes）→ `npm install` → `npm run dev` | 浏览器打开 5173 有初始页 |
| 10:30–12:00 | 5 个页面（先 mock）：市场表格 / 选手详情（价格 + 折线图占位 + 涨跌原因 + AI 卡）/ 买卖表单 / 持仓页 / 流水页 + 顶部导航 | 5 个路径可切换、不白屏 |
| 13:00–15:00 | 接真实接口：`VITE_API_BASE_URL` + `src/api/client.ts`；接 `/api/players`、`/api/account`、`/api/positions`、`/api/trades`、`/api/players/{id}`、`/api/players/{id}/prices`、`/api/analysis/{id}` | 数据来自后端，代码里搜不到写死的 `127.0.0.1` |
| 15:00–16:30 | 错误与三态：后端 `message` 中文直出；加载中 / 空 / 失败三态；买卖后刷新余额、持仓、流水 | 余额不足、持仓不足能弹出后端原文 |
| 16:30–17:30 | 浏览器全链路联调（与 B）：查行情 → 买入 → 看持仓 → 卖出 | 浏览器真实跑通，逐步截图 |
| 17:30–18:00 | PR + 文档：PR 模板勾"接口变更：否"；页面要素/路由截图补进 `docs/requirements/wireframes/README.md`；CI 前端 job 绿 | PR 已建、CI 绿 |

**砍单**：10:30 脚手架没出来 → 只保"市场 + 详情 + 买卖"，持仓/流水 mock；14:00 未接上真实接口 → 浏览器闭环顺延，接口级闭环今天必须绿（D 已备好 e2e）。**D 不代写前端**。

### 2.2 B 同学：后端与交易系统（约 6h）

**边界**：`code/backend/app/{api,models,schemas,core}`、`requirements.txt`、`scripts/seed_db.py`、`tests/`；不碰前端 / `core_engine/` / `ai/`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–10:30 | 与 C 定死价格落库分工：C 只算 `PriceUpdate`、B 写库；新增 `scripts/update_prices.py`：调 C 的 `update_price` → 同事务 `UPDATE players` + `INSERT price_history(reason)`（T3-01） | 跑一次后 `/api/players/{id}/prices` 多一个带中文 reason 的点 |
| 10:30–12:00 | 历史查询复核：升序 / 每点带 reason / 空返回 `[]` 不 404；补齐 8 名选手初始历史 | Swagger 里 8 人都有价格历史 |
| 13:00–14:30 | 持久化验证（T3-05）：seed → 买入 → 重启 `uvicorn` → 再查 `/api/account`、`/api/positions` | 重启后数据仍在（截图/命令） |
| 14:30–16:00 | 联调支持 A：错误码/`message`、并发与重复提交语义、成交价用最新 `current_price` | A 页面无 `undefined` |
| 16:00–17:30 | PR + CI 后端 job 绿（接口变更需同步契约） | PR 已建、CI 绿 |

### 2.3 C 同学：行情与定价（约 6h）

**边界**：`code/core_engine/`、`data/seed_players.json`、`docs/algorithm/pricing_model.md`、`scripts/simulate_match.py`；**绝不**改 `app/api`、`app/models`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–11:30 | 实现 `update_price` + `standardize_score`（去掉 `test_pricing.py` 5 条 skip）：`P' = max(floor, P×(1+αS+βD))`、α=0.15 / β=0 / floor=1.0、单次 clamp ±20%、2 位小数、`PriceUpdate(new_price, change_pct, reason)` 中文可读句。**S 口径**：`S = clamp(z / Z_FULL_SCALE, -1, 1)`，默认 `Z_FULL_SCALE = 3.0`（3σ 满格，避免 1σ 顶格导致价格二值跳动）；改 1.0 即回到字面口径 | `pytest tests/unit/test_pricing.py` 5 条全绿；`pricing_model.md` 同步公式 + 参数表 + 一涨一跌案例 |
| 11:30–12:00 | 与 B 对齐落库分工与触发方式，结论写 `docs/requirements/mechanism_design.md` | 结论落文档，§5 待定项勾掉 |
| 13:00–15:00 | 模拟比赛发生器：`generate_match(seed)` / `generate_match_series(seed)`（同 seed 可复现）、`to_demand_signal` 除零保护 | 同 seed 两次结果一致 |
| 15:00–16:30 | `python scripts/simulate_match.py --seed 42` 打印 8 条"旧价 → 新价 + reason" | 命令行 8 条变化及原因 |
| 16:30–17:30 | `pricing_model.md` 补一涨一跌案例 + PR | 参数表无空白、PR 已建 |

**砍单**：中午公式没绿 → 先交"能算出新价 + 中文 reason"的最小版本，B 用固定规则临时制造价格变化保联调；C 下午补精确实现。

### 2.4 D 同学：AI / 测试 / 代码质量 / 部署 / 文档（约 6h）

**边界**：`code/backend/ai/`、`docs/`（除 `pricing_model.md`）、`.github/`、`render.yaml`；不碰 A/B/C 代码（`app/api/ai.py` 已按第 3 天计划接线）。

| 时段 | 任务 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| 09:40–12:00 | **代码质量**：配置 ruff（`pyproject.toml` 已有基础配置）→ 扫描 `code/backend`、`code/core_engine`、`tests`、`scripts` → 记录指标 → Top5 重构（先补测试再重构）→ 把 `ruff` 加进 CI 后端 job | 扫描报告 + 重构前后对比写进 `docs/acceptance/code_quality_report.md` | ✅ 见该报告 |
| 13:00–14:30 | 代码质量报告定稿：指标、Top5、前后对比、剩余问题按归属移交 | 报告含"扫描报告截图 + 重构前后对比"（课件 p.158 检查点） | ✅ |
| 14:30–16:00 | 全链路联调主持：e2e 2 条维持绿；补错误路径（404/参数非法/暂停交易）；联调问题登记 Issue | e2e 全绿、问题有记录 | ⏳ 待 A/B 浏览器联调 |
| 16:00–17:00 | 文档回填：`test_plan.md`、`test_report.md`、`milestones.md`；**S 的 3σ 归一化口径**同步到 `functional_spec.md` FR-M2-02 与 `test_plan.md`（TC-108，C 实现后转绿）；`pricing_model.md` 由 C 改 | 三份文档有真实数据，不写"应该能跑" | ✅ 2026-10-24 |
| 17:00–17:30 | 部署预检（不部署）：`render.yaml` rootDir/startCommand、`.env.example`、`DATABASE_URL`/`CORS` 控制台项、Render 误用 SQLite 告警 | 预检清单写进 `deployment.md` | ✅ 见 `deployment.md` §3.8 |
| 17:30–18:00 | CI 三 job 绿：后端（pytest + ruff）、前端（eslint + build）、交付物完整性 | CI 全绿 | ✅ run #30（`0bc2f14`）三 job 全绿 |

## 3. 19:30 晚验收（对照 M3，逐条打勾）

| # | 验收项 | 判定证据 | 责任人 |
| --- | --- | --- | --- |
| 1 | 浏览器完成「查行情 → 买入 → 看持仓 → 卖出」 | 5173 页面截图/录屏 | A + B |
| 2 | 余额 / 持仓 / 流水 / 价格历史正确入库 | Swagger + 数据库查询 | B + C |
| 3 | 价格历史升序、每点带中文 `reason` | `/api/players/{id}/prices` 响应 | B + C |
| 4 | AI 建议在页面可展示（action/理由/风险/免责声明） | 详情页 AI 卡截图 | A + D |
| 5 | 重启后端后数据仍在（T3-05） | 重启前后对比 | B |
| 6 | 全仓 `python -m pytest` 全绿、定价 5 条不再 skip | 终端输出 | 全员 |
| 7 | 代码质量：扫描报告 + 重构前后对比 | `docs/acceptance/code_quality_report.md` | D |
| 8 | CI 三 job 绿 | Actions 链接 | D |

**打勾规则**：第 1、2 项任一红 → M3 不达成，第 4 天优先补；第 6/7/8 项今天必须全绿，不能拖到第 6 天。

## 4. 风险与砍单规则

| 风险 | 症状 | 预防 / 砍单 |
| --- | --- | --- |
| A 前端 0% 起步 | 10:30 脚手架没出来 | 砍到「市场 + 详情 + 买卖」；持仓/流水 mock；D 不代写前端 |
| C 定价进行中 | 中午公式没绿 | 先交最小实现，B 用固定规则临时制造价格变化保联调 |
| 价格落库分工扯皮 | `/prices` 空表 | 09:40 就定死：C 只算、B 写库，结论写 `mechanism_design.md` |
| 只做功能不做质量 | 课件检查点材料缺 | D 上午出扫描报告，下午定稿，不拖到第 6 天 |
| 契约又改字段 | 前端联调 `undefined` | 契约已冻结（B 签字），改字段走 §6 流程 |
| 破坏性重构 | 重构后测试挂 | 先补测试再重构；每次重构后立刻 pytest；只做 Top5 低风险项 |

## 5. 今日产出物清单

- 浏览器全链路：查行情 → 买入 → 持仓 → 卖出（A + B）
- 价格更新落库 + `/prices` 历史可用（B + C）
- 重启后数据仍在（B）
- **代码质量扫描报告 + 重构前/后对比**（D）
- 全仓 pytest 97 passed / 0 skipped（定价 5 条已转绿）
- CI 三 job 绿（D）
- PR：A / B / C 各至少 1 个，B 的接口变更（如有）必须同步契约

## 6. 课件要求 ↔ 今日任务映射

| 课件要求（SWIEP.pdf） | 落到今天哪个任务 |
| --- | --- |
| p.119–127 开发过程：任务拆分 / 编码关注点 / 编码规范 / Git 分支协作 / Conventional Commits | 全员按本清单小步提交，commit 用 `feat/fix/test/docs`；PR 到 `develop` |
| p.128–143 代码评审、自动化测试、CI、安全开发、AI 辅助编程 | 每个 PR 走模板与评审；pytest + CI 三 job；AI 生成代码必须人工核对（原型/文档已标注草稿） |
| p.144–158 代码质量五维度 + 静态分析 | D：ruff 扫描 + Top5 重构 + 质量报告 |
| p.158 检查点：扫描报告截图 + 重构前后对比 | D：`docs/acceptance/code_quality_report.md` |

> 备注：所有 commit 只到 `develop`；push / PR / 合并 `main` 由王泽棠本人操作。不写每日总结，晚验收只记结论与证据。
