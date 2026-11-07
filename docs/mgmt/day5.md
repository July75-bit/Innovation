# 第 5 天任务清单（部署上线 + 完善作品/答辩准备 · 执行版）

> **日期**：第 5 天（上线日，实际执行 2026-10-25）｜ **负责人**：D（维护，全员执行）｜ **里程碑**：**M5 上线可用 ✅ 已达成**
> **课件依据**（SWIEP.pdf p.184–267）：第 5 天第 1 部分「部署作品」（部署模型、发布流程、构建/环境变量/域名 HTTPS、健康检查、上线前中后检查单、灰度与回滚）；第 5 天第 2 部分「完善作品：优化和迭代」（p.267）；p.268–270 为第 6 天答辩评分表（**8 分钟幻灯片 40% + 2 分钟演示 40% + 5 分钟问答 20%**）。
> **配套文件**：`milestones.md` T5-01~08、`docs/software/deployment.md`、`docs/acceptance/test_report.md` §6、`docs/acceptance/cross_test.md`、`render.yaml`。
> **本文件读法**：§1 是已完成的部署记录（对应第 1 部分）；§2–§3 是剩余任务与「完善作品」的优化迭代清单（对应第 2 部分）；§4 起是验收与产出物。

## 0. 现状快照（2026-10-25 实测）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| **M5 上线可用** | ✅ 已达成 | 公网地址 + 线上买卖/查询/AI + 重新部署后数据仍在 |
| 前端地址 | `https://playerstock-frontend-mdlk.onrender.com`（Static Site，`develop`） | `deployment.md` §6 |
| 后端地址 | `https://playerstock-backend-mdlk.onrender.com`（Web Service，Python 3 / Free） | `/api/health` → 200 `{"status":"ok"}` |
| 数据库 | Render **PostgreSQL 18**，服务 `playerstock-db`（**2026-11-23 到期**） | `deployment.md` §6 |
| 线上数据 | 9 轮配方，`/prices` **11 点/人**（sh1ro 暂停 2 点）、末点 = `current_price` | `test_report.md` §6 |
| 线上验收 | **TC-401~406 全部 ✅**（TC-405 双侧成立：服务端 200 + 前端 bundle 已含 `/market → /` 重定向，BUG-11 修复已上线） | `test_report.md` §6 |
| 自动化测试 | **137 passed / 0 skipped**（CI 与本机一致；BUG-10 已修，第 5 天又 +17 条：CORS 8 + 只读自检 3 + 错误文案 6） | `test_report.md` §1 |
| T5 任务 | **7 完成（T5-01~07）**，只剩 **T5-08 答辩三件套** | `milestones.md` §3 |
| 优化迭代 | 🟡 按课程「三层模型 + 用户体验检查清单」排查出 8 条缺口（见 §3） | 本文 §3 |
| 外部交叉原型测试 | 🟡 内部互测已做，**外部组未约**（三层模型的"测试反馈"回环未闭合） | `cross_test.md` §4 |
| 答辩材料 | ✅ 已齐（`slides.md` 14 页 / `defense.pdf` 13 页 / `demo-script.md` / `qa.md` 20 问） | `docs/presentation/`（彩排未做） |

## 1. 已完成：部署作品（课件第 5 天第 1 部分）

| 动作 | 结果 | 证据 |
| --- | --- | --- |
| Render Blueprint 导入 `render.yaml` | 三服务创建成功（Static Site + Web Service + Postgres） | `deployment.md` §6 |
| 分支固定 `develop` | push 后自动部署生效 | 同上 |
| 环境变量 | `DATABASE_URL`（Internal）、`VITE_API_BASE_URL`、`CORS_ORIGINS`；`LLM_API_KEY` 未配（走 `rule_fallback`） | `deployment.md` §2 |
| 数据库驱动 | 裸 `postgresql://` 归一化为 `+psycopg2`（否则 SQLAlchemy 2.1 起默认 psycopg3 会起不来） | `test_config_db_url.py` 6 条 |
| 线上灌数 | 本地用 **External URL** 跑 `python scripts/bootstrap_demo_data.py`（一条命令：种子 + 9 轮价格） | `deployment.md` §3.6 |
| 上线检查单 | §5 已勾 8 项（health / 前端 / CORS / 买卖 / 重新部署持久化 / AI / 无密钥 / 地址记录） | `deployment.md` §5 |
| 持久化验收 | 重新部署前后：余额 5000.00、持仓 0、流水 **3 条**、价格点 **11 个** 完全一致 → Postgres 生效 | TC-404 |
| 子路由刷新 | `GET /players/1` → 200（`render.yaml` SPA rewrite 生效） | TC-405 |
| 回滚路径 | Render → Deploys → 选上一成功版本 → Redeploy | `deployment.md` §8 |

## 2. 分人任务与状态（第 5 天全景，2026-10-25 20:20 实测）

> 这一节是**唯一的任务真相**：✅ 已完成 / 🟡 部分 / ❌ 未做。未完成项与 `day6_tasks.md` §1「闸门 A」一一对应。

### 2.0 总表

| 人 | 第 5 天完成度 | 剩余项 |
| --- | --- | --- |
| **A 倪颢容** | 部署 ✅ / 完善作品 ✅（D 代做） | 无剩余；**演示前请 A 按 `demo-script.md` 走查一遍窄屏与键盘操作** |
| **B 胡德昊** | 部署 ✅ / 运维收尾 ✅ | 无剩余：B6（CORS 白名单，线上复验）、B7（证据入库 `evidence/online/backend-debug-db.md`）、B8（回滚演练 `deployment.md` §8.1）、B9（线上性能实测） |
| **C 刘宏** | ✅ 100% | 无（第 6 天只需复核定价页） |
| **D 王泽棠** | 文档 ✅ / 收尾 ✅ | **D7 ✅ / D8 ✅**（PDF 已导出；回归 137 条绿，CI run #80 三 job 绿） |

**第 5 天关闭条件**：A4+A5+A6 ✅ + B6+B7+B8（CORS 决策／2 张截图／回滚演练）+ D7 ✅ D8 ✅ → 才进入第 6 天。
> 现状（2026-11-07）：**A 侧三条、B 侧三项（B6/B7/B8）、D 侧两项均已完成**；只剩 push 后 CI 三 job 复核。

### 2.1 A：前端上线 ✅ + 完善作品 ❌

| ID | 任务 | 状态 | 验收 / 证据 |
| --- | --- | --- | --- |
| A1 | 生产构建 + Render Static Site + `VITE_API_BASE_URL` | ✅ | `playerstock-frontend-mdlk.onrender.com` 打开不白屏、拉到 8 名选手 |
| A2 | 线上走查（文案/间距/空态/错误态） | 🟡 | 第 4 天已闭；无线上的二次走查记录 |
| A3 | TC-307 刷新截图 + 子路由刷新 | ✅ / 🟡 | 深链 F5 截图已有；4 张 F5 图可选补 |
| **A4** | **响应式**：`@media (max-width:720px)`，导航折行、详情页上下排、持仓/流水表格横向滚动、买卖按钮整行 | ✅ | **D 代为实现**（跨边界，已在合并提交说明中标注）；5 处 `@media` 已入库，CI run #70 前端 build 绿 |
| **A5** | **AI「思考中」**：`analysisLoading`，卡片位显示"AI 分析中…" | ✅ | **D 代为实现**；`analysisLoading` 4 处引用（含 token 校验的 finally 复位），CI 绿 |
| **A6** | **无障碍最小集**：折线图 `tabindex`+`@focus` 触发 tooltip、全局 `:focus-visible` 描边、`prefers-reduced-motion` 降级 | ✅ | **D 代为实现**；`PriceChart` 命中区可 Tab 聚焦并出 tooltip，CI 绿 |
| A7 | 2 分钟演示排练（`demo-script.md`） | 🟡 | 2:00 内走完、数字不念错 |

### 2.2 B：部署 ✅ + 运维收尾 🟡

| ID | 任务 | 状态 | 验收 / 证据 |
| --- | --- | --- | --- |
| B1 | Render 三服务（前端/后端/Postgres 18）+ 分支 `develop` | ✅ | 三服务 Live，`deployment.md` §6 |
| B2 | 环境变量 + 驱动修复（`+psycopg2`）+ `pool_pre_ping` | ✅ | `/api/health` 200；BUG-08 已修 |
| B3 | 线上灌数（External URL + `bootstrap_demo_data.py`） | ✅ | `/prices` 11 点/人、末点 = 现价 |
| B4 | 持久化验收（TC-404） | ✅ | 重新部署后 3 条流水 + 11 点不变 → Postgres 生效 |
| B5 | 线上交易闭环 + 6 类错误码（TC-403） | ✅ | `smoke_test_api.py`；[200,400] 只入账一次 |
| **B6** | **CORS 口径决策**（保留 `*` 写理由 / 改回白名单） | ✅ | 已改配置驱动（`b548a0b`）：`resolve_cors_origins()` —— 配了域名→白名单；显式 `*`→放开并 WARNING；没配→退化 `*` 并 WARNING；`tests/unit/test_cors_config.py` 8 条；口径进 `compliance.md` §4.1 |
| **B6.1** | **CORS 线上事故修复**（BUG-12） | ✅ **线上已复验** | 实测线上只放行 `localhost:5173`（`CORS_ORIGINS` 未填）→ 前端被拦。三处补：`render.yaml` 写死前端地址、`resolve_cors_origins()` 增加"线上仍用本地默认值→退化+告警"、尾斜杠归一化；用例 8 条。**线上现在**：`Origin: 前端域名` → 回显该域名；`Origin: evil.example.com` → 无该头（白名单生效，不是 `*`） |
| **B7** | 补 2 张截图：后端日志无 SQLite 警告 / Postgres 控制台表 | ✅ 证据已入库（截图可选） | `docs/acceptance/evidence/online/backend-debug-db.md`：① 日志的等价证据 = `/api/debug/db` 的 `是否 SQLite: false` + 方言 `postgresql`；② 库表清单 = 同接口返回 5 张表与行数（`players 8 / price_history 78 / trades 5 / users 1`）。文档里给了 4 条复跑命令 |
| **B8** | 回滚演练（Redeploy 上一版本并验证） | ✅ 2026-11-07 09:30 | 已执行并记录：Render 选 09:26 版本 Rollback → 部署成功 → `/api/health` 200 → 再手动 Redeploy 最新版本并重开 Auto-Deploy。完整记录（含"回滚只回代码不回数据"的复盘）见 `deployment.md` §8.1 |
| **B9** | 线上性能实测（填 `test_report.md` §8） | ✅ | 预热后 5 次取中位：行情 171.8ms（≤300）、买 308.8 / 卖 196.0ms（≤500）、AI 198.0ms（≤8s）、首屏≈437.8ms（≤3s）；买卖用净额为 0 的一买一卖 |
| 追加（运维收尾） | 预热脚本 + 错误文案「下一步」 | ✅ | `scripts/prewarm.py`（冷启动 49s，写进 `deployment.md` §3.10）；余额/持仓/上限三条错误补「最多可买 / 还能买 / 可卖」（+6 条单测）；线上 `/market` 白屏已修（BUG-11） |

### 2.3 C：定价 ✅ 全部完成

| ID | 任务 | 状态 | 验收 / 证据 |
| --- | --- | --- | --- |
| C1 | 线上价格核对（点数/升序/reason/末点=现价） | ✅ | 只读脚本 `scripts/check_price_history.py`；线上 11 点核对通过 |
| C2 | `POST /api/prices/recalc` 幂等 | ✅ | `test_prices_recalc.py` 5 条 |
| C3 | `pricing_model.md` 校对（α/β/floor/clamp/3σ/100 seed） | ✅ | §7 正式回测 + §7.2 100 seed；§9 TODO 清空 |
| C4 | "一涨一跌"演示案例 | ✅ | §8（seed 42，区间案例 + 单点案例） |
| C5 | 定价 2–3 页幻灯片素材 | 🟡 | 已写进 `slides.md` 06/07 页，**复核属第 6 天** |

### 2.4 D：文档 ✅ + 收尾 🟡

| ID | 任务 | 状态 | 验收 / 证据 |
| --- | --- | --- | --- |
| D1 | 线上验收 TC-401~406（含 TC-405 服务端复核） | ✅ | `test_report.md` §6 全 ✅ |
| D2 | 部署文档定稿（地址/环境变量/检查单/回滚/已知问题） | ✅ | `deployment.md` §6 + §5 勾 8 项 |
| D3 | 证据归档（4 张线上截图改名） | ✅ | `evidence/online/online-account/prices/positions/trades` |
| D4 | `prototype_review.md`（三层模型 + 两张清单） | ✅ | 7 节，含视觉规范与 12 条缺口 |
| D5 | 隐私文案稿 / 交叉测试延期说明 / `user_manual` 线上地址 | ✅ | `compliance.md` §4.2、`cross_test.md` §4、`user_manual` §2 |
| D6 | 答辩三件套材料（`slides.md`/`demo-script.md`/`qa.md`） | ✅ | 14 页 + 20 问 |
| **D7** | **导出 `docs/presentation/defense.pdf`** | ✅ | 13 页 / 539 KB，与 `slides.md` 内容一致；源文件 `build_deck.py` + `defense.html` 一并入库，可重生成 |
| **D8** | **回归 + CI 复核**（137 条 + 三 job 绿 + `test_report` 结论） | ✅ | 本机 **137 passed / 0 skipped** + ruff 三类门槛全绿；**CI run #80（`1a821f6`）三 job success** |

> 详细的任务定义、验收细节与"闸门 A/B"依赖关系见 `docs/mgmt/day6_tasks.md` §1（本节只保留状态总览，避免两处口径漂移）。

## 3. 完善作品：优化迭代清单（课件第 5 天第 2 部分 p.267）

> 依据你给的两页课件——「原型设计：三层模型」与「用户体验检查清单（Nielsen 启发式 + 智能体专项）」——对仓库现状逐条核对后的缺口。**这是 Day 5 第 2 部分的正式任务**，不是额外加需求。

### 3.1 三层模型对照（现状）

| 层 | 状态 | 说明 |
| --- | --- | --- |
| 用户任务与场景 | ✅ | `user_stories.md` 7 条 INVEST + AC、`problem_definition.md` 5W1H |
| 界面设计（结构·组件·流程） | ✅ | `wireframes/README.md`：信息架构 Mermaid + ASCII 线框 + TradePanel 状态表 + 三态表 |
| 视觉设计（色彩·字体·间距） | 🟡 | 色彩 ✅（`main.css` 13 个 token，含 `--up/--down/--warn` 语义色）；字体 36 处硬编码、间距/圆角无 token、**无视觉设计文档** |
| 用户体验（反馈·容错·信任） | 🟡 | 见 §3.2 |
| 测试反馈（回环） | 🟡 | 内部互测 + 16 张证据；外部组问卷未做 |

### 3.2 缺口清单（按优先级，可直接当 Task 用）

> **2026-11-07 更新**：**P0 三条（#1 响应式 / #2 AI 思考中 / #3 无障碍）已完成**，由 D 代为实现，
> 依据是 CI run #70（`4e45433`）：前端 `npm ci + lint + build` 全绿 → 代码可编译；
> 合并时补回了丢失的 `analysisLoading` 复位，避免 AI 卡片永久停在加载态。
> #4–#12 仍按优先级跟踪；视觉设计文档已由 `docs/requirements/prototype_review.md` §3 补齐（#9 的文档层）。

| # | 优先级 | 缺口 | 依据（课件） | 负责人 | 验收方式 |
| --- | --- | --- | --- | --- | --- |
| 1 | **P0** | ✅ 已修：响应式（5 处 `@media (max-width:720px)`） | 智能体专项「响应式」 | D 代做 | CI 前端 build 绿；演示前 A 走查窄屏 |
| 2 | **P0** | ✅ 已修：AI「分析中」占位卡片（含 token 校验复位） | 「等待可感知」 | D 代做 | CI 前端 build 绿 |
| 3 | **P0** | ✅ 已修：折线图数据点可 `tabindex` + `@focus` 出 tooltip、全局 `:focus-visible` 描边、`prefers-reduced-motion` 降级 | 「无障碍：键盘可达、对比度、不只靠颜色」 | D 代做 | CI 前端 build 绿；演示前 A 用 Tab 走查 |
| 4 | P1 | 买卖**无二次确认** | 「防错：危险操作二次确认」 | A | 点"买入"先确认再提交 |
| 5 | P1 | 数量无快捷选项（1/5/10/全部），50 股上限靠记 | 「识别优于回忆」 | A | 快捷按钮可用 |
| 6 | P1 | **Enter 不能提交** | 「高效：快捷键、默认值」 | A | 输入框回车即提交 |
| 7 | P1 | AI 降级只说"AI 暂不可用"，**不说原因**（无密钥/超时/输出异常） | 「拦截可理解：说明原因」 | D（后端）+ A（展示） | 徽标 hover/文案显示具体原因 |
| 8 | P1 | 错误信息给了原因和数值，**没给下一步**（如"可买 1 股"） | 「错误可恢复：原因 + 下一步」 | B（文案）+ A | 余额不足时提示可买股数 |
| 9 | P2 | 视觉设计无文档、字体/间距/圆角未 token 化（43 处字号 / 约 50 处间距硬编码） | 「视觉设计：字体层级、间距与圆角用统一变量」 | A + D | ✅ 文档层已完成（`prototype_review.md` §3 视觉规范）；**代码 token 化待 A**（V-1/V-2） |
| 10 | P2 | AI reason 只有文字数值，无"点开看对应价格点" | 「来源可追溯：可展开核验」 | A | 点 reason 跳到图表对应点 |
| 11 | P2 | 页面只有页脚一句合规声明，无隐私/数据说明 | 「隐私透明」 | A + D | ✅ 文档层已完成（`compliance.md` §4.2 文案稿）；**页面入口待 A** |
| 12 | P2 | 外部交叉原型测试未做 | 「测试反馈」回环 | D | ✅ 延期说明 + 补救方案已写入 `cross_test.md` §4（不伪造记录） |

> **取舍规则**：P0 三条（1/2/3）必须在答辩前修完——它们是检查清单原文点名项，且改动小、风险低；P1 时间允许就做；P2 可写进"已知限制"并在答辩主动说明（诚实 > 假装做完）。

## 4. 晚验收（对照 M5 + 课程 p.184–267 + 第 6 天答辩 p.268–270）

| # | 验收项 | 当前 | 证据 |
| --- | --- | --- | --- |
| 1 | 公网后端 `/api/health` 返回 ok | ✅ | `test_report.md` §6 TC-401 |
| 2 | 公网前端打开不白屏，能拉行情 | ✅ | TC-402 |
| 3 | CORS 正常（无跨域报错） | ✅ | TC-402 |
| 4 | 线上买入 → 持仓 → 卖出 → 流水 | ✅ | TC-403（买 2 @108.75 / 卖 1 / 并发卖 1 = [200,400]） |
| 5 | 线上 AI 分析可用（无密钥走 `rule_fallback`） | ✅ | TC-406 |
| 6 | 重启/重新部署后余额/持仓/流水/价格历史仍在 | ✅ | TC-404 |
| 7 | 线上折线图 ≥10 点、原因、AI 卡、三态 | ✅ | 线上页面（A 截图） |
| 8 | 子路由刷新不 404 | ✅ | TC-405（`/players/1` → 200） |
| 9 | 前端产物/源码无写死地址、无密钥 | ✅ | CI 地址检查 + `grep` |
| 10 | `deployment.md` 定稿 | ✅ | 地址/环境变量/回滚/已知问题齐 |
| 11 | 本机 137 passed / 0 skipped | ✅ | `test_report.md` §1 |
| 12 | 外部交叉原型测试记录 | 🟡 | 待约组或写延期 |
| 13 | 答辩三件套 + 彩排 | 🟡 | 材料齐（§6）；**彩排 0 次**，第 6 天关闭条件 |

**打勾规则**：第 1–11 项已全绿 → **M5 达成**；第 12/13 项是第 5 天第 2 部分与第 6 天的出口条件，最晚第 6 天上午完成（**需求不降级**）。

## 5. 风险与回滚

| 风险 | 症状 | 缓解 / 回滚 |
| --- | --- | --- |
| 免费 Postgres **2026-11-23 到期** | 答辩后数据消失 | 文档已写明；如需长期保留 → 换 Neon（只改 `DATABASE_URL`） |
| 免费实例 15 分钟休眠 | 冷启动约 1 分钟，演示卡顿 | 演示前 10–15 分钟预热 `/api/health`；录屏兜底 |
| CORS 仍为 `allow_origins=["*"]` | 与白名单设计/合规口径冲突 | ✅ **已解决**（B，`b548a0b`）：代码改为 `resolve_cors_origins()` 配置驱动（配了域名→白名单；显式 `*`→放开并 WARNING；没配→退化 `*` 并 WARNING），口径进 `compliance.md` §4.1。**线上还踩过一次**（BUG-12：`CORS_ORIGINS` 未填 → 只放行 `localhost:5173`，前端被拦），已补 `render.yaml` 写死前端地址 + "线上仍用本地默认值→退化并告警" + 尾斜杠归一化；**重新部署后端即生效** |
| `DATABASE_URL` Internal/External 混用 | 本地连不上/线上报错 | 后端用 Internal，灌数用 External；填错立即改并重启 |
| 线上数据被验收操作污染 | 演示时余额/流水不是初始态 | 重新部署后用 External URL 重跑 `bootstrap_demo_data.py --reset` |
| 答辩当天网络/平台故障 | 无法演示 | 提前录 2 分钟演示视频 + 本地环境兜底（不改变验收标准） |
| P0 优化来不及 | 检查清单点名项未做 | 砍演示细节、不砍 P0 三条（响应式/AI 思考中/键盘可达） |

## 6. 今日产出物清单

- [x] 公网地址（前后端 + Swagger + 数据库）→ `deployment.md` §6
- [x] 线上验收 TC-401~406 全部 ✅ → `test_report.md` §6
- [x] 线上证据归档 → `docs/acceptance/evidence/online/`
- [x] `deployment.md` 定稿（环境变量、检查单、回滚、已知问题）
- [x] 线上数据：每名可交易选手 ≥10 个价格点（sh1ro 2 点，属预期）
- [x] 本机/CI 137 passed / 0 skipped
- [x] **答辩三件套**：8 分钟幻灯片（`slides.md` 14 页 + `defense.pdf` 13 页已导出）/ 2 分钟演示脚本（`demo-script.md`）/ 5 分钟 QA（`qa.md` 20 问）
- [x] **优化迭代 P0 三条**（响应式 / AI 思考中 / 无障碍最小集）→ D 代实现，CI run #70 前端 build 绿（`4e45433`）
- [x] `prototype_review.md`（三层模型 + 检查清单对照）→ `docs/requirements/prototype_review.md`
- [x] 外部交叉原型测试：**延期说明 + 补救方案**已写入 `cross_test.md` §4（不伪造记录）
- [x] `user_manual.md` 终稿（线上地址、本地备用、5 条已知问题）／`compliance.md` §4.2 隐私文案稿
- [x] CI 三 job 绿（run #80 `1a821f6` success；本机 137 条 + ruff 亦绿）

> **第 5 天关闭条件（Hard Gate）**：P0 三条合入 ✅ + 上述勾选全绿 + CI 绿（push 后复核）→ 才进入第 6 天。
> 未勾项只剩「CI 三 job 复核」；B 侧运维三项（CORS 口径、日志/Postgres 证据、回滚演练）**均已完成**
> （见 B6/B6.1/B7/B8 行与 `deployment.md` §8.1）。
> 分派见 `docs/mgmt/day6_tasks.md` §1「闸门 A：第 5 天收尾」。

## 7. 课件要求 ↔ 今日任务映射

| 课件第 5 天（SWIEP.pdf） | 本项目任务 | 状态 |
| --- | --- | --- |
| 部署模型/发布流程（p.184–196） | Render Static Site + Web Service + Postgres（方案 B） | ✅ |
| 构建、环境变量、域名/HTTPS（p.197–235） | `VITE_API_BASE_URL`、`DATABASE_URL`、`CORS_ORIGINS`、HTTPS | ✅ |
| 健康检查/上线前中后检查单（p.236–267） | `deployment.md` §3/§5 + TC-401~406 | ✅（剩 2 张截图） |
| 灰度发布、回滚、故障处理 | `deployment.md` §8 回滚路径 | ✅（路径就绪） |
| **第 5 天第 2 部分：完善作品（p.267）** | **§3 优化迭代清单（三层模型 + 用户体验 12 条）** | ✅ P0 三条已修；P1/P2 未做项已如实记为已知限制 |
| 第 6 天答辩评分（p.268–270）：8min 幻灯片 40% + 2min 演示 40% + 5min 问答 20% | §2.4 三件套 + 彩排 | 🟡 三件套齐，彩排未做 |
