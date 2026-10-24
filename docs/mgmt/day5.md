# 第 5 天任务清单（部署上线 + 完善作品/答辩准备）

> **日期**：第 5 天（上线日，建议 2026-10-25；按团队节奏可提前/顺延）｜ **负责人**：D（维护，全员执行）｜ **里程碑**：**M5 上线可用**
> **课件依据**（SWIEP.pdf p.184–267）：第 5 天第 1 部分「部署作品」（部署模型、发布流程、构建/环境变量/域名 HTTPS、健康检查、上线前/中/后检查单、灰度与回滚）；第 5 天第 2 部分「完善作品：优化和迭代」（p.267）；p.268–270 为第 6 天答辩评分表（**8 分钟幻灯片 40% + 2 分钟演示 40% + 5 分钟问答 20%**）。
> **配套文件**：`milestones.md` 的 T5-01~06、`docs/software/deployment.md`、`docs/acceptance/user_manual.md`、`docs/acceptance/compliance.md`、`docs/acceptance/test_report.md` §6、`render.yaml`。

## 0. 开工基线（2026-10-24 17:15 实测）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| M3 / M4 | ✅ 均已达成 | A 的 16 张浏览器证据：`docs/acceptance/evidence/` |
| 测试 | **120 passed / 0 skipped**（CI 与本机一致；BUG-10 已修，见下） | `test_report.md` §1/§9 |
| 部署准备 | ✅ 已完成 | `bootstrap_demo_data.py`、PG 连接串归一化（+psycopg2）、`pool_pre_ping`、`deployment.md` §3.9 四步全绿 |
| Render / Postgres | ✅ 三个服务已上线：前端 `playerstock-frontend-mdlk`、后端 `playerstock-backend-mdlk`、Postgres 18 `playerstock-db`（**2026-11-23 到期**）；线上已灌 9 轮数据（11 点/人） | `deployment.md` §6、`test_report.md` §6 |
| 线上只读验收 | ✅ TC-401 / TC-402 / TC-406 已实测通过（B 用 HTTP 直连核对） | `test_report.md` §6 |
| 线上交易验收 | ✅ TC-403 已跑通（2026-10-25，B）：买 2 @108.75 → 卖 1 → 并发卖 1 = [200,400]，余额回到 5000.00、持仓清空、流水 3 条；6 类错误码全对 | `test_report.md` §6 |
| 线上待做 | ⬜ TC-404（重新部署后数据仍在，现可用那 3 条流水做基准）、TC-405（子路由刷新，A）；线上部署 `168fb3e` 落后 `origin/develop` 3 个提交，需 Manual Deploy | `test_report.md` §6 |
| 待修 | ~~BUG-03~~ **已修**（2026-10-25，`eb0d7e7`：测试改文件捕获 + `errors="replace"`，`seed_db.py` 输出转 UTF-8；编号记为 BUG-10）；TC-307 已由 A 补截图 | `test_report.md` §9 BUG-10 / `test_plan.md` §4.4 |
| 外部交叉原型测试 | 🟡 内部互测已记录，外部组未约 | `docs/acceptance/cross_test.md` |
| 答辩材料 | ❌ 未开始（幻灯片/演示脚本/QA） | — |

> **今天两条主线**：① **M5 上线**：Render 前后端 + 免费 Postgres，数据持久化，线上全流程验收；② **完善作品 + 答辩准备**：优化迭代清单、8 分钟幻灯片、2 分钟演示脚本、5 分钟 QA。
> **硬前提**：部署分支固定选 **`develop`**（否则 Render 不会随 push 自动部署）；BUG-10 已修，本机/CI 均 120 绿；上线前需处理 **CORS 临时放开**（见 §4 风险表）。

## 1. 全员共同段（09:00–09:40）

| 时间 | 事项 | 动作 | 产出 |
| --- | --- | --- | --- |
| 09:00–09:15 | 站会三问 | 昨天 M3/M4 收口 / 今天上线 / 卡在哪；确认 Render 账号可用、BUG-03 归属 | 口头对齐 |
| 09:15–09:30 | 基线复跑 | 仓库根 `python -m pytest`，修复 BUG-03 后应 **120 passed / 0 skipped** | 终端输出 |
| 09:30–09:40 | 上线分工确认 | D 主操作 Render，B 管后端/数据库，A 管前端构建，C 管价格数据核对；所有操作截图留档 | 部署操作流水 |

## 2. 分工与任务

### 2.1 A 同学：前端上线 + 完善 + 答辩演示（约 7h）

**边界**：只改 `code/frontend/`；不改后端/契约。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–10:40 | **前端生产构建**：`npm ci` → 用线上后端地址设 `VITE_API_BASE_URL` → `npm run build`；`dist/` 产物检查（无本地地址、无密钥） | 构建 exit 0；`dist` 里 grep 不到 `127.0.0.1`/`localhost:8000` |
| 10:40–12:00 | **部署 Render Static Site**（`render.yaml` 或手动 New Static Site，分支 `develop`）；配 `VITE_API_BASE_URL`；绑定公网地址 | 公网页面打开不白屏，Network 能拉到 `/api/players` |
| 13:00–14:30 | **完善作品（A 侧）**：线上走查问题清单（文案/间距/空态/错误态）；修 P1/P2；补 **TC-307 刷新回归**截图 | 问题清单关闭；刷新后数据仍在（截图） |
| 14:30–16:00 | **答辩演示准备**：2 分钟演示脚本（市场→详情→买卖→持仓→流水→AI 卡）；8 分钟幻灯片里前端/交互部分素材 | 演示脚本能按顺序点通；截图/录屏备用 |
| 16:00–17:30 | 与 B/D 走线上全链路；失败项当场修或登记 | 线上买卖/持仓/流水/图表全过 |

### 2.2 B 同学：后端上线 + 数据库 + 持久化（约 7h）

**边界**：`code/backend/`、`scripts/`、`tests/`；契约变更需同步文档。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–10:20 | **修 BUG-03**：bootstrap 测试的 `subprocess` 输出按 UTF-8 容错（`encoding="utf-8", errors="replace"` 或 locale 处理）；本机全仓复跑 | **120 passed / 0 skipped** 本机绿 |
| 10:20–12:00 | **后端部署**：Render Web Service（`render.yaml` Blueprint，分支 `develop`）；建免费 Postgres；填 `DATABASE_URL`（**Internal**）、`CORS_ORIGINS`、`LLM_API_KEY`（可选）；**HTTPS/健康检查** | `/api/health` 公网 200；日志无“误用 SQLite”警告 |
| 13:00–14:30 | **线上灌数据**：用 **External Database URL** 跑 `python scripts/bootstrap_demo_data.py`（或 `seed_db.py` + `simulate_match --rounds 9` + `update_prices --from-json`）；核对点数 | 每名可交易选手 ≥10 个价格点（sh1ro 暂停=2 点）；`/prices` 升序、带 reason |
| 14:30–16:00 | **持久化验收**：线上买一笔 → 重启/重新部署后端 → 再查账户/持仓/流水/价格历史；按 `deployment.md` §4 打勾 | 重启前后完全一致；Postgres 生效（非临时盘） |
| 16:00–17:30 | 线上全链路联调；修线上/本地不一致；**回滚演练**（Redeploy 上一个可用版本） | 全链路通过；回滚步骤有记录 |

### 2.3 C 同学：价格数据/接口上线核对 + 完善 + 答辩（约 5h）

**边界**：`code/core_engine/`、`docs/algorithm/pricing_model.md`、`scripts/simulate_match.py`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–11:00 | **线上价格核对**：seed 后抽查 3 名选手 `/prices` 的 S/得分/reason 与 `current_price` 关系；验证 `POST /api/prices/recalc` 幂等 | 抽样一致；重复 recalc 不重复落库 |
| 11:00–12:30 | **完善作品（C 侧）**：`pricing_model.md` 第 6 天定稿前的最后校对（α/β/floor/clamp/3σ/100 seed 表）；准备答辩用“一涨一跌”案例 | 参数表无空；案例可在页面复现 |
| 14:00–16:00 | **答辩幻灯片定价部分**：公式推导、参数含义、100 seed 稳定性、下行风险说明（α 敏感性） | 8 分钟版里定价 2–3 页 |
| 16:00–17:30 | 配合线上全流程验收；价格异常/回滚场景确认 | 线上价格链路无阻断问题 |

### 2.4 D 同学：部署主操作 + 线上验收 + 文档/答辩（约 8h）

**边界**：`.github/`、`render.yaml`、`docs/`（除 `pricing_model.md`）、`code/backend/ai/`。

| 时段 | 任务 | 完成标准 |
| --- | --- | --- |
| 09:40–11:00 | **Render 主操作**：注册/登录 → New Blueprint 导入 `render.yaml`（分支 `develop`）→ 建免费 Postgres → 配环境变量（`DATABASE_URL` Internal / `CORS_ORIGINS` / `LLM_API_KEY` 可选）→ 记录服务 URL | 前后端服务 Running；HTTPS 可访问 |
| 11:00–12:30 | **上线检查单（前/中/后）**：构建产物、环境变量、数据库迁移/初始化、健康检查、日志、敏感值不打印；`deployment.md` §3 逐项填写 | 检查单无空白项 |
| 13:00–15:00 | **线上验收 TC-401~406**：健康检查、CORS、线上买卖闭环、重启持久化、子路由刷新、无密钥全站可用；截图 | `test_report.md` §6 全部 ✅ + 截图 |
| 15:00–16:30 | **部署文档定稿**（`deployment.md` §6 地址/已知问题、§8 回滚）＋ `user_manual.md`/`compliance.md` 校对；外部交叉原型测试记录（约不到就写延期原因） | 文档可交付 |
| 16:30–18:00 | **答辩材料**：8 分钟幻灯片大纲（问题→方案→演示→工程/测试/部署→反思）、2 分钟演示脚本、5 分钟 QA 问题清单；组织第 1 次完整彩排（录像） | 幻灯片/脚本/QA 三件套齐；彩排完成 |

## 3. 晚验收（对照 M5 + 课程 p.184–267 + 第 6 天答辩 p.268–270）

| # | 验收项 | 判定证据 | 责任人 |
| --- | --- | --- | --- |
| 1 | 公网后端 `/api/health` 返回 `{"status":"ok",...}` | 浏览器/curl 截图 | B + D |
| 2 | 公网前端页面打开不白屏，能拉到行情 | 截图 + Network | A + D |
| 3 | CORS 正常（前端无跨域报错） | Console/Network 截图 | A + D |
| 4 | 线上完成一次买入 → 持仓 → 卖出 → 流水 | 线上截图 + 数据库/接口核对 | A + B |
| 5 | 线上 AI 分析可用（无密钥时 `rule_fallback`，200 不报错） | 详情页 AI 卡截图 | A + D |
| 6 | **重启/重新部署后，余额/持仓/流水/价格历史仍在** | 重启前后对比 + 日志无 SQLite 警告 | B + D |
| 7 | 线上折线图 ≥10 点、涨跌原因、AI 卡、三态正常 | 线上截图 | A |
| 8 | 子路由刷新（`/players/1`、`/positions`、`/trades`）不 404 | 浏览器刷新截图 | A |
| 9 | 前端产物/源码无写死本地地址、无密钥泄漏 | `grep` + 截图 | D |
| 10 | `deployment.md` 定稿（URL、环境变量、回滚、已知问题） | 文档 | D |
| 11 | BUG-03 修复，本机 120 passed / 0 skipped | pytest 输出 | B |
| 12 | 交叉原型测试记录（外部组或延期说明） | `cross_test.md` | D |
| 13 | 答辩三件套（幻灯片 8min / 演示 2min / QA 5min）+ 彩排 | 文件 + 录像/纪要 | 全员 |

**打勾规则**：第 1–7 项任一红 → **M5 不达成**，必须当场修（**需求不降级**，不写“线上不可用但本地可演示”）；第 11 项今天必须绿；第 13 项最晚第 6 天上午完成。

## 4. 风险与回滚（不砍需求，只做风险缓解）

| 风险 | 症状 | 缓解 / 回滚 |
| --- | --- | --- |
| 临时放开 CORS（`allow_origins=["*"]`，`9abacf9`） | 与 `CORS_ORIGINS` 设计/合规口径冲突 | 部署前改回 `settings.cors_origin_list`，并在 Render 配 `CORS_ORIGINS`=前端公网地址（B/D 执行） |
| 免费 Postgres 30 天到期 | 答辩后数据消失 | 文档写明；如需要可换 Neon（同样只改 `DATABASE_URL`） |
| 免费实例 15 分钟休眠 | 冷启动约 1 分钟，演示卡顿 | 演示前 5 分钟预热 `/api/health`；录屏兜底 |
| `DATABASE_URL` 填 Internal/External 混用 | 本地连不上/线上报错 | 后端用 **Internal**，本地灌数用 **External**；填错立即改并重启 |
| 分支不是 `develop` | push 后不自动部署 | Blueprint 创建时确认分支；改分支后手动 Redeploy |
| CORS 漏配前端域名 | 浏览器跨域报错 | 填 `CORS_ORIGINS` = 前端公网地址；改完重启服务 |
| 前端构建期变量漏配 | 线上请求打到 localhost | 在 Render Static Site 配 `VITE_API_BASE_URL` 后重新 build |
| 线上数据未灌 | 折线图空、页面无数据 | 用 `bootstrap_demo_data.py`（External URL）重跑；核对点数 |
| 线上/本地行为不一致 | 线上 500/字段异常 | 按 `deployment.md` §7 排查；必要时 **Redeploy 上一个可用版本**（回滚演练） |
| 答辩当天网络/平台故障 | 无法演示 | 提前录 2 分钟演示视频 + 本地环境兜底；不改变验收标准，只做展示备份 |

## 5. 今日产出物清单

- [ ] 公网地址：后端 `https://…` / 前端 `https://…`（写进 `deployment.md` §6）
- [ ] 线上验收截图：`docs/acceptance/evidence/online/`（健康检查/买卖/持仓/流水/图表/AI/三态/刷新）
- [ ] `test_report.md` §6 TC-401~406 全部 ✅
- [ ] `deployment.md` 定稿（环境变量、检查单、回滚、已知问题）
- [ ] BUG-03 修复 + 本机 120 passed
- [ ] 线上数据：每名可交易选手 ≥10 个价格点（sh1ro 2 点）
- [ ] 答辩三件套：8 分钟幻灯片 / 2 分钟演示脚本 / 5 分钟 QA 清单 + 彩排记录
- [ ] `user_manual.md` / `compliance.md` 终稿
- [ ] 外部交叉原型测试记录（或延期原因）
- [ ] CI 三 job 绿

## 6. 课件要求 ↔ 今日任务映射

| 课件第 5 天（SWIEP.pdf p.184–267） | 本项目任务 |
| --- | --- |
| 部署模型/发布流程（p.184–196） | T5-01/T5-02：Render Static Site + Web Service + Postgres（方案 B） |
| 构建、环境变量、域名/HTTPS（p.197–235） | `VITE_API_BASE_URL`、`DATABASE_URL`、`CORS_ORIGINS`、HTTPS |
| 健康检查/上线前中后检查单（p.236–267） | `deployment.md` §3/§5 检查单 + TC-401~406 |
| 灰度发布、回滚、故障处理 | §4 回滚演练（Redeploy 上一版本） |
| 第 5 天第 2 部分：完善作品（p.267） | A/B/C 的线上问题清单修复 + TC-307 |
| 第 6 天答辩评分（p.268–270）：8min 幻灯片 40% + 2min 演示 40% + 5min 问答 20% | D 组织三件套与彩排 |
