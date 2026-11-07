# 第 6 天任务清单（功能冻结 · 彩排 · 答辩）

> **日期**：第 6 天（2026-11-07）｜ **负责人**：D（维护，全员执行）｜ **里程碑**：**M6 可交付**（当前 ⬜）
> **课件依据**：SWIEP.pdf p.268–270 —— **8 分钟幻灯片 40% + 2 分钟演示 40% + 5 分钟问答 20%**。
> **今日纪律**：**功能冻结**——只修 bug、只改稿子与文档；不新增功能、不动契约字段、不改表结构。
> **本文件即第 6 天的唯一任务来源**（原 `day6_tasks.md` 已并入，编号 A-1…D-10 保持不变，历史引用不作废）。

## 0. 开工基线（2026-11-07 11:50 实测）

| 项 | 值 |
| --- | --- |
| 分支 / 工作区 | `develop` = `origin/develop`，干净 |
| 测试 / CI | **137 passed / 0 skipped**；CI **run #80（`1a821f6`）三 job 绿** |
| 覆盖率 | 91%（839 语句 / 79 未覆盖，要求 ≥60%） |
| 线上 | 前端 `playerstock-frontend-mdlk.onrender.com`（bundle `index-W-YIPE7C.js`，含 A 的组件化）；后端 `/api/health` 200；**Postgres**（`/api/debug/db` 方言 postgresql、`是否 SQLite: false`）；8 选手 / 11 价格点 / 5 表 / 8 条流水 |
| 答辩材料 | `slides.md` 14 页 · `defense.pdf` 13 页（已按修正后的数字重导）· `demo-script.md` 2:00 逐秒 + §0.1 值守流程 · `qa.md` **25 问**（原 20 + B 补 5） |
| 检查单 | `deployment.md` **37/37 全勾**（含 7.2 的重新部署复验） |
| **唯一硬缺口** | **彩排 0 次**（B-5 的"现场追问"也挂在彩排上） |

## 1. 今日目标（三句话）

1. **对稿**：四人各自把自己讲的页对到代码上，数字以代码为准；
2. **彩排两遍**：8 + 2 + 5 = 15:00，计时、有记录；
3. **冻结与兜底**：不新增功能，把线上预热与本地兜底演练一遍。

顺序是「先对稿 → 再空跑 → 彩排 1 → 改稿 → 彩排 2 → 收尾」，不卡具体钟点。

---

## 2. 分工与任务

### 2.1 A 同学：前端 + 演示主操

**边界**：只改 `code/frontend/` 与 `slides.md` 第 02 页。

| ID | 任务 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| A-1 | 响应式：导航抽屉化、详情页上下排、表格转卡片、买卖按钮整行 | 375px 宽无横向滚动 | ✅ **A 已亲验 2026-11-07**（`evidence/23~27`：市场/详情/持仓/流水/抽屉五张） |
| A-2 | AI「思考中」：`analysisLoading` + "AI 分析中…"占位卡 | 限速后在详情页抓到该状态 | 🟡 代码已实现（D 代做，含 token 校验的 `finally` 复位）；**截图仍缺**——A 截到的是整页 `加载中`，不是 AI 卡占位 |
| A-3 | 无障碍最小集：数据点 `tabindex="0"` + `@focus` 出 tooltip、全局 `:focus-visible` 描边、`prefers-reduced-motion` 降级 | 纯键盘能读出某个点 | ✅ **A 已亲验 2026-11-07**（`evidence/28-keyboard-focus.png`：焦点描边 + tooltip 带时间/价格/原因） |
| A-4 | 可选三项：数量快捷按钮 / 买卖二次确认 / Enter 提交 | — | 🟡 **快捷按钮已完成**（`TradePanel.vue:37` 的 `quickQty = [1,5,10,25]`，线上截图可见）；二次确认与 Enter 提交未做，冻结期不做、写进已知限制 |
| A-5 | 按 `demo-script.md` 练 2 次，核对话术里的成交价与余额 | 2:00 内走完、数字不念错 | ⬜ |
| **A-6** | 改 `slides.md` 第 02 页：用哪张截图、说什么 | 页内 8 选手 / 4 路由 / 三态与实际一致 | ⬜ |
| **A-7** | 演示主操作：按 `demo-script.md` 走 2:00，**含一次"故意失败"**（数量填 999 触发余额不足） | 两次彩排都 ≤2:10、无卡壳 | ⬜ |
| **A-8** | 演示前确认：线上 8 名选手在、余额 5000.00、流水干净 | 截图发群 | ⬜ |
| **A-9** | 亲手走查 A-1/A-2/A-3 三项（都是 D 写的，你还没亲眼看过） | 拖窄窗口 + 只用 Tab 走一遍折线图 | ⬜ |

**不做（写进已知限制）**：A-4 的三项与视觉 token 化——冻结期不加功能；被问就答"P0 已清零，P1 在迭代清单里"。

**兜底**：线上打不开 → 切本地 `vite preview` + 本地后端；演示砍"故意失败"分支保主流程。

### 2.2 B 同学：后端 + 线上值守

**边界**：`code/backend/app/**`（只修 bug）、`render.yaml`、`deployment.md`。

| ID | 任务 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| B-1 | CORS 口径二选一（保留 `*` 写理由 / 改回白名单） | 代码与文档口径一致 | ✅ 已改配置驱动（`b548a0b`），`test_cors_config.py` 8 条 |
| B-2 | 2 张截图：后端日志无 SQLite 警告 / Postgres 控制台表 | 证据入库 + `deployment.md` §5 打勾 | ✅ 用 `/api/debug/db` 等价取证：`evidence/online/backend-debug-db.md`（5 表 / 8 选手 / 78 价格点） |
| B-2.1 | CORS 线上事故修复（BUG-12） | 线上白名单生效 | ✅ 已复验：`Origin: 前端域名` 回显、`evil.example.com` 无该头 |
| **B-3** | 复核 `slides.md` 04/05 页：Vue 3.5.42 / TS 6.0 / Vite 8.2.2 / FastAPI 0.161.1 / SQLAlchemy 2.1.6、并发时序、BUG-01 的「5000→5504、卖 4 股」 | 逐条与代码/`requirements.lock.txt` 一致，不一致直接改 | ✅ 已复核（`44322b8`）：并发时序与 BUG-01 数字**一致未改**；修掉 3 处不一致——路由 7→**8** 个、前端版本 5.x/7.x→**TS 6.0 / Vite 8.2**（Vue 3.5）、用例 120→**137** 条 / 缺陷 10→**13** 条（含 3 个 P0）；`build_deck.py` 写死 ROOT 也一并修好并重导 `defense.pdf` |
| B-4 | （原 B-3 的重复条目） | — | 🔀 合并进 B-3 |
| **B-5** | 彩排中扮"提问老师"：从 `qa.md` 抽 5 问追问（并发 / CORS / 驱动 / 回滚 / 性能各 1） | 答不上来的 ≥3 条补进 `qa.md` | 🟡 **桌面演练版已备**：`docs/presentation/qa_drill.md` —— 5 条主问各往下追 2 层（共 15 问），每层都有应答要点与"答不上来的统一话术"；彩排时让别人照这份问、B 不备课直接答。**现场那一遍仍需在彩排里跑**（约 12–15 分钟，正好当问答段演练） |
| **B-6** | 答辩当天值守流程：谁盯 `/api/health`、异常时怎么 Redeploy | 写进 `demo-script.md` §0 的团队 checklist | ✅ 已写进 `demo-script.md` **§0.1 值守流程**（T−15/−10/−5 分钟各做什么、演示中盯 Network、故障只 Redeploy 不重建、三条铁律） |
| **B-7** | 补最后一项检查单：重新部署后数据仍在的截图 → `evidence/online/` + `deployment.md` §5 第 37 项打勾 + `test_report.md` §6 引用 | 检查单 **37/37** | ✅ 完成（`a99f396`）：6 张 before/after 图入 `evidence/online/`、对账记录 `persistence-redeploy.md`（`persistence_check.py --diff` 退出码 0）、`deployment.md` **37/37** 全勾、`test_report.md` §6 已加引用 |

**兜底**：线上 502/超时 → Render 手动 Redeploy（路径已演练，见 `deployment.md` §8.1）。

### 2.3 C 同学：定价页 + 现场案例

**边界**：只改 `slides.md` 06/07 页与 `docs/algorithm/pricing_model.md` §8。

| ID | 任务 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| **C-1** | 复核 06/07 页：α=0.15 / β=0 / floor=1.0 / clamp ±20% / `Z_FULL_SCALE=3`、100 seed 中位 −7.40%、回测三行（规则版 −3.52%/5.90%、随机 −0.59%/2.59%、买入持有 −10.78%/14.88%） | 与 `pricing_model.md` §7/§9 逐字一致 | ⬜ |
| **C-2** | "一涨一跌"两个现场可点案例：选手 + 轮次 + 两句口播，写进 `pricing_model.md` §8 | 现场 3 秒内定位到那条价格点 | ⬜ |
| **C-3** | 认领 `qa.md` Q4–Q8（定价 5 问）并脱稿 | 不看稿能答完 | ⬜ |
| C-4 | 线上价格抽查：`scripts/check_price_history.py` 再核一次 11 点 | 输出贴群 | ⬜ 可选 |

**兜底**：100 seed 讲不清 → 只说"中位 −7.40%、方向一致率 99.99%，完整表在 `pricing_model.md` §7.2"。

### 2.4 D 同学：主讲 + 控时 + 收尾

**边界**：`code/backend/ai/`（只修 bug）、`docs/`、`.github/`、`render.yaml`。

| ID | 任务 | 完成标准 | 状态 |
| --- | --- | --- | --- |
| D-1 | 导出 `docs/presentation/defense.pdf` | 与 `slides.md` 一致 | ✅ 13 页 / 539 KB，`build_deck.py` 可重生成 |
| D-2 | 文档收口：`user_manual` 线上地址 / `compliance` §4.1/§4.2 / `day5.md` 勾选 / `prototype_review` 索引 | 无空白、索引齐 | ✅ |
| D-3 | 回归 + CI：137 条 + 三 job 绿 + `test_report` 结论 | run #80 绿 | ✅ 本机 137 passed；CI run #80 success |
| D-4 | 合并后跑一次线上全链路（market→detail→buy→positions→trades） | 有截图或记录 | 🟡 未单独留证据，今天 A-8/A-7 覆盖一次即可 |
| **D-5** | 主讲 01 / 03 / 08 / 09 / 10 页 | 8:00 ±30s | ⬜ |
| **D-6** | 控时：演示 2:00 提示、问答 5:00 收口 | 全程 ≤15:00 | ⬜ |
| **D-7** | 组织两次彩排，问题记进 `docs/presentation/README.md` | 有两次记录与计时 | ⬜ |
| **D-8** | 认领 `qa.md` Q1–Q3（合规）、Q9–Q11（AI）、Q15–Q17（测试/局限）并脱稿 | 9 问脱口而出 | ⬜ |
| **D-9** | 3.3 的 `pulse-committers.csv` 入库（`Top committers` 弹窗 → Download CSV） | 文件在 `evidence/`，索引补一行 | ⬜ |
| **D-10** | 收尾：`test_report` 结论改「可交付」、`milestones.md` M6 与 T6-01~06 回填、`daily_summary.md` 第 6 天段 | 三处都改完 | ⬜ |

**待拍板**：`slides_additions.md` 的 01B/01C/01D 三页（使命口号 / 产品定义 / 设计原则）是否合进 `slides.md`。合则对稿时一起做、PDF 只重导一次；不合则三块内容只在问答里口头补。

---

## 3. 彩排计时表（打印，现场填）

| 段 | 内容 | 讲者 | 目标 | 彩排 1 | 彩排 2 |
| --- | --- | --- | ---: | ---: | ---: |
| ① | 00 封面 + 01 问题 | D | 0:50 | | |
| ② | 02 产品一览 + 03 取舍 | A | 1:05 | | |
| ③ | 04 架构 + 05 交易正确性 | B | 1:00 | | |
| ④ | 06 定价公式 + 07 诚实部分 | C | 1:00 | | |
| ⑤ | 08 AI + 09 工程实践 + 10 分工复盘 | D | 1:30 | | |
| ⑥ | 收尾 | D | 0:15 | | |
| ⑦ | **幻灯片小计** | — | **8:00** | | |
| ⑧ | 作品演示（`demo-script.md`） | A | 2:00 | | |
| ⑨ | 问答（预设 5 问） | 全员 | 5:00 | | |
| ⑩ | **合计** | — | **15:00** | | |

> 超时处置：幻灯片超 30s → 砍 09 页的 CI 细节；演示超时 → 跳过"故意失败"；问答超时 → D 用"文档里有，会后发您"收口。

## 4. 晚验收（M6 关闭条件，逐条打勾）

| # | 验收项 | 判定证据 | 责任人 |
| --- | --- | --- | --- |
| 1 | 功能冻结成立：当天无新功能提交 | `git log` 只有 docs/fix | D |
| 2 | 彩排 ≥2 次、每次 ≤15:00 | §3 两张计时表填满 | D |
| 3 | 幻灯片四件套齐：`slides.md` / `defense.pdf` / `demo-script.md` / `qa.md`（问答 ≥23 问） | 文件齐、PDF 与 md 同版 | D |
| 4 | 演示 2:00 内完成，含错误分支 | 彩排记录 | A |
| 5 | 线上 `/api/health` 200、8 选手、余额 5000.00 | 截图 | B |
| 6 | `deployment.md` §5 检查单 **37/37** | 全勾 | B |
| 7 | `test_report.md` 结论 =「可交付」；137 passed | 文档 + CI run #80 | D |
| 8 | 彩排记录写进 `docs/presentation/README.md` | 两次记录 | D |
| 9 | `daily_summary.md` 第 6 天段 | 有实质内容 | D |

**打勾规则**：第 2、4 项是今天的核心（材料早就齐了，缺的就是练）；第 5/6 项任一红 → 启用本地兜底并在开场说明；第 1 项破了（有人提功能）→ D 当场拦下。

## 5. 演示前 checklist（T−30 分钟）

- [ ] 线上预热过（`/api/health` 连续 200，冷启动约 49s）
- [ ] 市场页 8 选手、余额 5000.00、持仓/流水干净（脏了 `bootstrap_demo_data.py --reset`）
- [ ] 浏览器缩放 100%、关掉无关标签、投屏分辨率确认
- [ ] `defense.pdf` 与今天改过的 `slides.md` 是同一版
- [ ] `demo-script.md` 打印件（A）+ 计时器（D）
- [ ] 录屏兜底（2 分钟演示 + PDF）已存 U 盘与本地
- [ ] 本地环境可跑（`uvicorn app.main:app` + `vite preview`）
- [ ] 转接头 / 翻页笔 / 白板笔

## 6. 风险与砍单

| 风险 | 症状 | 处置 |
| --- | --- | --- |
| 免费实例冷启动 | 打开转圈 40–60s | 提前 15 分钟预热；开场先说"免费实例正在唤醒" |
| 现场断网 | 线上全挂 | 切本地（已练）；再不行播录屏 |
| 彩排发现数字对不上 | 稿子与代码不一致 | **以代码为准改稿**，改完重导 PDF |
| 有人临场缺席 | 某页没人讲 | 主责+备份：A↔D、B↔C（备份只保讲完，不改内容） |
| 评委问没准备的 | 卡壳 | 统一话术"这块在仓库 `docs/…` 有记录，会后补充给您" + 记下来 |
| 冻结期有人提功能 | 答辩前改动风险 | D 直接驳回，记 backlog |
| Postgres 2026-11-23 到期 | 答辩后两周数据消失 | 写进"已知限制"；需要长留换 Neon 只改 `DATABASE_URL` |

---

## 7. 待补的两份证据（可直接转发给 A / B）

> 背景：第 5 天收尾的**代码与文档都已完成**，只差两份「截图证据」。它们不影响作品能不能跑，但影响答辩时能不能拿出证据链。
> 两件都不需要本地环境，全部用**线上地址** + 浏览器 DevTools 完成。

> **关于 A 提的提交拆分（A5 → A6 → A4）**：这个拆分**已经在 `develop` 上了**，就是 A 自己的两个提交：
> `5a96a44 feat(frontend): AI 分析中占位态 + 折线图键盘无障碍（A5/A6）`（A5/A6 同文件、一次提交）、
> `9f10c52 feat(frontend): ≤720px 响应式——导航折叠、表格转卡片、375px 走查证据（A4）`（A4 单独、便于评审）。
> **不需要 revert 重提**——重做会多出 2 个 revert + 2 个 feat 提交，历史反而更长，且在冻结期动前端代码有回归风险。
>
> 残留一处小差异（不影响功能，冻结期不动）：`PlayerDetailView.vue` 用的是 `960px` 断点，
> `TradePanel / MarketView / PositionsView / TradesView` 用 `720px`，`App.vue` 走的是 `menu-toggle` 类切换。
> 375px 下三者都命中；被问就答"详情页信息密度不同，单独取了断点"。

### 7.1 给 A 的委派单：P0 三条的视觉证据（约 40 分钟）

**为什么要这个**：`day5.md` §3 的 P0 三条（响应式 / AI 思考中 / 键盘可达）是 D 代写的代码，CI 只能证明「能编译」，证明不了「真的生效」。所以需要 3 张真实浏览器截图，同时这也是 A 第一次亲眼确认这三条。

**准备**：先打开 `https://playerstock-frontend-mdlk.onrender.com` 让它预热（免费实例冷启动约 49 秒，别急着截图）。

| 步骤 | 具体操作 | 截图要点 |
| --- | --- | --- |
| **① 响应式** | 按 `F12` 打开 DevTools → 点左上「设备切换」图标（或 `Ctrl+Shift+M`）→ 顶部选 **iPhone SE / 375×667** → 依次打开 `/`、`/players/1`、`/positions` | 三张：市场页（导航折行 + 表格）、详情页（标题/价格上下排）、持仓页（表格可横向滚动）。**页面上不能出现横向滚动条** || **② AI「分析中」** | DevTools → `Network` 面板 → 限速选 **Fast 3G**（别用 Slow 3G，会直接超时）→ 硬刷新 `/players/1` → **立刻**截 AI 卡片位置 | 卡上显示「**AI 分析中…（行情与交易不受影响）**」。接口线上约 200ms，限速后有几秒窗口，够截 |
| **③ 键盘可达** | 关掉设备模式，在 `/players/1` 只按 `Tab`：焦点会依次走到导航 → 折线图数据点（有描边焦点框）→ 每点停一下会出 tooltip | 两张：① 焦点落在某个数据点上（能看到 `:focus-visible` 描边）；② tooltip 显示「时间 / 价格 / reason」。**全程不碰鼠标** |
| **④ A2/A3 线上走查 + 四张 F5（与上面一次做完）** | CORS 已于 2026-11-07 上午线上复验生效，**不用再等**。依次按 `F5` 刷新四条路由：`/market`、`/players/1`、`/positions`、`/trades` | 四张：每张的地址栏 + 页面内容都在，证明 SPA rewrite 与深链刷新不 404（TC-405） |

**「无横向滚动」怎么证明（比肉眼可靠）**：在 375px 状态打开控制台（`Esc` 或 `Console` 面板），粘贴这一行：

```js
document.documentElement.scrollWidth + ' / ' + window.innerWidth
```

两个数字都是 `375` 才算通过（`scrollWidth` 更大就是横向溢出，属于真 bug，要告诉 D）；把这一行输出一起截进图里。

**怎么进入其它路由（375px 下导航收进了「菜单」抽屉，不是没有页面）**：

| 目标页 | 进入方式 |
| --- | --- |
| `/players/1` 详情 | **点任意选手卡片**（卡片本身是链接），或地址栏直接把 `/` 改成 `/players/1` |
| `/positions` 持仓 | 点顶栏右上「**菜单**」→ 抽屉里选「持仓」（抽屉打开时点遮罩可关） |
| `/trades` 流水 | 同上，选「流水」 |
| `/market` | 地址栏直敲（会重定向到 `/`，验证 BUG-11 的修复） |

**红线**：不允许用原型页 `docs/software/prototype/index.html` 顶替——那会被一眼看穿，而且证明不了线上生效。

**落地**：

1. 图存进 `docs/acceptance/evidence/`：`23-responsive-375.png` / `24-ai-loading.png` / `25-keyboard-focus.png`，F5 四张用 `26-f5-market.png` / `27-f5-player.png` / `28-f5-positions.png` / `29-f5-trades.png`；
2. `docs/acceptance/evidence/README.md` 末尾「汇报证据」表下补 7 行（文件 / 内容 / 关键断言）；
3. `docs/mgmt/day5.md` §3.2 表格第 1/2/3 行的「验收方式」列换成截图链接；§2.1 的 A2/A3 两行由 🟡 改 ✅（写「2026-11-07 线上走查 + 4 张 F5」）；
4. 做完在群里说一句「P0 三条已亲验、四条路由刷新正常」，并在 day6.md A-9 打勾。

**坑**：设备模式下截图会带上手机边框，建议用 DevTools 的「Capture screenshot」而不是系统截图，尺寸干净。

### 7.2 给 B 的委派单：重新部署后数据仍在（约 25 分钟）

**为什么要这个**：这是 `deployment.md` **§9 TODO 的最后一项**，也是「线上用的是 Postgres 而不是临时 SQLite」最直接的一条人证。`/api/debug/db` 已经给了文本证据，缺的是「部署前后数据一致」的对照截图。

**红线：不要在彩排或演示前 30 分钟内做**——重新部署会让线上冷启动几十秒。

| 步骤 | 具体操作 | 记录什么 |
| --- | --- | --- |
| 1. 部署前快照 | 浏览器依次打开三个接口（**连地址栏一起截**）：`/api/account`、`/api/trades`、`/api/players/1/prices` | 余额、流水条数（应 3 条）、价格点数（应 11 点） |
| 2. 触发重新部署 | Render Dashboard → `playerstock-backend` → 右上 `Manual Deploy` → `Deploy latest commit` → 等状态变 **Live** | 截图部署状态（选填，但推荐） |
| 3. 部署后对账 | 同样三个接口再打开一次 | 三个数字与步骤 1 **逐项相同**；价格点末点仍等于 `current_price` |
| 4. 存证 | 四张图（前 3 + 后 3 可拼成两张对照） | 命名 `online-persistence-before.png` / `online-persistence-after.png` |

**合格标准**：两张图能看出「同一个地址、同一组数据、部署前后一致」；余额 5000.00、流水 3 条、价格 11 点。

**落地**（四处都要改，缺一不可）：

1. 图存 `docs/acceptance/evidence/online/`；
2. `docs/software/deployment.md` **§9 TODO 最后一项** `- [ ] D 第 6 天：把"重新部署后数据仍在"的截图存进 test_report.md` → 打勾并写成 `- [x] …（B 于 2026-11-07 完成，图见 evidence/online/online-persistence-*.png）`；
3. 同文档 **§5** 的「重新部署一次后端，然后刷新页面」那行补截图链接；
4. `docs/acceptance/test_report.md` **§6 线上验收结果**末尾加一行引用；`evidence/README.md` 索引补 2 行。

**坑**：

- **别顺手清库**：`bootstrap_demo_data.py --reset` 会重置数据，那就证明不了「数据还在」；
- 免费 Postgres 的数据存在数据库里，重新部署**不会**丢——如果真丢了，说明 `DATABASE_URL` 指到了临时盘，要立刻告诉 D；
- 部署期间线上短暂 50x 属正常，截图时避开那几十秒。

### 7.3 两张委派单的共同验收

| 检查 | 谁 |
| --- | --- |
| 6 张图都在 `docs/acceptance/evidence/`（3 张 P0 + 2~3 张持久化） | A / B |
| `evidence/README.md` 索引补齐（每条有「内容 + 关键断言」） | A / B |
| `day5.md` §3.2、`deployment.md` §9 与 §5、`test_report.md` §6 四处回填 | A / B |
| D 复核：图片能打开、断言与文内数字一致、链接不 404 | D |

### 7.4 可选：把 AI 从「规则兜底」切到真模型（B，约 10 分钟，冻结期可不做）

> 现状：`render.yaml` 里 `LLM_API_KEY` 是 `sync: false`（控制台手填），**从没填过** → 线上一直 `rule_fallback`。
> 这是**设计好的降级**，不是故障（`GET /api/analysis/1` 仍 200）。要不要切，看答辩需不需要展示真模型。

三个变量必须**一起**配，缺一个就回落到规则版（不会 5xx）：

| 变量 | 填什么 | 常见坑 |
| --- | --- | --- |
| `LLM_API_KEY` | 服务商给的 key（只在 Render 控制台填，`sync: false` 已保证不进仓库） | 别写进 `.env.example` 或文档 |
| `LLM_BASE_URL` | **完整 URL**，要带 `/chat/completions` | 只填 base 路径会 404 |
| `LLM_MODEL` | 该服务真实存在的模型名 | 默认 `gpt-4o-mini` 在第三方网关上通常不存在 |

**验证工具（B 已备）**：

```powershell
# ① 本地直接打模型（最快定位 key/URL/模型名哪个错）
$env:LLM_API_KEY="..."; python scripts/check_llm.py --direct
# ② 查线上最终走了哪条路（source = llm 还是 rule_fallback）
python scripts/check_llm.py --base https://playerstock-backend-mdlk.onrender.com
```

脚本会打印掩码后的环境变量、HTTP 状态与错误详情，并对 400 给出三种常见原因（URL 缺 `/chat/completions`、
模型名不存在、模型不支持 `temperature`）。**当前线上实测 `source = rule_fallback`**（未配 key），属预期。

> 安全：若 key 曾出现在聊天记录里，答辩结束后请到服务商后台吊销/轮换一次。

---

## 附录 A：第 1–5 天核对结论（2026-11-07）

**结论：五天工作无缺失项**；发现 6 处「文档状态没回填」，已当次修正（commit `8dc7c91`）。

| 天 | 交付 | 结论 |
| --- | --- | --- |
| 1 | 环境 + 5 表 + 12 接口契约四人签字 | ✅（第 4 项"前端显示连接成功"第 2 天闭环；Milestones M1–M6 已建、12 条 Issue 归入） |
| 2 | A 5 页面 / B 9 接口 / C 定价+模拟器 / D AI 原型 | ✅ 12/12 |
| 3 | 交易闭环 + 质量报告 51→44 + CI lint 门槛 | ✅ 7/7，浏览器证据 16 张 |
| 4 | 10 点折线图 + 每点 reason + AI 卡 + 三态 + 回测 | ✅ 7/7 |
| 5 | Render 三服务 + Postgres + TC-401~406 + CORS 复验 + 回滚演练 | ✅ 7/8（T5-08 材料齐、彩排未做 → 今天补） |

**修正的 6 处**：① C 第 1 天 7 项 `⬜`→✅（第 2 天吸收）；② T1-38「Milestones 未建」→ 已建；③ 第 4 天「BUG-03 待修」→ BUG-10 已修；④ 第 5 天「三件套未开始 / CORS 仍为 `*`」→ 材料齐、已白名单复验；⑤ `day5.md` 四处 ❌/🟡；⑥ 原 `day6_tasks.md`「120 条」→137 条、`deployment.md` 两项检查单。

**仍需人工确认的 2 项**：Kanban / Team Planning 看板（Projects v2 需登录，Milestones 已确认）；外部交叉原型测试（已记延期 + 补救方案，不追）。
