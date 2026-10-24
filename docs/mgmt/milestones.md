# 6 天冲刺里程碑与 WBS（任务分解）

> **负责人**：D ｜ **截止**：第 1 天定稿，每天更新进度 ｜ **状态**：✅ 已填写（每日更新进度看板）
> **对应课程指标**：#15 里程碑、任务分解 WBS、进度排期、资源分配

## 1. 里程碑总览

| 里程碑 | 时间 | 验收标准（必须是看得见的结果） | 状态 |
| --- | --- | --- | --- |
| M1 骨架可运行 | 第 1 天 | 四人环境都能跑；前端连上后端；接口契约确认 | 🟡 后端可跑、接口契约已实现（D/B/A 已签，**C 待签**）；前端代码已就绪但未在浏览器验证（A） |
| M2 四大模块各自跑通 | 第 2 天 | 市场数据 / 交易接口 / 定价脚本 / AI 原型分别可演示 | ✅ 2026-10-24（四模块均有可演示产物：A 前端 5 页面接真实接口、B 9 接口、C 定价+模拟器、D AI 接口；浏览器联调属 M3/T3-04） |
| M3 交易闭环打通 | 第 3 天 | 浏览器里完成「查行情 → 买入 → 看持仓 → 卖出」，数据入库 | ⬜ |
| M4 亮点完成 | 第 4 天 | 价格折线图 + 涨跌原因 + AI 建议正常展示 | ⬜ |
| M5 上线可用 | 第 5 天 | 有公网地址；线上买卖/查询/AI 各成功一次；重启后数据仍在 | ⬜ |
| M6 可交付 | 第 6 天 | 回归测试通过、文档齐全、PPT 完成、演示排练 ≥2 次 | ⬜ |

## 2. WBS 任务分解

> 编号 `T-<天>-<序号>`；「依赖」填必须先完成的任务；「验收」写清楚"看到什么算完成"。

### 第 1 天：环境 + 骨架 + 接口契约

**全天目标**：四个人各自的电脑都能把项目跑起来，前端能连上后端，接口字段四个人签字确认。
**今天不追求功能，追求“能跑 + 能对接”。**

**必须锁死的 6 个决策（第 2 天起不准改）**

| # | 决策 | 定值 |
| --- | --- | --- |
| 1 | 选手主键字段名 | `player_id`（**不是** `id`） |
| 2 | 价格字段名 | `current_price` / `prev_price` / `change_pct` |
| 3 | 时间格式 | ISO 8601 UTC，例 `2026-01-01T10:05:00Z`（前端 `new Date()` 可解析） |
| 4 | 价格历史必须带原因 | `price_history` 每行必须有 `reason` |
| 5 | 前端 API 地址来源 | 环境变量 `VITE_API_BASE_URL`，**禁止写死** `127.0.0.1:8000` |
| 6 | 后端启动命令 | `uvicorn app.main:app`（**不是** 6 天手册里的 `main:app`） |

> 下表「负责人」= 小节标题里的成员；「全员共同段」四人一起做。
> 今晚 19:30 只认 6 项验收（见 2.6），下面 37 项是**为了通过那 6 项**的执行拆解。

#### 2.1 全员共同段（08:30–09:30，3 项）

| ID | 时段 | 任务与命令 | 依赖 | 完成标准 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T1-01 | 08:30–08:45 | 站会，三问各 60 秒：昨天做了啥 / 今天做啥 / 卡在哪 | — | 当日计划口头对齐，无分歧 | ✅ 第 1 天（`daily_summary.md` 有站会记录） |
| T1-02 | 08:45–09:15 | 环境三验：`python --version`（3.12/3.13）、`node --version`（≥20 LTS）、`git --version` | — | 三条版本号截图发群 | ✅（第 2 天补验：conda 环境 Python 3.13 / Node 24 / Git 可用，测试可跑） |
| T1-03 | 09:15–09:30 | `git clone` 仓库 → 切分支（`feat/a-frontend` / `feat/b-backend` / `feat/c-pricing` / `feat/d-ai-deploy`）→ 读 `docs/software/api_contract.md` 与 `architecture.md` | T1-02 | 每人回一句“已读，我有 X 个疑问” | ✅（仓库 + develop/main 已建；`feat/*` 未采用，团队直接提交 develop，已定案） |

#### 2.2 A 同学：前端（8 项，约 5.5h）

**边界**：只改 `code/frontend/`，不碰 `code/backend/` 任何文件。

| ID | 时段 | 任务与命令 | 依赖 | 完成标准 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T1-04 | 09:30–09:45 | **解除目录阻塞**：`Move-Item code/frontend/README.md docs/software/frontend_setup.md`（否则脚手架会因目录非空失败；该说明要保留，不要直接删） | T1-03 | `code/frontend/` 为空目录；`docs/software/frontend_setup.md` 存在 | ⬜ |
| T1-05 | 09:45–10:15 | `npm create vue@latest code/frontend`；选项：TS=Yes / JSX=No / Router=Yes / Pinia=No / Vitest=Yes / E2E=No / ESLint=Yes / Prettier=Yes | T1-04 | 脚手架生成成功 | ⬜ |
| T1-06 | 10:15–10:35 | `cd code/frontend` → `npm install` → `npm run dev` | T1-05 | 浏览器打开 `localhost:5173` 显示初始页 | ⬜ |
| T1-07 | 10:35–10:55 | 新建 `code/frontend/.env.example`（`VITE_API_BASE_URL=http://127.0.0.1:8000`）+ `src/api/client.ts`（从 `import.meta.env` 读地址，封装 `get/post`） | T1-06 | 代码里搜不到硬编码的 `127.0.0.1` | ✅ 2026-10-24（`.env.example` + `client.ts` 已建；client.ts 只读 `VITE_API_BASE_URL`、缺省与错误文案不再写死地址；CI 前端 job 加地址检查防回归） |
| T1-08 | 10:55–11:30 | **今日最关键交付**：HomeView 调 `GET /api/health`，页面显示“连接成功：playerstock-backend” | T1-07, T1-13 | 页面出现连接成功文案 | ⬜ |
| T1-09 | 13:00–14:00 | 配 4 条路由：`/` 市场、`/players/:id` 详情、`/positions` 持仓、`/trades` 流水；各建空 view | T1-06 | 4 个路径可切换、不白屏 | ⬜ |
| T1-10 | 14:00–15:30 | 统一顶部导航（Logo / 市场 / 持仓 / 流水 / 余额占位）+ 抽 `LoadingState` / `EmptyState` / `ErrorState` 三个组件 | T1-09 | 每个页面都有统一顶栏 | ⬜ |
| T1-11 | 15:30–17:30 | 对着契约核对字段（`player_id` / `current_price` / `change_pct` / `rating` / `role` / `latest_reason` / `avg_cost` / `market_value` / `profit`）→ 缺的当场提给 B → 与 B 联调 5173×8000 → 提 PR（模板勾“接口变更：否”）+ 补 `docs/requirements/wireframes/README.md` | T1-08, T1-16 | PR 已建；CI 前端 job 转绿；契约下留一行确认 | ⬜ |

#### 2.3 B 同学：后端与交易系统（9 项，约 6h）

**边界**：只改 `code/backend/app/{api,models,schemas,core}`、`code/backend/requirements.txt`、`scripts/seed_db.py`；不碰 `code/frontend/`、`code/core_engine/`、`code/backend/ai/`。

| ID | 时段 | 任务与命令 | 依赖 | 完成标准 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T1-12 | 09:30–09:55 | `cd code/backend` → `py -3.12 -m venv .venv` → `.\venv\Scripts\Activate.ps1` → `pip install -r requirements.txt` → `Copy-Item .env.example .env` | T1-03 | 终端出现 `(.venv)`；`git status` 看不到 `.env` | ✅（用 conda 环境 `playerstock` 代替 venv；依赖已装、测试可跑） |
| T1-13 | 09:55–10:20 | **后端三验**：`python -m uvicorn app.main:app --reload --port 8000`，验证 `/`、`/api/health`、`/docs` | T1-12 | 三个页面截图发群（第 1 个里程碑） | ✅（`/`、`/api/health`、`/docs` 可用，`test_health.py` 覆盖） |
| T1-14 | 10:20–11:30 | 按 `database_design.md` 建 5 张表：`User/Player/Position/Trade/PriceHistory`；`players` 含 `role`（真实位置）与 `rating`（模拟评分）；`positions` 加 `UNIQUE(user_id, player_id)`；`trades` 加 `INDEX(user_id, created_at)`；跑通 `init_db()`；把 `database_design.md` 定稿 | T1-13 | `playerstock.db` 生成成功；文档无空白节 | ✅（5 张表 `init_db()` 通过，见 `database_design.md`） |
| T1-15 | 11:30–12:00 | `sqlite3 playerstock.db ".schema"`（或 Python 读 `sqlite_master`）自测，把实际 schema 贴进 `database_design.md` 附录 | T1-14 | 文档与实际表 100% 一致 | ✅（实际 schema 已写入 `database_design.md` §2） |
| T1-16 | 13:00–14:00 | **主持接口契约评审**：逐条过 10 个接口 + 字段防扯皮表；确认 `role`（真实位置）与 `rating`（模拟评分，UI 需标注）已进契约；A 确认能渲染、C 确认价格字段、D 确认 AI 输入可拼；四人各留一行确认 | T1-14 | `api_contract.md` 有 4 行确认记录 | 🟡 契约已冻结并全部实现；确认记录仅 D 签字，A/C 待签 |
| T1-17 | 14:00–15:00 | 实现只读接口 `GET /api/players`、`GET /api/account`（demo 用户 + 5000 余额） | T1-16 | Swagger 能试出数据 | ✅（`test_api_players.py` 覆盖） |
| T1-18 | 15:00–16:30 | 实现 `POST /api/trades/buy` 骨架：正整数校验 → 查选手 → 查余额 → 事务内扣款+加持仓+写流水，失败返回 400 + 中文 `message` | T1-17 | 买 2 股（价 126.00）后余额 4748.00、持仓 +2、流水 +1 | ✅（买入/卖出事务已实现） |
| T1-19 | 16:30–17:30 | 写第一批真测试：正常买入 / 余额不足 / 非法数量（把 `tests/unit/test_trades_rule.py` 对应 skip 去掉） | T1-18 | `python -m pytest` 全绿 | ✅（`test_trades_rule.py` 9 条全绿） |
| T1-20 | 17:30–18:00 | 提后端 PR（勾“接口变更：是，已更新 api_contract”），CI 后端 job 绿 | T1-19 | PR 已建 | ✅（PR 流程已走通，CI 后端 job 绿） |

> **可砍规则**：若 16:00 前还在挣扎环境，立刻砍掉 T1-18/T1-19，今天必须保住 **T1-13 三验 + T1-14 表结构 + T1-16 契约签字** 三件事，买入留到第 2 天。

#### 2.4 C 同学：行情与定价（7 项，约 5h）

**边界**：只改 `code/core_engine/`、`data/seed_players.json`、`docs/algorithm/pricing_model.md`、`scripts/simulate_match.py`；**绝不**改 `app/api`、`app/models`。

| ID | 时段 | 任务与命令 | 依赖 | 完成标准 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T1-21 | 09:30–10:45 | 审 `data/seed_players.json`（已按 CS2 场景给出 8 名真实 CS2 选手，身份公开、价格与评分为模拟，字段 `player_id` / `name` / `display_name` / `team` / `role` / `initial_price` / `current_price` / `rating` / `status`），确认价格与评级合理 | T1-03 | `json.load` 通过，8 名选手，无重复 id | ⬜ |
| T1-22 | 10:45–11:30 | 定稿 `pricing_model.md`：公式 `P' = max(floor, P×(1+αS+βD))`、α=0.15 / β=0 / floor=1.0 / 窗口 N=5、**单次涨幅 clamp 上限**（建议 ±20%，今天必须定一个数并写进文档） | T1-21 | 参数表无空白；clamp 有具体值 | ⬜ |
| T1-23 | 13:00–14:00 | 与 B 对齐三件事：① 价格存 `players.current_price`；② 历史存 `price_history(player_id, price, reason, ts)`；③ 谁触发价格更新（定时任务 or 手动脚本） | T1-22 | 结论写进 `mechanism_design.md` 并勾掉“待定项” | ⬜ |
| T1-24 | 14:00–15:00 | 参加契约评审，重点确认 `GET /api/players/{id}/prices`：时间升序、每点带 `reason`、空历史返回 `[]` 而非 404 | T1-16 | 契约签字 | ⬜ |
| T1-25 | 15:00–16:30 | 在 `code/core_engine/pricing.py` 实现 `update_price` + `standardize_score`，去掉 `tests/unit/test_pricing.py` 的 skip | T1-22 | 5 条定价测试全绿 | ⬜ |
| T1-26 | 16:30–17:30 | `python scripts/simulate_match.py --seed 42`：能打印比赛结果；若 `update_price` 已完成，能打印“旧价 → 新价 + reason” | T1-25 | 命令行看到一条价格变化及原因 | ⬜ |
| T1-27 | 17:30–18:00 | 在 `pricing_model.md` 第 8 节填“至少一个涨、一个跌”案例占位；提定价 PR | T1-26 | 两个案例各一行 | ⬜ |

> 今天的交付是 **公式 + 数据 + 数据结构共识**，不要求“价格必须动起来”——价格真跑起来是第 2 天。

#### 2.5 D 同学：AI / 部署 / 文档（10 项，约 6h）

**边界**：只改 `code/backend/ai/`、`docs/`（除 `pricing_model.md`）、`.github/`、`render.yaml`；不碰 A/B/C 的代码目录。

| ID | 时段 | 任务与命令 | 依赖 | 完成标准 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T1-28 | 09:30–10:00 | 仓库体检：确认 `git status` 里**没有** `.env`、`*.db`、`node_modules`；`.gitignore` 生效；确认 GitHub 仓库地址与分支约定 | T1-03 | 一次干净提交，无关文件 0 | ✅（`.gitignore` 生效，无 `.env` / `*.db` / `node_modules` 提交） |
| T1-29 | 10:00–10:45 | 填 `docs/requirements/problem_definition.md`：5W1H 五维 + 痛点映射 + **产品边界（明确不做什么 ≥5 条）** | T1-03 | 五个维度无空白 | ✅（5W1H + 不做清单已落文档） |
| T1-30 | 10:45–11:30 | 填 `docs/algorithm/ai_agent_prompt.md`：输入上下文 JSON（B 要能拼出来，含 CS2 指标）、输出必须含 `action/reason/risk_level/source/disclaimer`、超时 20s、无密钥降级 | T1-29 | 与 B 确认“你要给我的字段”清单 | ✅（输入/输出契约与失败链路已定稿） |
| T1-31 | 13:00–13:45 | 主持需求评审（15 分钟）：过一遍 5W1H 与“不做什么”，A/B/C 各提 1 个反对意见并记录 | T1-29 | 评审结论写进 `daily_summary.md` | ✅（评审问题与决策记录在 `daily_summary.md` 第 1 天「今日问题与决策」） |
| T1-32 | 13:45–14:30 | 部署方案预研（**今天不部署**）：注册 Render；确认 Static Site / Web Service 配置、免费实例会休眠、**SQLite 临时盘会丢数据**；结论补进 `deployment.md` 第 4 节 | — | 明确第 5 天走持久盘还是 PostgreSQL | ✅（`deployment.md` §3–§4 已定方案 B：Static Site + Web Service + 免费 Postgres） |
| T1-33 | 14:30–15:00 | 参加契约评审，确认 `GET /api/analysis/{player_id}` 字段与错误码，并确认“AI 绝不改余额”写进契约 | T1-16 | 契约签字 | ✅（`api_contract.md` §4.10 已签字，含 AI 只读保证） |
| T1-34 | 15:00–16:00 | 在 `code/backend/ai/fallback.py` 实现 `rule_based_advice`（纯阈值规则，不调模型） | T1-30 | 给定上下文返回合法 JSON（无需模型） | ✅（`fallback.py` + `test_ai_fallback.py` 6 条） |
| T1-35 | 16:00–17:00 | 通读 `README.md`：补四人分工与联系方式、复核启动命令、确认“已知偏差”5 条全员知情 | T1-28 | README 可直接给老师看 | ✅（README 已含分工/启动/已知偏差） |
| T1-36 | 17:00–17:30 | 确认 `risk_plan.md` 前三个高风险有预案；开写 `daily_summary.md` 第 1 天（站会 + 晚验收） | T1-31 | 两份文档有实质内容 | ✅（风险 Top3 预案 + 第 1 天记录已落盘） |
| T1-37 | 17:30–18:00 | 提交文档 PR；确认 CI 三个 job：后端 pass、前端 pass/skip、交付物检查 pass | T1-36 | CI 全绿 | ✅（CI 已改为监听 main+develop，三 job 绿） |
| T1-38 | —（2026-10-24 补记） | **仓库协作三件套**（课件第 1 天 p.28）：GitHub Kanban / Team Planning / Bug Tracker + 提交仓库链接 + 通过 Issues 收第一轮反馈 | — | 仓库有看板/里程碑/Issue 流程，能展示协作痕迹 | 🟡 仓库 + README + PR 流程 + 2 条 Issue 已有；Kanban / Team Planning / Milestones 尚未建（需 GitHub 网页操作，用户/B 执行） |
| T1-39 | —（2026-10-24 补记） | **需求规范书**（课件第 1 天 p.52）：`docs/requirements/functional_spec.md` + `nonfunctional_spec.md` + **领域类图 UML**（3 分钟汇报用） | T1-29 | 两份需求文档齐全；UML 领域类图可讲解 | ✅ 2026-10-24（两份文档已有；`functional_spec.md` §3 补 UML 领域类图 + 类到实现映射） |
| T1-40 | —（2026-10-24 补记） | **沟通 / 风险管理计划**（课件第 1 天 p.53）：沟通管理计划 + 风险管理计划（本项目合并进根目录 `project_management_plan.md`，`docs/mgmt/communication_plan.md` / `risk_plan.md` 为指针文件） | — | 两份计划有实质内容且为唯一事实来源 | ✅ 2026-10-24（沟通 §1–8 / 风险 §9–11 已合并定稿；与课件命名不同，映射关系已注明） |

#### 2.6 19:30 晚验收（20–30 分钟，逐条打勾）

| # | 验收项 | 判定证据 | 责任人 |
| --- | --- | --- | --- |
| 1 | 四人环境都能运行（Python / Node / Git） | 各自终端版本号截图 | 全员 |
| 2 | FastAPI 启动，`/api/health` 返回 ok | 浏览器打开 `127.0.0.1:8000/api/health` | B（T1-13） |
| 3 | Vue 启动，浏览器能打开页面 | 5173 页面截图 | A（T1-06） |
| 4 | **前端显示后端连接成功** | 页面出现“连接成功：playerstock-backend” | A+B（T1-08） |
| 5 | 代码已提交、远程仓库已创建 | 仓库地址 + 至少 4 个 PR | 全员（T1-11/T1-20/T1-27/T1-37） |
| 6 | 四人分工 + 接口字段已确认 | `api_contract.md` 下四行确认记录 | B 主持（T1-16） |

**打勾规则**：第 4 项没绿，今天不算完成——它是第 3 天交易闭环的地基。

#### 2.7 第 1 天最容易翻车的 5 个点

| 风险 | 症状 | 预防 |
| --- | --- | --- |
| `code/frontend/` 非空导致脚手架失败 | `npm create vue` 报目录非空 | 开工第一件事做 T1-04 |
| 启动命令照抄手册 `main:app` | `Could not import module "main"` | 必须 `uvicorn app.main:app`，且在 `code/backend/` 下执行 |
| 接口字段各写各的 | 前端拿到 `undefined` | T1-16 必须签字；改字段走 PR“接口变更” |
| 密钥/数据库被提交 | PR 里出现 `.env`、`playerstock.db` | `.gitignore` 已配，提交前 `git status` 自查（T1-28） |
| C 和 B 都以为对方会存历史价 | 第 3 天发现 `price_history` 空表 | T1-23 那场对齐会必须定“谁写入” |

> **状态回填口径（2026-10-24）**：上表 40 项的 ✅ 是**当前已验证的最终状态**，不代表第 1 天 19:30 晚验收时已绿——
> 当晚实况见 `daily_summary.md` 第 1 天段（环境未验证、后端 5 表未建、契约仅 D 签字、A 前端 0 项），
> 多数在当晚 19:46 与第 2 天补完。**T1-38~40 是课件第 1 天实践/检查点要求，原 WBS 漏项，2026-10-24 补记**。

### 第 2 天：四大模块各自跑通

| ID | 任务 | 负责人 | 依赖 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T2-01 | 行情/详情/账户/持仓/流水接口 | B | T1-14 | Swagger 可测 | ✅ 2026-10-23（B 提交 5 表 / 9 接口） |
| T2-02 | 买入/卖出接口 + 事务 | B | T2-01 | 余额与持仓同步变化 | ✅ 2026-10-23（交易闭环 + 27 条新测试） |
| T2-03 | 交易边界测试（余额不足/超上限/非法数量） | B | T2-02 | pytest 通过 | ✅ 2026-10-23（`test_trades_rule.py` 等全绿） |
| T2-04 | 市场页 + 选手详情页（模拟数据） | A | T1-06 | 页面有可见内容 | ✅ 2026-10-24（`MarketView` / `PlayerDetailView` + 路由已就绪，见 A 的 `9782dc7`） |
| T2-05 | 买卖表单 + 持仓页 | A | T2-04 | 表单可提交（可先 mock） | ✅ 2026-10-24（`TradePanel` 买卖表单 + `PositionsView` / `TradesView`，均已接真实接口） |
| T2-06 | `update_price` + `standardize_score` | C | T1-21 | 定价脚本独立可跑 | ✅ 2026-10-24（`pricing.py` 实现完成，`test_pricing.py` 10 条全绿） |
| T2-07 | 模拟比赛发生器（固定 seed） | C | T1-21 | 同 seed 结果一致 | ✅ 2026-10-24（`simulator.py` 实现完成；同 seed 复现断言已由 `test_simulator.py` 3 条覆盖，TC-106 ✅） |
| T2-08 | AI 原型（给数据出结构化建议） | D | T1-30 | 命令行能输出 JSON | ✅ 2026-10-23（三态实测） |
| T2-09 | 规则版兜底建议 | D | T2-08 | 无密钥时返回合法结构 | ✅ 2026-10-23（第 1 天提前完成） |
| T2-10 | 用户故事清单 `docs/requirements/user_stories.md`（≥5 条 INVEST + 验收条件） | D（A 补前端视角） | T1-29 | 每条故事有 AC，后端可验证的 AC 有测试证据 | ✅ 2026-10-24（7 条 INVEST + AC，附验收落地状态表） |
| T2-11 | 原型展示 `docs/software/prototype/index.html`（AI 生成的交互原型） | D 出稿 → A 确认 | — | 可点击的 5 个界面 + 交易/AI 建议交互，教师可评估可行性 | ✅ 2026-10-24（AI 生成草稿，18 项交互自测通过；A 确认后作为前端实现基线） |
| T2-12 | 技术方案调研 `docs/software/architecture.md`（选型论证 + 未来 2 周新技术自学计划与 Milestone） | B + D | T1-16 | 选型有备选对比；新技术有负责人/时间窗/验收 Milestone | ✅ 2026-10-24（补 §4.1 选型论证 + §7 自学计划，Milestone 对齐 M4–M6） |

### 第 3 天：交易闭环（硬卡点）

| ID | 任务 | 负责人 | 依赖 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T3-01 | 价格更新落库 + 历史查询接口 | B + C | T2-06 | `/prices` 返回升序序列 | ✅ 2026-10-24（B `5f069ee` 价格落库脚本 + C 定价实现；`test_price_update.py` 6 条；reason 可追溯 TC-110 ✅） |
| T3-02 | 前端接真实接口（列表/账户/买卖/持仓/流水） | A | T2-02 | 不刷新页面也能更新 | 🟡 2026-10-24（5 个视图已接真实接口：`api.listPlayers/getPlayer/getPriceHistory/getPositions/listTrades/buy/sell/getAnalysis`；浏览器端尚待 A 装依赖后验证） |
| T3-03 | 错误提示展示（后端 message 直出） | A | T3-02 | 余额不足有中文提示 | ✅ 2026-10-24（`TradePanel` + 4 个视图统一 `err instanceof ApiError ? err.message`，后端中文 message 原样展示） |
| T3-04 | **全链路联调**：查行情→买入→看持仓→卖出 | A+B+C | T3-01, T3-02 | 浏览器里真实跑通 | ⬜（代码已就绪；等 A 装依赖起前后端做浏览器验证，M3 唯一闸门） |
| T3-05 | 数据持久化验证（重启后端数据仍在） | B | T3-04 | 重启后持仓仍正确 | ✅ 2026-10-24（B 会话实测：重启前后余额/持仓/流水/价格历史四项一致；证据已写入 `test_report.md` §2.3，含复现命令） |
| T3-06 | 集成测试用例（e2e） | D | T3-04 | `tests/integration/` 有可用用例 | ✅ 2026-10-23（接口级 2 条已跑通；浏览器全链路 T3-04 待 A） |
| T3-07 | 代码质量闭环（课件第 3 天 p.144–158）：ruff 静态扫描 + Top5 重构（先补测试）+ 质量报告 + CI 加 lint 门槛 | D | T1-37 | 扫描报告 + 重构前后对比（检查点要求） | ✅ 2026-10-24（`docs/acceptance/code_quality_report.md`：51→44，D 负责文件 0 残留，pytest 65/5 不变） |

### 第 4 天：图表与 AI

| ID | 任务 | 负责人 | 依赖 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T4-01 | 历史价格折线图 | A | T3-01 | 至少 10 个点 | 🟡 2026-10-24（`PriceChart.vue` + `/prices` 已接；**补点已完成**：`simulate_match --rounds 8 --json data/price_updates.json` + `update_prices --from-json` → 6 人 10 点、`ropz` 9 点、`sh1ro` 2 点，配方见 `database_design.md` §4.1；浏览器渲染待 A 验） |
| T4-02 | 涨跌原因展示 | A + C | T4-01 | 页面展示 reason | ⬜ |
| T4-03 | AI 分析接口 `/api/analysis/{id}` | B + D | T2-08 | 返回合法结构 | ✅ 2026-10-24（第 3 天提前接入，`test_api_ai.py` 7 条 + e2e：6 字段 / 200+rule_fallback / TC-205） |
| T4-04 | AI 建议卡（action/理由/风险） | A | T4-03 | 页面能看到徽标 | ⬜ |
| T4-05 | 加载中/无数据/失败三态 | A | T4-01 | 拔网线能看到失败态 | ⬜ |
| T4-06 | 核心异常测试用例 | D | T3-04 | 边界用例通过 | ⬜ |
| T4-07 | 智能体回测初版 | D | T2-09 | `backtest_report.md` 有数字 | ⬜ |

### 第 5 天：部署上线

| ID | 任务 | 负责人 | 依赖 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T5-01 | 后端部署 + 环境变量 + CORS | D + B | T4-03 | 公网可访问 `/api/health` | ⬜ |
| T5-02 | 前端部署 + `VITE_API_BASE_URL` | D + A | T4-04 | 公网页面能打开 | ⬜ |
| T5-03 | SQLite 持久化方案落地 | D + B | T5-01 | 重启后数据仍在 | ⬜ |
| T5-04 | 线上全流程验收（买卖/查询/AI 各一次） | 全员 | T5-02 | 验收清单打勾 | ⬜ |
| T5-05 | 修复线上与本地不一致问题 | 全员 | T5-04 | 无阻断性 bug | ⬜ |
| T5-06 | 部署说明定稿 | D | T5-04 | `deployment.md` 填完 | ⬜ |

### 第 6 天：冻结与答辩

| ID | 任务 | 负责人 | 依赖 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| T6-01 | 功能冻结（只修 bug） | 全员 | T5-05 | 无新功能 PR | ⬜ |
| T6-02 | 回归测试 + 测试报告 | D | T5-05 | `test_report.md` 完成 | ⬜ |
| T6-03 | 文档补齐（需求/架构/数据库/用户手册/合规） | D + 全员 | T6-02 | CI 交付物检查通过 | ⬜ |
| T6-04 | 答辩 PPT | 全员 | T6-03 | `docs/presentation/` | ⬜ |
| T6-05 | 演示数据固定 + 彩排 2 次 | D | T6-04 | 完整流程 8+2+5 分钟 | ⬜ |
| T6-06 | 每日复盘汇总 | D | T6-05 | `daily_summary.md` 完成 | ⬜ |

## 3. 进度看板（每天更新）

| 天 | 计划任务数 | 完成 | 未完成及原因 |
| --- | --- | --- | --- |
| 第 1 天 | 40（含 3 条补记；必达 6 项验收中第 4 项未绿） | 23 完成 + 2 部分 | A 前端 8 项、C 定价 7 项未开始；T1-16 契约仅 D 签字、T1-38 Kanban/Team planning/Milestones 待建（需 GitHub 网页） |
| 第 2 天 | 12 | 12 完成 | —（A 前端、C 定价补齐后复核；2026-10-24 更新） |
| 第 3 天 | 7 | 5 完成 + 1 部分（T3-01/03/05/06/07 ✅，T3-02 🟡） | T3-04 浏览器全链路待 A 起 `npm run dev` 后点一遍（M3 唯一闸门）；C 契约 §7 待签字；自动化层 **97 passed / 0 skipped**，CI 后端 ruff 四项、前端 `npm ci`/lint/build/vitest 均已本地复跑全绿（见 `test_report.md` §2.3/§2.4） |
| 第 4 天 | 7 | | |
| 第 5 天 | 6 | | |
| 第 6 天 | 6 | | |

## 4. 如果只有 5 天（压缩方案）

| 原计划 | 5 天版调整 |
| --- | --- |
| 第 1 天 环境与接口 | 保留，必须完成 |
| 第 2 天 各模块开发 | 保留，只做核心功能 |
| 第 3 天 前后端集成 | 保留，优先级最高 |
| 第 4 天 AI 与图表 | AI 与图表做最简版本，同时开始部署 |
| 第 5 天 部署交付 | 部署、验收、文档、PPT 并行 |

**优先保住**：交易闭环、价格变化、AI 分析、线上访问。
**直接放弃**：复杂登录、多智能体协作、实时赛事数据、精细动画。
