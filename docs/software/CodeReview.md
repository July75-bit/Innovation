# 代码评审与软件质量（汇报 3.6 / 3.7）

> **负责人**：D 王泽棠 ｜ **对应汇报内容**：第一部分 **3.6 软件质量**（3.6.1 质量控制和保证方法、3.6.2 质量工具使用）与 **3.7 代码统计**；代码评审流程与记录一并收纳于此。
> **截图证据**：[`evidence/17-code-quality-scan.png`](../acceptance/evidence/17-code-quality-scan.png)（静态扫描+测试+CI 门禁）、[`evidence/18-quality-pylint-pep8.png`](../acceptance/evidence/18-quality-pylint-pep8.png)（Pylint 语义分析 + PEP8 + 格式化体检）、[`evidence/19-complexity-stats.png`](../acceptance/evidence/19-complexity-stats.png)（认知复杂度 + 代码统计）。截图由真实命令输出渲染生成（脚本可复跑）。
> **当前基线（2026-11-07 17:00 复测）**：pytest **176 passed / 0 skipped** · 核心逻辑覆盖率 **98%**（956 语句 / 17 未覆盖）· CI **run #95 三 job 全绿** · 已修复缺陷 **14 条**（P0/P1 清零）。

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

**一条真实降级日志长什么样**（2026-11-07 本机实跑：注入一个超时的假 client，不触网）：

```
WARNING ai.llm_agent LLM 输出不可用，回落规则版：TimeoutError: model did not respond in 20s
→ 接口返回 200，source=rule_fallback，action=HOLD
```

这一行同时证明三件事：① 异常被**分级捕获**而不是裸 except；② 降级**留痕**，线上能查到为什么没用上模型；③ 故障**没有升级成 5xx**，交易与行情完全不受影响。复跑方式见 §5 最后一条。

> 量化：`app/` + `ai/` 中 `except / raise ApiError` 相关语句 **28 处**，全部有对应用例（176 条中约 50 条是异常/边界路径）。

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
| pytest | 单元+集成测试 | `pyproject.toml` | **176 passed / 0 skipped**（CI run #95；截图 17 摄于 134 条的时点，此后补到 176 条） |
| coverage.py | 覆盖率 | 命令行 `--source=app,core_engine` | **98%**（956/17，≥60% 达标） |
| ruff | lint + format | `pyproject.toml` + CI | CI 门槛全绿；D 负责文件 0 残留 |
| eslint + oxlint | 前端 lint | `code/frontend` | CI 绿 |
| vue-tsc | 前端类型检查 | `npm run build` 内含 | CI 绿 |
| vitest | 前端单测 | 3 个 spec（format / PriceChart / router） | 本地绿 |
| GitHub Actions | CI 门禁 | `.github/workflows/ci.yml` 三 job | run #95 全绿；**交付物 job 现校验 45 项必需文件（非空）+ 证据图 ≥20 张 + 仓库卫生（误提交拦截）** |
| VS Code 扩展 | 编码即时反馈 | `.vscode/settings.json`（Pylance basic + Ruff 保存自动修） | 全员共用 |

---

## 3. 3.7 代码统计

> 统计口径：`git ls-files` 跟踪的文件（排除 `node_modules/`、`package-lock.json`、构建产物），按语言聚合文件数与行数；与 VS Code Counter 的"按语言统计"一致。复跑脚本见 §5。

| 类别 | 语言 | 文件数 | 行数 |
| --- | --- | ---: | ---: |
| **代码** | Python（后端 + 引擎 + 脚本 + 测试） | 78 | 9917 |
| | Vue（单文件组件） | 13 | 3486 |
| | TypeScript（api / router / composables / 测试） | 19 | 1641 |
| | CSS | 1 | 108 |
| | HTML（原型 591 + 入口 13） | 2 | 604 |
| **文档** | Markdown（README + 51 份 docs 交付文档） | 51 | 8027 |
| **配置与数据** | JSON（种子数据、package、tsconfig 等） | 12 | 729 |
| | YAML（CI、render 蓝图） | 2 | 252 |
| | **合计（全部跟踪文件）** | **178** | **24764** |

- **代码行小计（Python + Vue + TS + CSS + HTML）= 15756 行**；文档与配置单列，不计入代码。
- **模块数：18** —— 后端 Python 包 7（`ai`、`app`、`app/api`、`app/core`、`app/models`、`app/schemas`、`core_engine`）+ `scripts` + 测试 2（`tests/unit`、`tests/integration`）+ 前端 `src` 目录 8（`api`/`assets`/`components`/`composables`/`mock`/`router`/`utils`/`views`）。
- 相比第 5 天的统计（133 文件 / 17420 行），增长主要来自 A 的登录注册页（`AuthView.vue` 737 行、`useAuth.ts` 315 行及其单测）与 D 的汇报材料。
- 截图：`evidence/19-complexity-stats.png` 第 2 段（该图摄于第 5 天，行数为当时快照）。

### 3.1 AI Vibe coding / 团队自写比例（估算，如实标注）

**算法**（人人可复核）：把"由 AI 起草的代码"除以"代码总行"，分子只算前端与原型，分母不含文档与配置。

| 部分 | 行数 | AI 参与度 |
| --- | ---: | --- |
| 前端 Vue + TS + CSS | 5235 | **AI 出初稿**，A 逐行复核并做 6 次人工修正 |
| 交互原型 `docs/software/prototype/index.html` | 591 | **AI 草稿**，D 校验 18 项交互后定稿 |
| 后端 + 定价引擎 + 脚本 + 测试（Python） | 9917 | **人工编写**，AI 仅辅助排错与补测试 |
| **合计（代码行）** | **15756** | — |

> **结论：AI 首稿约 5826 行 / 15756 行 ≈ 37%**；其余 63% 人工编写。
> **但 100% 的提交代码经负责人逐行阅读、本地运行验证并配测试背书**（见 `compliance.md` §3 的声明："不存在直接复制未理解代码"）。
> 比例本身不是评分点，"**用了 AI 但每一行都过手**"才是——这也是我们能在被追问时现场改代码、讲清每处设计的前提。

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
# 先确认用「项目环境」而非 conda base（否则报 No module named pytest）
conda activate playerstock      # 或 & "D:\miniconda\envs\playerstock\python.exe"
python -m pytest                                     # 176 passed
ruff check --select E4,E7,E9,F,C901 code/backend code/core_engine tests
ruff check --select E,W code/backend code/core_engine tests scripts   # PEP8：仅 25 条 E501
pylint code/core_engine code/backend/app/core        # 9.74/10
complexipy code/core_engine                          # 认知复杂度
coverage run --source=app,core_engine -m pytest && coverage report -m # 98%
cd code/frontend; npm ci; npm run build; npm run lint; npm run test:unit

# 代码统计（§3 那张表就是它跑出来的）
git ls-files | Select-String -Pattern '\.py$|\.vue$|\.ts$|\.md$|\.css$|\.html$|\.json$|\.ya?ml$'

# 真实降级日志（§1.1 那条 WARNING，注入超时假 client，不触网）
python -c "import logging; logging.basicConfig(level=logging.INFO); from ai.llm_agent import analyze; analyze({'player_id':1,'name':'ZywOo','current_price':126.0,'change_pct':5.0,'rating':88,'recent_prices':[{'price':120.0},{'price':126.0}],'position':{'quantity':10,'avg_cost':120.0}}, chat=lambda p: (_ for _ in ()).throw(TimeoutError('model did not respond in 20s')))"
```

CI 结果：<https://github.com/July75-bit/Innovation/actions>（最新 run #95 三 job 绿）。
