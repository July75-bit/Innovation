# 答辩幻灯片

> **负责人**：全员（D 汇总） ｜ **截止**：第 6 天 ｜ **状态**：✅ 材料齐（Slidev 答辩稿已迁到 [docs/slides](../slides/)，17 页、Mermaid 架构/ER 图、逐页讲稿，GitHub Actions 自动构建 PDF；本目录保留演示脚本/问答/彩排手册与旧版 PDF）；待**全员彩排**
> **评分占比**：答辩评分表 —— 介绍幻灯片 **40%** + 功能演示 **40%** + 回答问题 **20%**

## 文件清单（已产出）

| 文件 | 内容 | 负责人 | 状态 |
| --- | --- | --- | --- |
| [`../slides/`](../slides/) | **Slidev 答辩稿（17 页源稿 slides.md + style.css + assets + package.json）**；GitHub Actions 自动构建 PDF/静态站 | D | ✅ |
| [`defense.pdf`](defense.pdf) | 旧版 PDF（16 页，上一版 HTML 流程产物；新版请用 Slidev 导出） | D | 历史 |
| [`defense.html`](defense.html) | 旧版 HTML 源文件（历史；本次答辩主材料为 Slidev） | D | 历史 |
| [`build_deck.py`](build_deck.py) | 旧版 `defense.html` 的生成脚本（历史） | D | 历史 |
| [`demo-script.md`](demo-script.md) | 2 分钟现场演示脚本（逐秒操作 + 话术 + 失败预案） | D / A 执行 | ✅ |
| [`qa.md`](qa.md) | 5 分钟问答（20 问，七类，含"救命句式"） | D 汇总 / 全员认领 | ✅ |
| [`pricing_slides.pptx`](pricing_slides.pptx) | 定价模块 **3 页素材**（公式推导 / 参数理由 / 100 seed 稳定性与下行风险），每页含口播备注，可直接拷进主稿；文字数据与 `docs/algorithm/pricing_model.md` §2/§3/§7/§8 一致 | C | ✅ |

**放映 / 导出**：Slidev 源稿与构建说明见 [../slides/README.md](../slides/README.md)；本机放映需要 Node.js 22.22+，或直接用 GitHub Actions 的 artifact。

> 课程允许直接用 Slidev 写幻灯片、用 Mermaid 画图；本稿架构图与 ER 图都是 Mermaid 代码块，改数据直接改 markdown。
> 旧的 defense.pdf / defense.html 是上一版 HTML 流程产物，不作为本次答辩主材料。

## GitHub Actions 自动构建 + 在线发布（推荐）

推送 [docs/slides](../slides/) 的改动会自动触发 [.github/workflows/slides.yml](../../.github/workflows/slides.yml)，
构建后发布到 GitHub Pages：**幻灯片在线看 <https://july75-bit.github.io/Innovation/>**，
**PDF 直接查看/下载 <https://july75-bit.github.io/Innovation/playerstock_defense.pdf>**。

流水线：
npm ci → Playwright Chromium → slidev build → slidev export → 上传 artifact **playerstock-defense-slides**（保留 30 天）。

**下载**：GitHub 仓库 → Actions → 左侧「答辩幻灯片 (Slidev)」→ 最近一次绿色 run → 底部 Artifacts → 下载后解压，得到 17 页 PDF 与可离线放映的静态站。
也可在 Actions 页面点 **Run workflow** 手动触发。

## 工具建议（课程推荐）

- **Slidev**：<https://cn.sli.dev/> —— Markdown 写幻灯片，适合代码/图表
- **Mermaid**：架构图、时序图直接嵌在幻灯片里
- 也可以用 PPT / 飞书文档，但**必须能导出 PDF 放仓库**

## 时间分配（老师要求：介绍 8 分钟 + 演示 2 分钟 + 问答 5 分钟）

| 页 | 内容 | 目标时长 |
| --- | --- | --- |
| 1–2 | 封面、使命 / 口号 / 目标用户 / 差异化 | 55s |
| 3–4 | 产品定义、用户故事、设计原则 | 75s |
| 5–7 | UX 界面、技术选型、仓库与协作 | 90s |
| 8–10 | 生命周期复盘、系统架构、定价与 AI | 115s |
| 11–13 | 数据库、接口、软件质量 | 75s |
| 14–15 | 代码统计、用户测试与容量 | 35s |
| 16–17 | 演示衔接 + Q&A 提示 | 10s |

合计约 7′30″，留 30 秒缓冲；2 分钟演示与 5 分钟问答单独计时（演示脚本见 demo-script.md，分工反思走 Q&A）。

## 必答的 8 个内容点（对应课程 22 条指标）

- [ ] 1. 设计思维：用户、痛点、场景（指标 #1–#4）
- [ ] 2. 需求：功能/非功能需求可测量（指标 #2、#7）
- [ ] 3. 架构图 + 技术栈**含版本号**（指标 #7、#9）
- [ ] 4. 定价算法：公式、参数含义、**一条价格变化的完整拆解**（指标 #3、#11）
- [ ] 5. AI：Prompt 设计、JSON 契约、**不可用时的降级演示**（指标 #12、#13）
- [ ] 6. 测试：用例数、通过率、边界测试证据（指标 #10、#9）
- [ ] 7. 部署：线上地址、数据持久化验证（指标 #7）
- [ ] 8. 项目管理：WBS、风险应对、复盘（指标 #15–#18）

## 图表清单（提前画好，别现场画）

| 图 | 来源文件 |
| --- | --- |
| 系统架构图 | `docs/software/architecture.md` 第 1 节 |
| 交易时序图 | `docs/software/architecture.md` 第 3.1 节 |
| 价格更新状态机 | `docs/requirements/mechanism_design.md` 第 2 节 |
| AI 降级流程图 | `docs/algorithm/ai_agent_prompt.md` 第 5 节 |
| ER 图 | `docs/software/database_design.md` 第 1 节 |
| 回测对比表 | `docs/algorithm/backtest_report.md` 第 4 节 |

## 演示环节脚本（2 分钟，必须排练 ≥2 次）

1. 打开线上地址（**提前确认服务是醒的**，Render 免费实例会休眠）
2. 市场页 → "16 名虚拟选手、8 支战队各 2 人，价格随比赛表现变化"
3. 进详情页 → 指折线图 → 拆解一次涨跌原因
4. 买入 2 股 → 余额/持仓/流水三处同时变化
5. 点 AI 分析 → 展示 BUY + 理由 + 风险等级
6. （彩蛋）清空密钥再点一次 → 规则版兜底，"AI 挂了也能交易"
7. 持仓页 → 展示浮动盈亏

## 演示失败预案

| 故障 | 应对 |
| --- | --- |
| 线上服务休眠/超时 | 提前 10 分钟访问唤醒；备用本地环境 |
| 网络断了 | 本地录屏视频兜底 |
| AI 超时 | 直接说"演示降级路径"，反而加分 |
| 数据被清空 | 现场重新 seed（固定数据 10 秒重建） |
| 时间不够 | 砍掉持仓页和彩蛋，保交易闭环 + AI |

## TODO

- [x] D 出 Slidev 源稿（docs/slides/slides.md）/ demo-script.md / qa.md 初稿
- [x] Slidev 稿经 GitHub Actions 导出 17 页 PDF（旧 defense.pdf 仅历史）
- [x] B 补第 04/05 页的后端细节（架构版本号、并发时序）
- [x] C 补第 06/07 页的定价与回测数字（中位数 −7.40% / 均值 −6.46%、α=0.15·0.08·0.05 对比、3σ 满格说明；数据源 `pricing_model.md` §7.2；另有 3 页素材 `pricing_slides.pptx`）
- [ ] C 把第 06 页的**案例 reason 换成线上实际口径**（`（本轮得分 76.6，S=-1.00）`），并改用页面可复现的第 9 轮那一对（ZywOo 81.3 → −13.88%、flameZ 79.9 → +15.00%）
- [ ] A 补第 02 页与演示话术
- [ ] **排练 2 次**并计时（8+2+5 必须压进 15 分钟），记录写进本文件
- [ ] 答辩当天：确认线上服务醒着（预热 `/api/health`）、准备录屏兜底
