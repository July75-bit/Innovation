# 答辩幻灯片

> **负责人**：全员（D 汇总） ｜ **截止**：第 6 天 ｜ **状态**：✅ 材料齐（`slides.md` 14 页讲稿 / `demo-script.md` / `qa.md` 20 问 / **`defense.pdf` 13 页已导出**）；待**全员彩排**
> **评分占比**：答辩评分表 —— 介绍幻灯片 **40%** + 功能演示 **40%** + 回答问题 **20%**

## 文件清单（已产出）

| 文件 | 内容 | 负责人 | 状态 |
| --- | --- | --- | --- |
| [`slides.md`](slides.md) | 8 分钟幻灯片源稿（Slidev markdown，14 页，含逐页讲稿与时间戳） | D 主笔 | ✅ |
| [`defense.pdf`](defense.pdf) | **可直接投屏的 PDF（13 页，1280×720 横版）** | D | ✅ |
| [`defense.html`](defense.html) | PDF 的源文件（自包含，浏览器打开即可放映） | D | ✅ |
| [`build_deck.py`](build_deck.py) | 重新生成 `defense.html` 的脚本（离线，无 Slidev 依赖） | D | ✅ |
| [`demo-script.md`](demo-script.md) | 2 分钟现场演示脚本（逐秒操作 + 话术 + 失败预案） | D / A 执行 | ✅ |
| [`qa.md`](qa.md) | 5 分钟问答（20 问，七类，含"救命句式"） | D 汇总 / 全员认领 | ✅ |
| [`pricing_slides.pptx`](pricing_slides.pptx) | 定价模块 **3 页素材**（公式推导 / 参数理由 / 100 seed 稳定性与下行风险），每页含口播备注，可直接拷进主稿；文字数据与 `docs/algorithm/pricing_model.md` §2/§3/§7/§8 一致 | C | ✅ |

**重新生成 PDF**（改了 `slides.md` 之后）：

```powershell
python docs/presentation/build_deck.py          # → defense.html
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  --headless=new --disable-gpu --no-pdf-header-footer --allow-file-access-from-files `
  --print-to-pdf="docs\presentation\defense.pdf" `
  "file:///D:/projects/innovation/Innovation/docs/presentation/defense.html"
```

> 当前 PDF 与 `slides.md` 内容一致（13 页 = 封面 + 10 个内容页 + 演示页 + 致谢页）。
> 若老师要求 Slidev 原生导出：`npx @slidev/cli slides.md --export defense.pdf`。

## 工具建议（课程推荐）

- **Slidev**：<https://cn.sli.dev/> —— Markdown 写幻灯片，适合代码/图表
- **Mermaid**：架构图、时序图直接嵌在幻灯片里
- 也可以用 PPT / 飞书文档，但**必须能导出 PDF 放仓库**

## 时间分配（老师要求：介绍 8 分钟 + 演示 2 分钟 + 问答 5 分钟）

| 环节 | 时长 | 内容 | 主讲 |
| --- | --- | --- | --- |
| 开场 | 30s | 项目名、一句话介绍、**合规声明** | D |
| 问题与需求 | 1.5min | 5W1H、痛点、目标用户、做了什么不做什么 | D |
| 系统架构 | 1.5min | 架构图、四层结构、技术选型与版本号 | B |
| 核心机制 | 2min | 交易规则、价格公式、可解释性归因 | C |
| 智能体 | 1.5min | Prompt 设计、输出契约、降级方案、回测结论 | D |
| 工程实践 | 1min | 测试、CI、部署、风险管理、复盘 | D |
| 演示 | 2min | 现场操作完整交易闭环 + AI 分析 | A |
| 分工与反思 | 30s | 四人贡献、踩过的坑、如果重做会怎么改 | 全员 |

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
2. 市场页 → "8 名虚拟选手，价格随比赛表现变化"
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

## 文件清单（旧版说明，已被顶部表格替代）

```
docs/presentation/
├── README.md              # 本文件
├── slides.md              # Slidev 源文件（14 页，已产出）
├── demo-script.md         # 2 分钟演示脚本（已产出）
├── qa.md                  # 20 问问答（已产出）
└── defense.pdf            # 导出 PDF（待导出）
```

## TODO

- [x] D 出 `slides.md` / `demo-script.md` / `qa.md` 初稿
- [x] D 导出 `defense.pdf`（13 页，与 `slides.md` 内容一致）
- [ ] B 补第 04/05 页的后端细节（架构版本号、并发时序），C 补第 06/07 页的定价与回测数字，A 补第 02 页与演示话术
- [ ] **排练 2 次**并计时（8+2+5 必须压进 15 分钟），记录写进本文件
- [ ] 答辩当天：确认线上服务醒着（预热 `/api/health`）、准备录屏兜底
