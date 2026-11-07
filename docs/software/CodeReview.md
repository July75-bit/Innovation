# 代码评审与软件质量（汇报 3.6 / 3.7）

> **负责人**：D 王泽棠 ｜ **对应汇报内容**：第一部分 **3.6 软件质量**（3.6.1 质量控制和保证方法、3.6.2 质量工具使用）与 **3.7 代码统计**；代码评审流程与记录一并收纳于此。
> **截图证据**：[`evidence/17-code-quality-scan.png`](../acceptance/evidence/17-code-quality-scan.png)（静态扫描+测试+CI 门禁）、[`evidence/18-quality-pylint-pep8.png`](../acceptance/evidence/18-quality-pylint-pep8.png)（Pylint 语义分析 + PEP8 + 格式化体检）、[`evidence/19-complexity-stats.png`](../acceptance/evidence/19-complexity-stats.png)（认知复杂度 + 代码统计）。截图由真实命令输出渲染生成（脚本可复跑）。
> **当前基线（2026-11-07）**：pytest **134 passed / 0 skipped** · 核心逻辑覆盖率 **91%** · CI **run #71 三 job 全绿** · 已修复缺陷 **13 条**（P0/P1 清零）。

---

## 1. 3.6.1 质量控制和保证方法

课程要求两条：**代码要加必要的日志**、**代码要加异常和错误处理**。逐条给证据：

### 1.1 日志（logging）

| 位置 | 日志 | 目的 |
| --- | --- | --- |
| `code/backend/ai/llm_agent.py:293` | `logger.warning("LLM 输出不可用，回落规则版：%s: %s", …)` | AI 降级**必须留痕**，答辩可查降级原因 |
| `code/backend/app/main.py`（启动期） | `logger.warning` ×3：Render 上误用 SQLite、`DATABASE_URL` 未配置回落本地、`CORS_ORIGINS` 显式含 `*` | 把"线上数据会丢/来源全放开"这类**运维风险在日志里喊出来**，而不是静默 |
| `code/backend/app/main.py` | `logger.info("CORS 放行来源：%s", …)` | 启动即可核对白名单是否生效 |
| `scripts/update_prices.py` / `bootstrap_demo_data.py` | 分步 `print` 进度（灌数 1/3、2/3、3/3） | 长流程可观测 |

### 1.2 异常与错误处理

| 机制 | 位置 | 说明 |
| --- | --- | --- |
| 统一错误体 | `app/core/errors.py` | 所有 4xx/5xx 返回 `{success:false, message(中文), code(机器码)}`；前端**不写映射表**直接展示 |
| 异常分级捕获 | `ai/llm_agent.py` | 只捕 `ImportError/ValueError`（配置）与 `OSError/ValueError`（网络/JSON），**禁止裸 except**；失败一律回落 `rule_fallback`，AI 故障不用 4xx/5xx |
| 事务回滚 | `app/core/price_update.py`、`app/api/trades.py` | 任一步失败整批 rollback；并发守卫用条件更新 + `rowcount` |
| 输入校验 | Pydantic schema + `TradePanel` 前端预校验 | 非法数量 422、余额不足 400、暂停交易 400，均有测试 |
| 降级链路 | `ai/fallback.py` | 无密钥/超时/脏输出 → 同结构 6 字段兜底 |

> 量化：`app/` + `ai/` 中 `except / raise ApiError` 相关语句 **28 处**，全部有对应用例（134 条中约 40 条是异常路径）。

---

## 2. 3.6.2 质量工具使用（截图见文末）

> 课程点名：p3c（Java，**本项目不适用**，我们用 Python/TS）、PEP8、Pylint 语义分析、代码复杂度插件。逐项对应如下。

### 2.1 PEP8 规范（对应 autopep8 / pycodestyle）

- 工具：**ruff 0.17.4**（Rust 实现，规则集兼容 pycodestyle E/W），配置在 `pyproject.toml`（`line-length = 100`）。
- 实测：`ruff check --select E,W` → **25 条，全部为 E501（行超长）**，无其它 E/W 违规；
- 偏差声明：PEP8 建议 79 列，本项目统一 **100 列**（团队决议，写进 `pyproject.toml`，CI 与编辑器同口径）。
- 格式化体检：`ruff format --check` → 39 个文件格式一致、31 个可重排；**格式化未设 CI 门禁**（避免一次性大 diff 淹没评审），仅作健康度记录。
- 截图：`evidence/18-quality-pylint-pep8.png` 第 2、3 段。

### 2.2 Pylint 语义分析（对应 VSCode Pylint 插件 / PyCharm 检查）

- 工具：**Pylint 4.1.3**（装在工作区独立目录，不污染项目依赖）。
- 范围：`code/core_engine` + `code/backend/app/core`（核心计算与事务层）。
- 结果：**9.74 / 10**；10 条消息全部为 R/W/C 级（重构建议与风格），**无 E（错误）/ F（致命）**；
- 典型 3 条及处置：`W0718 过宽 except`（定价读配置的兜底，保留并注释原因）、`C0415 函数内 import`（避免循环依赖的刻意设计）、`R0913 参数过多`（`update_price` 的可选参数用 keyword-only，保留）。
- 截图：`evidence/18-quality-pylint-pep8.png` 第 1 段。

### 2.3 代码复杂度（对应 complexipy / CodeMetrics 插件）

- 工具：**complexipy 8.3.0**（认知复杂度，与 VSCode 插件同内核）+ **ruff C901**（圈复杂度，CI 门禁）。
- 认知复杂度实测：48 个文件 / 149 个函数，**最大 27、平均 3.31**；>15 的 5 个**全部在 `scripts/`（CLI 装配）**；业务代码最高 15（`pricing._build_reason`，4 个分支拼 reason 文案）。
- 圈复杂度门禁（CI）：业务/测试 **≤10 全绿**；`scripts` **≤12 全绿**（`simulate_match.main` 曾为 11，已拆分到 4，见 `code_quality_report.md` §4.2）。
- 截图：`evidence/19-complexity-stats.png` 第 1 段。

### 2.4 其余质量工具（团队实际在用的完整清单）

| 工具 | 类别 | 配置 | 最近结果 |
| --- | --- | --- | --- |
| pytest | 单元+集成测试 | `pyproject.toml` | **134 passed / 0 skipped** |
| coverage.py | 覆盖率 | 命令行 `--source=app,core_engine` | **91%**（≥60% 达标） |
| ruff | lint + format | `pyproject.toml` + CI | CI 门槛全绿；D 负责文件 0 残留 |
| eslint + oxlint | 前端 lint | `code/frontend` | CI 绿 |
| vue-tsc | 前端类型检查 | `npm run build` 内含 | CI 绿 |
| vitest | 前端单测 | 3 个 spec（format / PriceChart / router） | 本地绿 |
| GitHub Actions | CI 门禁 | `.github/workflows/ci.yml` 三 job | run #71 全绿 |
| VS Code 扩展 | 编码即时反馈 | `.vscode/settings.json`（Pylance basic + Ruff 保存自动修） | 全员共用 |

---

## 3. 3.7 代码统计

| 语言 | 文件数 | 行数 |
| --- | ---: | ---: |
| Python（.py） | 70 | 8342 |
| Vue（.vue） | 10 | 1737 |
| TypeScript（.ts） | 12 | 852 |
| Markdown（.md，文档交付物） | 41 | 6489 |
| **合计** | **133** | **17420** |

- **模块数：17**（`code/backend/app`、`code/core_engine`、`code/backend/ai`、`code/frontend/src`、`scripts`、`tests` 及子包）。
- 统计口径与 VS Code Counter 一致（按语言聚合文件数/行数，排除 `node_modules`）。
- 截图：`evidence/19-complexity-stats.png` 第 2 段。

### 3.1 AI Vibe coding / 团队自写比例（估算，如实标注）

| 部分 | AI 参与度 | 说明 |
| --- | --- | --- |
| 前端首版（`9782dc7`） | **AI 生成初稿 → A 逐行复核修改** | A 的提交说明即"由 AI 全权出力打造初版"，后续 6 次提交为人工修正 |
| 交互原型 `prototype/index.html` | AI 生成草稿 → D 校验 18 项交互 | 仅评审用，不进构建 |
| 后端核心（交易/落库/AI） | **人工编写**，AI 仅辅助排错 | 每条逻辑有测试背书（134 条） |
| 文档 | AI 起草 → 各负责人补真实数据 | "只填真实跑出来的结果"是填表铁律 |

> 估算：**AI 首稿约占代码行数的 35–40%**（前端 + 原型），但**100% 的提交代码经负责人逐行阅读并本地运行验证**（见 `compliance.md` §3，已声明"不存在直接复制未理解代码"）。

---

## 4. 代码评审（流程与记录）

### 4.1 怎么审

- **模板**：[`docs/mgmt/code_review_template.md`](../mgmt/code_review_template.md)（改编自 ACMWDevHubPPT 的 CodeReviewTemplate）。
- **触发门槛**（三选一）：改动 >100 行；触碰交易事务/定价公式/AI 契约字段/表结构；修 P0/P1 缺陷。
- **交叉评审**：A↔B/D、B↔C/D、C↔B、D↔A/C，**不能自审**。
- **顺序**：机器先过（pytest / ruff / build 全绿）→ 人看设计、四类总体意见、语句级问题、项目专属 8 项 → 三态结论。
- **结论接 Kanban**：通过 → Done；存在问题 → 回 In progress + 登记 `BUG-xx`；需重写 → 写明原因。

### 4.2 已完成的评审记录

| 日期 | 被审提交 | 结论 | 关键发现 |
| --- | --- | --- | --- |
| 2026-11-07 | `4ca0e8e`（B：第 4 天文档收尾） | **通过评审** | 5 条事实断言全部可核验；1 条措辞问题（标题"逐项勾"实为 8 项已勾、23 项未勾） |

> 完整记录：[`docs/reviews/2026-11-07_docs-day4-B_4ca0e8e.md`](../reviews/2026-11-07_docs-day4-B_4ca0e8e.md)。
> 评审与测试的分工（答辩口径）：**测试守住回归，评审守住表达与设计**——那次评审抓到的正是测试永远抓不到的"文档断言与事实落差"。

---

## 5. 复跑命令（给评委/同学）

```powershell
cd D:\projects\innovation\Innovation
python -m pytest                                     # 134 passed
ruff check --select E4,E7,E9,F,C901 code/backend code/core_engine tests
ruff check --select E,W code/backend code/core_engine tests scripts   # PEP8：仅 25 条 E501
pylint code/core_engine code/backend/app/core        # 9.74/10
complexipy code/core_engine                          # 认知复杂度
coverage run --source=app,core_engine -m pytest && coverage report -m # 91%
cd code/frontend; npm ci; npm run build; npm run lint; npm run test:unit
```

CI 结果：<https://github.com/July75-bit/Innovation/actions>（run #71 三 job 绿）。
