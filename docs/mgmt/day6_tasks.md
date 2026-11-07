# 剩余任务分派（第 5 天收尾 → 第 6 天答辩）

> **负责人**：D（维护）｜ **更新**：第 5 天 20:10 ｜ **纪律**：**功能冻结**，只做本文件列出的项；不新增功能、不动契约字段、不改表结构。
> **为什么分两段**：第 5 天第 2 部分「完善作品」（课件 p.267）的 **P0 三条没做完**，必须先关闭，否则第 6 天等于在流沙上答辩。
> **每人只看自己那一节**（§3），直接用聊天工具发过去即可。

## 0. 总览与依赖

```
闸门 A：第 5 天收尾（今天，约 4h）
  A ── P0 三条（响应式 / AI 思考中 / 键盘可达）──┐
  B ── CORS 口径 + 2 张检查单截图 ──────────────┤→ D 合并 → CI 绿 → 第 5 天关闭
  D ── defense.pdf · 文档收口 · 回归 120 条 ─────┘
                          │
                          ▼
闸门 B：第 6 天答辩（次日，约 4h）
  09:00 冻结确认 → 上午各人备稿 → 13:30 彩排 1 → 15:00 彩排 2 → 16:30 演示前 checklist
```

| 闸门 | 通过条件（缺一不可） |
| --- | --- |
| **A（关闭第 5 天）** | ① P0 三条合入并有截图；② CORS 结论写入文档；③ `deployment.md` §5 全勾；④ `defense.pdf` 存在；⑤ 120 条测试 + CI 三 job 绿 |
| **B（进入答辩）** | ① 彩排 ≥2 次并计时（8+2+5 ≤ 15 分钟）；② 演示前 checklist 全勾；③ 线上预热脚本有人负责 |

---

## 1. 闸门 A · 第 5 天收尾

### 1.1 A（前端）—— 3 项必做，1 项可选，约 3h

| ID | 任务 | 怎么算完成 | 依据 |
| --- | --- | --- | --- |
| **A-1** | **响应式**：`@media (max-width: 720px)`——市场表格转卡片、顶部导航折叠、详情页单列、图表整宽 | 375px 宽截图**无横向滚动**；导航可展开/收起 | `prototype_review.md` §4.2 #8 |
| **A-2** | **AI「思考中」**：`PlayerDetailView` 加 `analysisLoading = ref(false)`，AI 卡片位渲染"AI 分析中…"骨架 | 用 DevTools 网络限速 Slow 3G，截到"AI 分析中…"状态 | 同上 #5 |
| **A-3** | **无障碍最小集**：折线图数据点 `tabindex="0"` + `@focus="hoverIdx=i"`；所有 button 加 `:focus-visible { outline: 2px solid var(--text); }` | 只用 Tab+方向键能读出某个点的 tooltip；截图 | 同上 #7 |
| A-4（可选，做 1 个即可） | 买卖二次确认 / 数量快捷按钮 1·5·10 / Enter 提交 | 截图 | `day5.md` §3 P1 |
| A-5（闸门 B 用） | 按 `demo-script.md` 练 2 次演示，核对话术里的成交价/余额是否与线上一致 | 2:00 内走完、数字不念错 | `demo-script.md` |

> **不要做**：不要重构 `api/`、不要改路由、不要动 `docs/`（除第 02 页 PPT 素材）。

### 1.2 B（后端 / 部署）—— 2 项必做，约 1.5h

| ID | 任务 | 怎么算完成 | 依据 |
| --- | --- | --- | --- |
| **B-1** | **CORS 二选一**：① 保留 `allow_origins=["*"]` + 在 `deployment.md` §6 与 `compliance.md` 写明"演示期放开、上线后收紧"；② 改回 `settings.cors_origin_list` + Render 配 `CORS_ORIGINS`=前端域名并重新部署 | 代码与文档**口径一致**；选 ② 则重启后 `GET /api/players` 仍 200 | `deployment.md` §9 TODO |
| **B-2** | 补 2 张截图：① 后端日志无"当前部署在 Render 上却使用本地 SQLite"；② Postgres 控制台能看到 `players`/`trades` 表 | 图存 `docs/acceptance/evidence/online/`；`deployment.md` §5 对应 2 项打勾 | `deployment.md` §5 |
| B-3（闸门 B 用） | 复核 `slides.md` 第 04/05 页：架构版本号、并发时序、BUG-01 数字（5000→5504、卖 4 股） | 与代码/文档逐条一致，改完提 PR | `slides.md` |

### 1.3 C（定价）—— 全在闸门 B，闸门 A 无任务

> C 的第 5 天部分（线上价格核对、`pricing_model.md` 校对）已于 10-25 完成，**闸门 A 期间不用动**。
> 若有空，可提前做 §2.3 的 C-1/C-2。

### 1.4 D（AI / 测试 / 文档）—— 4 项，约 3h

| ID | 任务 | 状态 |
| --- | --- | --- |
| **D-1** | 导出 `docs/presentation/defense.pdf`（Slidev 或浏览器打印） | ⬜ |
| **D-2** | 文档收口：`user_manual.md` 线上地址 ✅、`compliance.md` §4.1 ✅、`day5.md` 勾选、`prototype_review.md` 索引 | 🟡 进行中 |
| **D-3** | 回归：`python -m pytest`（应 120 passed）+ push 后确认 CI 三 job 绿 + `test_report.md` 结论改"可交付" | ⬜ |
| **D-4** | 合并 A/B 的改动，跑一次全链路（线上 market→detail→buy→positions→trades） | ⬜ |

---

## 2. 闸门 B · 第 6 天答辩

> **评分结构**（课件 p.268–270）：幻灯片 **8 分钟 40%** + 演示 **2 分钟 40%** + 问答 **5 分钟 20%**。
> 材料：`docs/presentation/slides.md`（14 页，每页带 `【分:秒｜秒数｜主讲】`）、`demo-script.md`、`qa.md`。

### 2.1 A —— 演示与前端页

| ID | 任务 | 完成标准 |
| --- | --- | --- |
| A-6 | 改 `slides.md` 第 02 页（产品一览：用哪张截图、说什么） | 改完提 PR，页内数字与实际一致 |
| A-7 | **演示主操作**：按 `demo-script.md` 走 2:00，含一次"故意失败"演练（如数量填 999 触发余额不足） | 彩排 2 次都 ≤2:10，无卡壳 |
| A-8 | 演示前 checklist 第一条：确认线上 8 名选手、余额干净 | 截图发群 |

### 2.2 B —— 后端页与"提问老师"

| ID | 任务 | 完成标准 |
| --- | --- | --- |
| B-4 | 改 `slides.md` 第 04/05 页（同 B-3，若闸门 A 已做完则跳过） | 页内数字与代码一致 |
| B-5 | 彩排时扮演"提问老师"：从 `qa.md` 抽 5 问追问，记录答不上来的 | 至少补 3 条进 `qa.md` |
| B-6 | 答辩当天值守线上服务（预热 `/api/health`、必要时重启） | 演示期间 `/api/health` 一直 200 |

### 2.3 C —— 定价页与案例

| ID | 任务 | 完成标准 |
| --- | --- | --- |
| C-1 | 复核 `slides.md` 第 06/07 页：公式 / 参数表 / 3σ / 100 seed（中位 −7.40%）/ 回测表 | 与 `pricing_model.md` §7 §9 逐字一致 |
| C-2 | 准备"一涨一跌"两个现场可点案例（选手+轮次+两句口播），写入 `pricing_model.md` §8 | 现场 3 秒内定位 |
| C-3 | 认领 `qa.md` Q4–Q8（定价 5 问），脱稿 | 彩排时不用看稿 |

### 2.4 D —— 主讲、控时、收尾

| ID | 任务 | 完成标准 |
| --- | --- | --- |
| D-5 | 主讲幻灯片 01/03/08/09/10（其余由 A/B/C 分担，按 slides.md 标注） | 8:00 ±30s |
| D-6 | 控时与切换：演示 2:00 到点提示、问答 5:00 收尾 | 全程 ≤15 分钟 |
| D-7 | 组织 2 次彩排，记录问题到 `docs/presentation/README.md` | 有彩排记录与计时 |
| D-8 | 认领 `qa.md` Q1–Q3（合规）、Q9–Q11（AI）、Q15–Q17（测试/局限） | 脱稿 |

---

## 3. 每人一页（可直接转发）

### 给 A
```
【第 5 天收尾 · 今天 · 约 3h，功能冻结】
A-1 响应式：加 @media (max-width:720px)，市场表格转卡片、导航折叠、详情页单列、图表整宽。
    验收：375px 宽截图无横向滚动 + 导航可收起。
A-2 AI「思考中」：PlayerDetailView 加 analysisLoading，AI 卡片位显示"AI 分析中…"。
    验收：DevTools 限速 Slow 3G，能截到该状态。
A-3 无障碍最小集：折线图数据点 tabindex="0" + @focus 触发 tooltip；button 加 :focus-visible 描边。
    验收：纯键盘能读出某个点的原因。
（可选，三选一）买卖二次确认 / 数量快捷按钮 1·5·10 / Enter 提交。

【第 6 天答辩】
A-6 改 slides.md 第 02 页（产品一览用什么图、说什么）。
A-7 演示主操作：按 docs/presentation/demo-script.md 走 2:00，彩排 2 次，含一次"故意失败"（数量填 999）。
A-8 演示前确认线上 8 名选手在、账户干净，截图发群。

依据：docs/requirements/prototype_review.md §4（P0 三条）、docs/presentation/demo-script.md
```

### 给 B
```
【第 5 天收尾 · 今天 · 约 1.5h，功能冻结】
B-1 CORS 二选一，代码与文档必须一致：
    ① 保留 allow_origins=["*"]，把"演示期放开、上线后收紧"写进 deployment.md §6 + compliance.md；
    ② 改回 settings.cors_origin_list，Render 配 CORS_ORIGINS=前端域名并重新部署（重启后 /api/players 仍 200）。
B-2 补 2 张截图：① 后端日志无"当前部署在 Render 上却使用本地 SQLite"；② Postgres 控制台能看到 players/trades 表。
    图放 docs/acceptance/evidence/online/，再把 deployment.md §5 对应两项打勾。

【第 6 天答辩】
B-3 复核 slides.md 第 04/05 页：架构版本号、并发时序、BUG-01 数字（5000→5504、卖 4 股）。
B-5 彩排时扮演"提问老师"，从 qa.md 抽 5 问追问，答不上来的补进 qa.md。
B-6 答辩当天值守线上服务（预热 /api/health，必要时重启）。

依据：docs/mgmt/day6_tasks.md §1.2 / §2.2、docs/software/deployment.md §5
```

### 给 C
```
【第 5 天收尾】你这边没有任务（线上价格核对、pricing_model.md 校对已于 10-25 完成）。

【第 6 天答辩 · 约 2h】
C-1 复核 slides.md 第 06/07 页，与 pricing_model.md §7/§9 逐字对齐：
    公式、参数（α=0.15 / β=0 / floor=1.0 / clamp ±20% / Z_FULL_SCALE=3）、
    为什么 z/3、100 seed（中位 −7.40% / 均值 −6.46% / 范围 −20.82%~+12.20%）、
    回测表（规则版 −3.52%/回撤 5.90%、随机 −0.59%/2.59%、买入持有 −10.78%/14.88%）。有出入直接改。
C-2 准备"一涨一跌"两个现场可点案例（选手+轮次+两句口播），写进 pricing_model.md §8。
C-3 认领 qa.md Q4–Q8（定价 5 问），脱稿。

依据：docs/mgmt/day6_tasks.md §2.3、docs/algorithm/pricing_model.md §7/§8/§9
```

### 给 D（自己）
```
【第 5 天收尾 · 今天】
D-1 导出 docs/presentation/defense.pdf
D-2 文档收口：user_manual 线上地址 ✅ / compliance §4.1 ✅ / day5 勾选 / README 索引
D-3 回归 120 条 + push 后 CI 三 job 绿 + test_report 结论改"可交付"
D-4 合并 A/B 改动后跑一次线上全链路

【第 6 天答辩】
D-5 主讲 01/03/08/09/10 页（8:00 ±30s）
D-6 控时：演示 2:00 提示、问答 5:00 收尾，全程 ≤15 分钟
D-7 组织 2 次彩排并记录
D-8 认领 qa.md Q1–Q3 / Q9–Q11 / Q15–Q17
```

---

## 4. 完成定义

**M5 关闭（今天）**
- [ ] A-1/A-2/A-3 合入并有截图
- [ ] B-1 CORS 结论写入文档；B-2 两张截图 + `deployment.md` §5 全勾
- [ ] D-1 `defense.pdf` 存在；D-3 120 条 + CI 三 job 绿
- [ ] 未做项如实标注（外部交叉测试延期、LLM 版回测待密钥）

**M6 可交付（第 6 天）**
- [ ] 当天无新功能提交（只修 bug）
- [ ] 彩排 ≥2 次、计时 ≤15 分钟、有记录
- [ ] `docs/presentation/` 四件套齐（README / slides / demo-script / qa / defense.pdf）
- [ ] 演示前 checklist 全勾（线上预热、录屏兜底、数据干净）
