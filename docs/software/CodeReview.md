# 代码评审与质量工具使用（3.6 软件质量）

> **负责人**：D 王泽棠 ｜ **对应汇报内容**：3.6 软件质量 ——「质量工具使用」
> **配套文件**：模板 [`docs/mgmt/code_review_template.md`](../mgmt/code_review_template.md) ｜ 逐次记录 [`docs/reviews/`](../reviews/) ｜ 详细指标 [`docs/acceptance/code_quality_report.md`](../acceptance/code_quality_report.md)
> **当前基线（2026-11-07）**：pytest **134 passed / 0 skipped** · 核心逻辑覆盖率 **91%** · CI **run #71 三 job 全绿** · 已修复缺陷 **13 条**（P0/P1 清零）

> ⚠️ 说明：课程 Wiki 的 3.6 页面在本机网络下无法访问（`github.com/.../wiki` 连接被重置），
> 本文按「质量工具使用」的通用要求组织；若 3.6 有额外的必填项，把页面文字发我，我按原文补齐。

---

## 1. 我们用了哪些质量工具（一张表看完）

| # | 工具 | 类别 | 配置位置 | 怎么跑 | 最近一次结果 |
| --- | --- | --- | --- | --- | --- |
| 1 | **ruff** | 静态分析（lint） | `pyproject.toml` 的 `[tool.ruff]` + `[tool.ruff.lint]` | CI：`ruff check --select E4,E7,E9,F,C901 ...`；本地：`ruff check .` | CI 全绿；D 负责文件 **0 残留** |
| 2 | **pytest** | 单元 + 集成测试 | `pyproject.toml` 的 `[tool.pytest.ini_options]` | `python -m pytest` | **134 passed / 0 skipped**（21 个测试文件） |
| 3 | **coverage.py** | 覆盖率 | 命令行（`--source=app,core_engine`） | `coverage run -m pytest` → `coverage report -m` | 核心逻辑 **91%**（839 语句 / 79 未覆盖），课程要求 ≥60% |
| 4 | **eslint + oxlint** | 前端静态分析 | `code/frontend/eslint.config.ts` | `npm run lint`（CI 自动跑） | CI 全绿 |
| 5 | **vue-tsc** | 前端类型检查 | `package.json` 的 `type-check` 脚本 | `npm run build`（内含 `vue-tsc --build`） | CI 构建绿（21s） |
| 6 | **vitest** | 前端单测 | `vitest.config.ts` | `npm run test:unit` | 3 个 spec（`format` / `PriceChart` / `router`） |
| 7 | **GitHub Actions** | 持续集成 | `.github/workflows/ci.yml` | push 自动触发 | 3 个 job 全绿（run #71，`e9774de`） |
| 8 | **VS Code 扩展** | 编码即时反馈 | `.vscode/settings.json` + `extensions.json` | 保存即格式化/自动修 | Pylance `basic` + Ruff 0.17.4 |

### 1.1 CI 的三个 job（门禁在哪）

| job | 检查内容 | 不过的后果 |
| --- | --- | --- |
| 后端测试 | `pytest`（134 条）+ `ruff` 四条命令（业务/测试、scripts、复杂度） | 有测试挂或静态问题 → 红 |
| 前端检查 | ① grep 无写死本地地址 ② `npm ci` ③ `npm run lint` ④ `npm run build`（含类型检查） | 编译不过 → 红 |
| 交付物完整性 | 27 个课程要求文档是否存在 | 缺文档 → 红 |

### 1.2 ruff 门槛为什么分档（避免"为了过 CI 而改烂代码"）

| 范围 | 规则 | 复杂度阈值 | 理由 |
| --- | --- | --- | --- |
| `code/backend`、`code/core_engine` | `E4,E7,E9,F,C901` | 10 | 业务代码必须干净 |
| `tests` | 同上 | 10 | 测试代码同样要可维护 |
| `scripts` | `E4,E7,E9,F` + `C901` | **12** | CLI 入口的 argparse 装配天然分支多 |

> 编辑器侧：`.vscode/settings.json` 让保存时自动格式化 + 修可修问题，规则读 `pyproject.toml`，**和 CI 同口径**，避免"本地绿、CI 红"。

---

## 2. 代码评审怎么做（流程）

### 2.1 谁审谁（不能自审）

| 被审范围 | 评审人 |
| --- | --- |
| A 的 `code/frontend/` | B 或 D |
| B 的 `code/backend/app/`、`scripts/` | C 或 D |
| C 的 `code/core_engine/` | B |
| D 的 `code/backend/ai/`、`tests/`、CI | A 或 C |

### 2.2 什么时候必须走评审（三选一命中即走）

1. 改动 **> 100 行**；
2. 触碰 **交易事务 / 定价公式 / AI 契约字段 / 数据库表结构**；
3. 修的是 **P0 / P1 缺陷**。

其他小改动（文案、样式、注释）走"双人 quick check"。

### 2.3 评审顺序（机器先过，人只看机器看不出的）

```
作者自测 → pytest / ruff / npm run build 全绿
   ↓
填模板 §2「自动检查」（贴工具名与结果）
   ↓
评审人看 §3 设计 + §4 四类总体意见（风格/防御性/错误处理/结构）
   ↓
§5 语句级问题（文件:行 + 说明）+ §5.2 项目专属 8 项
   ↓
§6 结论：通过 / 存在问题（回 In progress + 登记 BUG-xx）/ 需重写
```

### 2.4 三态结论接 Kanban

| 结论 | 动作 |
| --- | --- |
| 通过评审 + 通过核验 | 卡片拖 `Done`，合并进 `develop` |
| 存在问题 | 卡片回 `In progress`，问题登记 `BUG-xx`（`test_report.md` §9 或 GitHub Issue），修完再核验 |
| 需重新编写 | 同上，且必须写明"为什么重写而不是修" |

---

## 3. 已完成的评审记录

| 日期 | 被审提交 | 范围 | 结论 | 关键发现 |
| --- | --- | --- | --- | --- |
| 2026-11-07 | `4ca0e8e`（B：第 4 天文档收尾） | 7 文件 / +56 −28，纯文档与配置 | **通过评审** | 5 条事实性断言全部可核验；1 条措辞问题：标题写"部署检查单**逐项**勾"，实际只勾 8 项、余 23 项 `[ ]` |

> 完整记录：[`docs/reviews/2026-11-07_docs-day4-B_4ca0e8e.md`](../reviews/2026-11-07_docs-day4-B_4ca0e8e.md)（含逐条对账命令与结果）

**那次评审值得保留的两个做法**

1. 改了接口 → **§3 接口清单 + §6 变更记录两处同时落**，并明确"前端不用适配"，避免了一次跨人返工；
2. 把踩过的坑（SQLAlchemy 2.1 默认 psycopg3）**写进 `.env.example` 注释并挂测试**，把口头经验变成可验证知识。

---

## 4. 质量改进闭环（有数字）

| 环节 | 数据 |
| --- | --- |
| 发现缺陷 | **13 条**（`test_report.md` §9），含 2 个 P0：并发超卖（余额 5000→5504）、部署驱动阻断 |
| 修复方式 | 每条都带**可复跑用例**（如 `test_trades_concurrency.py` 3 条守住并发、`test_config_db_url.py` 6 条守住驱动归一化） |
| 回归 | pytest 从 65 passed / 5 skipped → **134 passed / 0 skipped** |
| 覆盖率 | 核心逻辑 **91%**（要求 ≥60%） |
| 静态扫描 | D 负责文件 0 残留；全仓 72 项（50 项可 `--fix`）按归属移交 B/C |
| 门禁 | CI 三 job，push 即跑；ruff 分档避免"一刀切" |

### 4.1 与"只有测试没有评审"的区别（答辩口径）

- **测试**保证"已知行为不变"；
- **评审**发现"测试没想到的"——例如上面那次评审抓到的不是代码 bug，而是**文档断言与事实的落差**（"逐项勾"其实是 8 项），这类问题测试永远抓不到；
- 两者合起来才有闭环：**测试守住回归，评审守住表达与设计**。

---

## 5. 怎么复跑（给老师/同学）

```powershell
# 后端：测试 + 静态检查
cd D:\projects\innovation\Innovation
python -m pytest                                  # 期望 134 passed
ruff check --select E4,E7,E9,F,C901 code/backend code/core_engine
ruff check --select E4,E7,E9,F,C901 tests
ruff check --select E4,E7,E9,F scripts
ruff check --select C901 --config "lint.mccabe.max-complexity = 12" scripts

# 覆盖率（需 pip install coverage）
coverage run --source=app,core_engine -m pytest
coverage report -m                                # 期望 TOTAL 91%

# 前端：类型检查 + 构建 + 规范
cd code/frontend
npm ci && npm run build && npm run lint && npm run test:unit
```

CI 结果：<https://github.com/July75-bit/Innovation/actions>（最近一次 run #71 三 job 绿）
