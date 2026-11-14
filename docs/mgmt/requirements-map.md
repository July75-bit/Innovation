# 课程要求 → 仓库落点对照表（答辩自查用）

> **用途**：课程手册与汇报要求里点名的每一项，在这里都能查到「写在哪、证据是什么、谁负责」。
> 对照来源：`ACMWDevHubPPT`《创新工程实践营项目汇报内容》（汇报 15 分钟）、SWIEP.pdf 六天任务、作业一/二/三。
> **状态**：✅ 已具备（有产物 + 可验证）｜🟡 有但不完整｜❌ 缺
> 最后核对：2026-11-07 22:20（本机后端 265 passed / 前端 51 passed / 覆盖率 96%）

## 一、汇报第一部分：产品设计（8 分钟 / 40%）

### 1.1 使命、口号和策略

| 要求 | 落点 | 证据 | 状态 |
| --- | --- | --- | --- |
| 1.1.1 使命 | `slides.md` 01B | 一句话使命 + 三条可验证原则 | ✅ |
| 1.1.2 口号 | `slides.md` 01B | 「看懂比赛，从持有起」+ 与博彩切割 | ✅ |
| 1.1.3 目标用户 | `slides.md` 01B、`problem_definition.md` | 三类用户 + 排除线（未成年人/想赚钱/真钱竞猜） | ✅ |
| 1.1.4 如何获得用户 | `slides.md` 01B（2026-11-07 补） | 赛事节点 / 内容社群 / 自带传播三件事 | ✅ |
| 1.1.5 团队优势 | `slides.md` 01B（2026-11-07 补） | 四人分工表 + 各自不可替代点 | ✅ |
| 1.1.6 差异化（表格） | `slides.md` 01B | 4 维对比表（标的 / 价格形成 / 可解释 / 资金风险） | ✅ |

### 1.2 产品定义

| 要求 | 落点 | 证据 | 状态 |
| --- | --- | --- | --- |
| 产品定义模板段 | `slides.md` 01C | 「对于…他们…不同于…」完整六句 | ✅ |
| 1.2.1 解决的问题 | `slides.md` 01、`problem_definition.md` | 5W1H + 痛点映射 | ✅ |
| 1.2.2 用户故事式价值 | `slides.md` 01C、`user_stories.md` | 7 条 INVEST + Given-When-Then | ✅ |
| 1.2.3 解决方案形态 | `slides.md` 01C | Web 应用 + 规模与边界 | ✅ |

### 2 产品设计应用的原则

| 要求 | 落点 | 证据 | 状态 |
| --- | --- | --- | --- |
| 五组设计原则 | `slides.md` 01D | 每条原则 → 一个真实决定 → 可核查落点 | ✅ |

## 二、汇报第一部分：产品实现（3.1–3.7）

| 要求 | 落点 | 证据 | 状态 |
| --- | --- | --- | --- |
| **3.1 用户体验设计考虑的因素** | `prototype_review.md` §1.5（2026-11-07 补） | 9 类因素 × 取舍 × 落点 | ✅ |
| **账号体系（第 7 轮新增）** | `api_contract.md` §3 #13–17、§4.11–4.15；`user_manual.md` §2.5；`compliance.md` §4.3 | 注册/登录/me/退出/删号 5 个接口；PBKDF2-HMAC-SHA256 加盐 10 万次、令牌 30 天可撤销；`test_api_auth.py` + `test_auth_multiuser.py` | ✅ |
| **3.2 语言/IDE/框架 + 版本号，写在 README** | `README.md` 技术栈表、`architecture.md` §4 | Vue 3.5.42 / TS 6.0 / Vite 8.2.2 / FastAPI 0.161.1 / SQLAlchemy 2.1.6 | ✅ |
| **3.3 仓库链接 + 每人提交次数截图** | `evidence/20~22`、`pulse-committers.csv` | pulse 截图 + 准数统计（49/41/28/21）+ 口径说明 | ✅ |
| **3.4 生命周期问题汇总表** | `acceptance/lifecycle_issues.md` | 16 条 × 四列（类别/问题/原因/解决），每条带用例 | ✅ |
| **3.5.0 画图工具** | `architecture.md` §3.4（2026-11-07 补） | Mermaid + 6 张图的类型与位置 + 不用 Visio 的理由 | ✅ |
| 3.5.1 系统架构图 | `architecture.md` §1 | flowchart 分层图 | ✅ |
| 3.5.2 基础设施图 | `architecture.md` §6、`deployment.md` §6 | Render 三服务拓扑 | ✅ |
| **3.5.3 AI/算法说明 + 文献** | `ai_agent_prompt.md` §7.5（2026-11-07 补）、`pricing_model.md` | 模型选择理由、接口规范链接、定价公式来源 | ✅ |
| 3.5.4 数据库设计（ER 图） | `database_design.md` §2 | erDiagram 5 张表 + 字段口径 | ✅ |
| 3.5.5 接口设计（表格） | `api_contract.md` §3/§4 | 12 个接口清单 + 逐接口输入输出与错误码 | ✅ |
| **3.5.6 前端设计** | `architecture.md` §3.5（2026-11-07 补） | 框架/路由/状态/图表/样式/响应式/无障碍 8 项决策 | ✅ |
| **3.6 软件质量（3.6.1 + 3.6.2）** | `software/CodeReview.md` §1/§2 | 日志 15 处 + 异常五层 + PEP8/Pylint/复杂度 + 3 张截图 | ✅ |
| **3.7 代码统计（AI 比例/模块数/行数）** | `CodeReview.md` §3 | 178 文件 24764 行、模块 18、AI 首稿 37%（可复算） | ✅ |

## 二·补 第 4 天「测试作品」检查点（新版 SWIEP.pdf p.176–201）

| 要求 | 落点 | 状态 |
| --- | --- | --- |
| 单元测试核心逻辑（pytest） | `tests/unit` 24 个文件 | ✅ |
| 等价类 + 边界值为至少一个输入字段设计用例 | `test_plan.md` §4.0（TC-001~012）+ §7 方法对照 | ✅ |
| 场景法为一条关键业务流程写 E2E | `tests/integration/test_e2e_flow.py` | ✅ |
| 覆盖率 ≥60% | `test_report.md` §2.3 → 97% | ✅ |
| **≥10 个测试用例文档（七列模板：编号/名称/前置条件/步骤/输入/预期/优先级）** | `test_plan.md` **§4.0**（2026-11-14 补，12 条） | ✅ |
| 测试代码与文档提交到 `tests/` | `tests/unit` + `tests/integration` | ✅ |
| **缺陷修复使用 GitHub Issues / BugTracker Project** | **BUG-01~14 已逐条建成 Issue #22–#35 并全部关闭**（`bug` + `P0/P1/P2` 标签齐全） | ✅ 已完成（2026-11-14 核实） |
| **智能体测试分层（L1–L5）+ 五原则 + CI 门禁** | `acceptance/agent_test_layers.md` | ✅ L1–L5 齐（L4 黄金集 20 例、L5 红队 11 条） |
| **L4 评测（真模型 + 黄金集）** | `acceptance/agent_eval_report.md`、`tests/eval/` | ✅ 线上 16/16 走真模型、契约 100%、理由含数字 100%、P95 3.4s |
| **L5 红队（注入/越权/隐私/输出越界）** | `acceptance/agent_redteam.md`、`tests/eval/test_agent_redteam.py` | ✅ 11/11 通过；无自由输入 → 注入面为 0 |
| **33 项用户测试检查表（P1–P5 / I1–I4 / V1–V4 / H1–H9 / A1–A11）** | `tests/playerstock_agent_demo_user_test.md`（**正式提交版**，学生版表格逐格填满）、`tests/agent_demo_user_test.md`（内部自查版） | ✅ **32 通过 / 1 部分通过 / 0 不通过**（首轮 5 项部分通过已修复 4 项） |
| 第 4 天第 3 部分：小组交叉用户测试 | `cross_test.md` §4（延期说明 + 补救方案） | ❌ 未做（已如实记录） |
| 第 3 天检查点：提交 `docs/software/code_quality.md` / `code_review.md` | 两个文件均已按课件路径建好 | ✅ |

> 📄 **已备好可直接粘贴的 Issue 标题 + 正文**：[`bug-issues.md`](bug-issues.md)（14 条，含两种建法）。
> 🟡 **Issues 说明**：仓库现有 Issue 以「day1 / day3 / check frontend」等任务类为主，
> 14 条缺陷（BUG-01~14）记录在 `test_report.md` §9。若要把缺陷也纳进 BugTracker，需要逐条建 Issue（见交付说明）。

## 三、交付物与工程证据

| 要求 | 落点 | 状态 |
| --- | --- | --- |
| 可运行作品 + 公网地址 | Render 三服务（`deployment.md` §6） | ✅ |
| 测试用例文档 + 测试代码（`tests/`） | `test_plan.md`、`test_report.md`、`tests/` 26 文件 | ✅ 264 passed |
| 覆盖率 ≥60% | `test_report.md` §2.3 | ✅ 97% |
| 代码评审（模板 + 记录） | `code_review_template.md`、`docs/reviews/` 1 份 | 🟡 仅 1 份记录 |
| CI 可复现 | `.github/workflows/ci.yml` 三 job | ✅ |
| 合规声明 / 用户手册 / 部署说明 | `compliance.md`、`user_manual.md`、`deployment.md` | ✅ |
| 团队协作痕迹（Projects/Milestones/Issues） | 三个 Project + M1–M6 + **缺陷 Issue #22–#35、#37（15 条，bug/P0-P2 标签，含修复证据，已关闭）** | ✅（需评委登录可见或看截图） |

## 四、明确不做 / 已知限制（诚实清单）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 真实赛事数据接口 | 不做 | HLTV 反爬；用模拟数据 + 适配器预留 |
| 充值 / 提现 / 兑换 | 不做 | 合规红线 |
| 外部交叉原型测试 | 延期 | 已写延期说明 + 补救方案（`cross_test.md` §4），不伪造记录 |
| 依赖漏洞扫描（pip-audit） | 未接 | 冻结期不加门禁，列入下一步 |
| 回测重跑（16 人种子） | 未重跑 | `pricing_model.md` §7 已加注：结论说明机制特性，非绝对收益 |
| 彩排 | **0 次** | 唯一硬缺口，方案见 `rehearsal-plan.md` |

## 五、答辩前最后 3 件事

1. **彩排两遍**（`rehearsal-plan.md`，8+2+5=15:00）；
2. **演示前重置数据**（`bootstrap_demo_data.py --reset`，余额回 5000）；
3. **确认线上 `source=llm`**（真模型，中位 2.5s）与 16 名选手都在。
