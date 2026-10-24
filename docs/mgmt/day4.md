# 第 4 天任务清单（软件测试 + 图表/AI 亮点）

> **日期**：2026-10-25（第 4 天）｜ **负责人**：D（维护，全员执行）｜ **里程碑**：**M4 亮点完成**（价格折线图 + 涨跌原因 + AI 建议正常展示）+ 课程第 4 天测试检查点
> **课件依据**（SWIEP.pdf p.160–183）：第 4 天第 1 部分「软件测试方法」、第 2 部分「测试和修复软件缺陷」、第 3 部分「交叉原型测试」；检查点：**p.177 测试用例（文档 + 代码提交到 `tests/`）**、**p.178 修复缺陷**、**p.179–182 原型测试问卷**。
> **配套文件**：`milestones.md` 的 T4-01~07、`docs/acceptance/test_plan.md`、`test_report.md`、`docs/algorithm/backtest_report.md`、`docs/algorithm/pricing_model.md` §7。

## 0. 开工基线（2026-10-24 15:30 实测）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| 仓库 | `develop` 工作区干净，本地比 origin 多 2 个 commit（今日文档更新，待 push） | `git status -sb` |
| 测试 | **97 passed / 0 skipped**（单元 91 + 集成 6）；TC-101~110 全绿，TC-106 已由 `test_simulator.py` 覆盖 | `pytest` |
| T3 收尾 | 5 完成 + 2 部分：T3-02（真实接口已接、浏览器未验）、T3-04（全链路未跑）；**M3 未达成** | `milestones.md` |
| 契约 | **四人已签**（D/B/A 已在 develop；C 于 `94ea9aa` 补签 §7） | `api_contract.md` |
| 数据 | `playerstock.db` 0 字节（未 seed）；按 B 的配方可灌到每人 10+ 点 | `database_design.md` §4.1 |
| 前端 | 代码就绪；本工作区无 `node_modules`/`dist`；CI run #30 前端 job（安装依赖 + lint + build）全绿 | GitHub Actions |
| 质量工具 | 未装 `pytest-cov`；无 `scripts/backtest.py`；`backtest_report.md` 只有模板 | — |

> **今天两条主线**：① **课程检查点**：测试用例 + 覆盖率 ≥60% + 修复缺陷 + 交叉原型测试；② **项目亮点 M4**：折线图 / 涨跌原因 / AI 卡 / 三态 + 回测初版。
> **硬前提**：A 必须上午完成 **T3-04 浏览器全链路收口**（`npm ci` → `.env.local` → uvicorn 8000 → `npm run dev`），否则 M3 继续挂、T4 全部没有真实数据可看。
>
> **实际进展（2026-10-24 17:15，D 汇总）**：**M3/M4 已达成**——A 提交 14 张浏览器证据（`docs/acceptance/evidence/`，含 10 点折线图 / 原因 / AI 卡 / 三态 / 5 条错误分支）；C 补 `POST /api/prices/recalc` + 5 条用例、§7 正式回测与 100 seed、reason 带得分；B 补一键灌数 `bootstrap_demo_data.py` + 部署预检 8 条用例、reason 分工闭环。全仓 **120 passed（CI ubuntu）/ 0 skipped**；本机 Windows 因 BUG-03 为 118 passed + 1 failed + 1 error（B 的 bootstrap 子进程 UTF-8 解码，见 `test_report.md` §9）。剩余：部署（第 5 天）、外部交叉原型测试组、LLM 版回测 S1'（第 5 天）、TC-307 刷新回归。

## 1. 全员共同段（09:00–10:00）

| 时间 | 事项 | 动作 | 产出 |
| --- | --- | --- | --- |
| 09:00–09:15 | 站会三问 | 昨天 T3 收尾 / 今天 T4+测试 / 卡在哪；确认 A 装依赖、B 灌数据、C 回测数据 | 口头对齐 |
| 09:15–09:25 | 基线复跑 | 仓库根 `python -m pytest`，确认 **97 passed / 0 skipped** | 终端输出 |
| 09:25–10:00 | 三线并行启动 | A 起前后端跑 T3-04；B 跑 seed + `simulate_match --rounds 8` + `update_prices --from-json`；C 准备回测数据（契约已由 C 于 `94ea9aa` 补签） | A 截图、B 的 10+ 点数据、C 的回测草稿 |

## 2. 分工与任务

### 2.1 A 同学：前端（约 7h，T3-04 收口 + M4 全部页面项）

**边界**：只改 `code/frontend/`。**基线**：`docs/software/prototype/index.html`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:25–11:30 | **T3-04 浏览器全链路收口**：`npm ci` → `Copy-Item .env.example .env.local` → 后端 `seed_db.py` + `uvicorn --port 8000` → `npm run dev`；跑「查行情 → 买 2 股 → 持仓 → 卖 1 股 → 流水」 | 逐步截图；T3-02/T3-03 实机验证（余额不足/持仓不足/超上限/非法数量/暂停交易 5 条错误分支弹后端原文） |
| 11:30–13:00 | **T4-01 折线图**：`PriceChart` 接 10+ 个点；处理 0 点空态、单点；时间轴按 ts 升序 | 每人（sh1ro 暂停除外）≥10 点可见 |
| 14:00–15:00 | **T4-02 涨跌原因**：详情页展示 `latest_reason` + 折线每点 `reason`（tooltip 或列表） | 页面能看到最近原因；抽查 3 个点与后端一致 |
| 15:00–16:00 | **T4-04 AI 建议卡**：action / reason / risk / source / disclaimer；`source=rule_fallback` 有降级徽标 | 6 字段与契约 §4.10 一致 |
| 16:00–17:00 | **T4-05 三态**：加载中 / 无数据 / 失败；拔网线或停后端看到失败态并可重试 | 三态截图 |
| 17:00–17:40 | 补 `docs/requirements/wireframes/README.md` 页面截图 + 状态改 ✅；配合 D 做交叉原型测试演示 | 文档有截图；3 分钟演示脚本能跑 |
| 17:40–18:00 | CI 前端 job 复核（lint + build） | run 绿 |

**砍单**：11:30 还没跑通浏览器 → 只保「市场 + 详情 + 买卖」；折线图砍 hover/缩放；三态只保失败态。

### 2.2 B 同学：后端（约 6h，造数据 + 修缺陷 + 部署准备）

**边界**：`code/backend/app/{api,models,schemas,core}`、`requirements.txt`、`scripts/`、`tests/`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:20–10:00 | **T4-01 数据准备**：`seed_db.py --reset` → `simulate_match.py --seed 42 --rounds 8 --json data/price_updates.json` → `update_prices.py --from-json data/price_updates.json` | 每人 10+ 个价格点；`/prices` 升序、每点带 reason、最后一点 = `current_price`（sh1ro 暂停停在 2 点，属预期） |
| 10:00–12:00 | **修复缺陷**：优先处理 CI/交叉测试提交的 P0/P1（交易、价格落库、契约字段）；新增边界用例 | 缺陷清单状态更新；`pytest` 全绿 |
| 13:00–15:00 | **部署准备（第 5 天）**：确认 Render 账号、Postgres 建库、环境变量清单（`DATABASE_URL`/CORS/密钥）；复核 `render.yaml`、`/api/health`、`postgres://` 归一化 | `deployment.md` §3 检查单逐项勾 |
| 15:00–17:30 | 配合 A 联调错误码/并发/成交价语义；交叉原型测试当被测方 | 前端无 `undefined`；问题有记录 |
| 17:30–18:00 | CI 后端 job 绿；接口变更同步契约（如无变更注明） | run 绿 |

### 2.3 C 同学：定价（约 5h，回测数据 + 修缺陷）

**边界**：`code/core_engine/`、`data/seed_players.json`、`docs/algorithm/pricing_model.md`、`scripts/simulate_match.py`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:20–09:40 | 契约 §7 **已签**（C 于 `94ea9aa` 补签）——本轮无需再签；转到回测数据准备 | 确认 `api_contract.md` 四人记录齐全 |
| 09:40–11:00 | 给 B 的 8 轮明细核对：同 seed 下 `simulate_match.py` 与 `update_prices.py` 算出的价格一致；`reason` 含 S + 得分 | 抽样 3 条一致 |
| 11:00–15:00 | **回测数据**：`pricing_model.md` §7 用正式数据替换第 1 天试跑；补 100 seed 稳定性统计（涨跌方向/幅度分布） | §7 有数字 + 100 seed 表；一涨一跌案例 |
| 15:00–17:00 | 修复定价/模拟器缺陷；审 `reason` 文案（与 B 的幂等拼接对齐，避免双写得分） | 缺陷清单更新 |
| 17:00–18:00 | 交叉原型测试配合；CI 复核 | — |

### 2.4 D 同学：测试 / 质量 / 回测 / 文档 / 部署（约 7h）

**边界**：`code/backend/ai/`、`docs/`（除 `pricing_model.md`）、`.github/`、`render.yaml`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:20–11:00 | **T4-06 核心异常用例**：404/422/暂停交易/超上限/回滚/空价格历史/AI 降级/密钥不外泄；补进 `tests/` | 新增用例全绿；`test_plan` 对应 TC 有执行证据 |
| 11:00–12:00 | **覆盖率统计**（课程 p.177）：本地 `python -m pip install pytest-cov` → `pytest --cov=app --cov=core_engine --cov-report=term`；核心逻辑 ≥60% | 覆盖率数字写进 `code_quality_report.md` / `test_report.md` |
| 13:00–15:00 | **交叉原型测试组织**（课程 p.179–182）：约另一组互测；A 演示（市场→详情→买卖→回测/AI），B/C 记录问卷（实际效果/可用性/竞品/功能/体验 + 建议） | 新增 `docs/acceptance/cross_test.md`：问卷 + 建议 + 后续动作 |
| 15:00–16:00 | **测试报告定稿**：`test_plan` / `test_report` 填真实数字（97+、覆盖率、缺陷清单、交叉测试结论） | 文档无空白节；P0/P1 缺陷为 0 或已修 |
| 16:00–17:30 | **T4-07 回测初版**：写 `scripts/backtest.py`（可重跑）→ 规则版 AI 建议 vs 买入持有；输出 `docs/algorithm/backtest_result.json` + 填 `backtest_report.md` 数字（收益/回撤/胜率） | 报告里的每个数字都能被脚本复现 |
| 17:30–18:00 | CI 三 job 绿；milestones 第 4 天进度回填；push 前自检 | run 绿；看板更新 |

**兜底**：回测 17:30 还没数字 → 只做「1 个策略 + 3 个指标（总收益/最大回撤/胜率）+ 固定 3 组 seed」，报告如实写限制。

## 3. 晚验收（对照 M4 + 课程 p.177–178 检查点）

| # | 验收项 | 判定证据 | 责任人 |
| --- | --- | --- | --- |
| 1 | T3-04 浏览器全链路：查行情→买入→持仓→卖出 | 5173 页面截图/录屏 | A |
| 2 | 折线图 ≥10 个价格点（sh1ro 暂停除外） | 详情页截图 + `/prices` 点数 | A |
| 3 | 涨跌原因展示（最近原因 + 每点 reason） | 页面截图 + 后端响应对照 | A + C |
| 4 | AI 建议卡 6 字段 + `rule_fallback` 徽标 | 详情页截图 | A + D |
| 5 | 加载中/无数据/失败三态 | 拔网线/停后端截图 | A |
| 6 | 测试用例文档 + 测试代码在 `tests/`（含新增异常用例） | pytest 输出 | D |
| 7 | 核心逻辑覆盖率 ≥60% | 覆盖率报告数字 | D |
| 8 | 缺陷修复记录（`test_report.md` §8 缺陷清单更新） | 缺陷表零 P0/P1 | B + C + D |
| 9 | 交叉原型测试记录（问卷 + 建议） | `docs/acceptance/cross_test.md` | D |
| 10 | 回测初版有真实数字 | `backtest_report.md` + `backtest_result.json` | D |
| 11 | CI 三 job 绿 | Actions 链接 | D |

**打勾规则**：第 1/2 项任一红 → **M4 降级**（只保详情页静态展示 + 后端数据）；第 6/7/9 项是课程第 4 天检查点，**必须绿**；第 10 项可缩水但不能没有数字。

## 4. 风险与砍单规则

| 风险 | 症状 | 预防 / 砍单 |
| --- | --- | --- |
| A 依赖/浏览器卡住 | 10:00 还没看到 5173 页面 | 砍到「市场 + 详情 + 买卖」；折线图先用 5 个点；T3-04 降级为「接口级闭环 + 截图」 |
| 价格点不够 10 个 | 折线图验收红 | 用 B 的 `--rounds 8` 配方；必要时把 `ts` 整体平移到过去 |
| 回测做不完 | 17:30 报告空白 | 1 策略 3 指标 + 3 组 seed；限制写清楚 |
| 覆盖率工具装不上 | 无覆盖率数字 | `pip install --user pytest-cov` 或 `coverage run -m pytest`；仍不行则记录命令 + 用测试数/分支覆盖口头说明 |
| 交叉测试约不到组 | 无问卷记录 | 组内互测（A↔B、C↔D），用同一份课件问卷，标注"组内互测" |
| 回测数据口径不一致 | C 的 100 seed 统计与 B 落库价格对不上 | 上午先对 3 条抽样，统一 `reason`/价格口径 |
| 部署凭据/账号没就绪 | 第 5 天卡住 | B 今天下午只做"清单 + 账号可登录"，真正部署留第 5 天 |

## 5. 今日产出物清单

- [ ] T3-04 浏览器全链路截图/录屏（A）
- [ ] 折线图 / 涨跌原因 / AI 卡 / 三态截图（A，M4 证据）
- [ ] 10+ 价格点数据（B，`data/price_updates.json` + 落库后 `/prices` 点数）
- [x] 契约 §7 四人签字齐全（C 已补签 `94ea9aa`）
- [ ] 新增异常测试用例 + 覆盖率报告（D）
- [ ] 缺陷清单更新（B/C/D，P0/P1 清零或记录）
- [ ] `docs/acceptance/cross_test.md`（D，课程 p.179–182 问卷）
- [ ] `scripts/backtest.py` + `docs/algorithm/backtest_result.json` + `backtest_report.md` 初版数字（D）
- [ ] `pricing_model.md` §7 正式回测数据 + 100 seed 统计（C）
- [ ] CI 三 job 绿（D）

## 6. 课件要求 ↔ 今日任务映射

| 课件第 4 天（SWIEP.pdf p.160–183） | 本项目任务 |
| --- | --- |
| 软件测试方法；等价类/边界值/场景法写测试用例（p.177 检查点） | T4-06 新增异常用例；已有 97 条覆盖交易/定价/AI |
| 统计覆盖率，核心逻辑 ≥60%（p.177） | D 上午 `pytest-cov` 统计并写进报告 |
| 测试和修复软件缺陷（p.178） | 交叉测试/用户手册测试 → `test_report.md` §8 缺陷清单 → B/C/D 修 |
| 交叉原型测试问卷（p.179–182） | D 组织、A 演示、B/C 记录 → `docs/acceptance/cross_test.md` |
| 项目里程碑 M4（图表与 AI） | T4-01 折线图、T4-02 原因、T4-04 AI 卡、T4-05 三态 |
| 交付物「回测报告」 | T4-07 + `pricing_model.md` §7 |
