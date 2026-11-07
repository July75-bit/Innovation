# 代码评审与软件质量（汇报 3.6 / 3.7）

> **负责人**：D 王泽棠 ｜ **对应汇报内容**：第一部分 **3.6 软件质量**（3.6.1 质量控制和保证方法、3.6.2 质量工具使用）与 **3.7 代码统计**；代码评审流程与记录一并收纳于此。
> **截图证据**：[`evidence/17-code-quality-scan.png`](../acceptance/evidence/17-code-quality-scan.png)（静态扫描+测试+CI 门禁）、[`evidence/18-quality-pylint-pep8.png`](../acceptance/evidence/18-quality-pylint-pep8.png)（Pylint 语义分析 + PEP8 + 格式化体检）、[`evidence/19-complexity-stats.png`](../acceptance/evidence/19-complexity-stats.png)（认知复杂度 + 代码统计）。截图由真实命令输出渲染生成（脚本可复跑）。
> **当前基线（2026-11-07 17:00 复测）**：pytest **216 passed / 0 skipped** · 核心逻辑覆盖率 **97%**（1289 语句 / 43 未覆盖）· CI **run #104 三 job 全绿** · 已修复缺陷 **14 条**（P0/P1 清零）。

---

## 1. 3.6.1 质量控制和保证方法

课程要求两条：**代码要加必要的日志**、**代码要加异常和错误处理**。下面不是原则，是逐处清单（数字均可用 §5 的命令复核）。

### 1.1 日志（logging）

**日志器：6 个模块级命名空间**（`playerstock`、`playerstock.errors`、`playerstock.trades`、`ai.llm_agent`、`ai.context`、`app.api.ai`），统一走标准库 `logging`，由部署平台（Render）收集 stdout。

**全部 15 处日志调用（下表按场景合并）**：

| 级别 | 位置 | 打什么 | 为什么必须打 |
| --- | --- | --- | --- |
| info | `app/main.py:78` | 启动即输出**当前用哪个库**（SQLite / Postgres） | "线上数据为什么总丢"的第一现场 |
| info | `app/main.py:82` | 启动输出**CORS 实际放行来源** | 一眼核对白名单是否生效，不用猜 |
| warning | `app/main.py:55` | `CORS_ORIGINS` 未配置 → 退化为放开并告警 | 把"配置漏填"从**无声事故**变成日志第一屏可见 |
| warning | `app/main.py:61` | `CORS_ORIGINS` 显式含 `*` | 合规口径要求"放开要留痕" |
| warning | `app/main.py:64` | 线上仍用本地默认来源 → 退化并告警 | BUG-12 事故的复盘产物：误配必须喊出来 |
| warning | `app/main.py:86` | **Render 上却用 SQLite** | 免费实例文件系统是临时的，数据会全丢 |
| warning | `ai/llm_agent.py:322` | LLM 输出不可用 → 回落规则版，附异常类型与原因 | AI 降级必须留痕，答辩可查"为什么没用模型" |
| warning | `ai/context.py:219` | 查库失败 → 回落 seed 数据，附原因 | 区分"AI 挂了"与"库挂了" |
| warning | `app/api/ai.py:108` | 上下文组装失败 → 用最小上下文 | 连 seed 都读不到时，仍要能定位 |
| exception | `app/api/trades.py:211` / `:310` | **买入/卖出失败**（含 user_id、player_id 与堆栈） | 交易是最危险的写路径，失败必须能追到人和标的 |
| exception | `app/core/errors.py:59` | 未处理异常（method + path + 堆栈） | 500 不把堆栈给前端，但**服务端必须留全套** |
| info | `app/main.py:87` | 启动打印**日志文件路径**（含 `/api/debug/logs` 提示） | 出问题先知道去哪看 |
| info | `app/api/auth.py:206` | 账号删除（user_id、昵称、连带持仓/流水/令牌条数） | 删号是破坏性操作，必须可追溯 |
| info | `app/core/database.py:95` | 启动补齐 `users` 口令列时说明补了哪些列 | 老库升级静默改表最危险 |

**一条真实日志长什么样**（2026-11-07 本机实跑：注入一个超时的假 client，不触网）：

```
WARNING ai.llm_agent LLM 输出不可用，回落规则版：TimeoutError: model did not respond in 20s
→ 接口返回 200，source=rule_fallback，action=HOLD
```

这一行同时证明三件事：① 异常被**分级捕获**而不是裸 except；② 降级**留痕**；③ 故障**没有升级成 5xx**，交易与行情不受影响。

> 量化：`app/` + `ai/` 中 `except / raise ApiError` 相关语句 **28 处**，全部有对应用例（216 条中约 50 条是异常/边界路径）。

**日志不只刷在控制台：同时落盘，出错能自查**

| 能力 | 实现 | 怎么用 |
| --- | --- | --- |
| **写文件** | `app/core/logging_config.py`：`RotatingFileHandler`（单文件 2 MB、保留 3 份、UTF-8） | 默认 `logs/app.log`，可用 `LOG_DIR` 覆盖；目录不可写时自动退到临时目录，**绝不因日志失败拖垮启动** |
| **控制台照旧** | 同时保留 `StreamHandler` | 开发时 `uvicorn` 窗口里还是能实时看到 |
| **降噪** | `httpx` / `httpcore` / `urllib3` 压到 WARNING | 否则每发一个请求打一行，真实错误会被淹没（实测压制前 119 KB，压制后 4 KB） |
| **本地自查** | `Get-Content logs\app.log -Tail 50` | 不用启动服务也能看历史错误 |
| **线上自查** | `GET /api/debug/logs?lines=100&level=WARNING` | Render 没有终端，浏览器打开网址即可看最近日志；与 `debug.py` 同一开关，`DEBUG_ENDPOINTS=0` 时返回 404 |

> 安全边界：日志里**从不写口令、token、连接串**（代码中无一处这样写）；日志接口只读、路径来自服务端配置，不接受用户输入，因此没有目录穿越面。
> 覆盖：`logging_config.py` 与 `logs.py` 均有单测（含"目录不可写退临时目录""重复初始化不重复挂 handler""端点关闭时 404"）。

**没有日志的地方，与原因**（如实交代）：

| 模块 | 情况 | 为什么合理 |
| --- | --- | --- |
| `code/core_engine/` | **0 处日志** | 纯函数：不碰库、不碰网络、无副作用；参数非法一律 `raise ValueError`（9 处），由调用方决定怎么记录 |
| `scripts/` | 用 `print` 而非 logger | 命令行工具，输出即用户界面（灌数 1/3、2/3、3/3 进度），进日志反而难读 |

### 1.2 异常与错误处理

**第一层：所有失败都是同一个 JSON**（契约 `api_contract.md` §2）

```json
{"success": false, "message": "可直接展示的中文", "code": "机器码"}
```

由 `app/core/errors.py` 统一挂三个 handler：

| 异常类型 | HTTP | `code` | 行为 |
| --- | --- | --- | --- |
| `ApiError`（业务） | 400 / 404 / 500 | 见下表 | `message` 前端**直接展示**，不写映射表 |
| `RequestValidationError`（Pydantic） | 422 | `VALIDATION_ERROR` | 转成"请求参数不合法：quantity"这类人话，不暴露 Pydantic 原文 |
| 其它所有异常 | 500 | `INTERNAL_ERROR` | `logger.exception` 留全套堆栈；**返回给前端的只有一句中文** |

**第二层：7 个业务错误码，每个都有对应用例**

| `code` | 触发条件 | 测试 |
| --- | --- | --- |
| `PLAYER_NOT_FOUND` | 选手不存在 | `test_api_ai.py`、`test_api_players.py` |
| `INSUFFICIENT_BALANCE` | 余额不足（提示带"最多可买 N 股"） | `test_trades_rule.py` |
| `INSUFFICIENT_POSITION` | 持仓不足（提示带"可卖 N 股"） | `test_trades_rule.py` |
| `POSITION_LIMIT_EXCEEDED` | 超过 50 股上限 | `test_trades_rule.py` |
| `PLAYER_TRADING_SUSPENDED` | 比赛中暂停交易 | `test_core_exceptions.py` |
| `ENDPOINT_DISABLED` | 只读自检接口未开启 | `test_debug_api.py` |
| `INTERNAL_ERROR` | 未预期异常兜底 | `test_core_exceptions.py`（回滚路径） |

**第三层：捕获方式有纪律**（实测 32 处 `try/except`）

| 纪律 | 做法 | 反例（我们没这么写） |
| --- | --- | --- |
| **不裸 except** | 只捕具体类型：配置用 `ImportError/ValueError`，网络与 JSON 用 `OSError/ValueError` | `except:` 一把抓，连 Ctrl+C 都吞掉 |
| **兜底必须留痕** | 确实需要 `except Exception` 的地方，一律 `logger.exception(...)` + 注释说明为什么宽 | 静默 `pass` |
| **兜底不暴露堆栈** | 转成 `ApiError("交易失败，请稍后重试", 500, "INTERNAL_ERROR")` | 把 traceback 直接返回前端 |
| **不可测的兜底标出来** | `# pragma: no cover` 标注（交易兜底 2 处、5 个 `__repr__`），覆盖率报告里能看出它们是"刻意不测"而非"漏测" | 为了刷覆盖率硬造用例 |

**第四层：事务边界**（写路径的安全网）

- `db.commit()` 4 处、`db.rollback()` 8 处，**成对出现**：`except ApiError → rollback → raise`（保留原始错误码），`except Exception → rollback → logger.exception → 转 500`；
- 并发安全不靠"先查后写"，而是**把判断写进 SQL 的 WHERE + 看 `rowcount`**（BUG-01 的修复），失败即回滚；
- 三张表（余额/持仓/流水）在同一事务内，任一步失败整批回滚。

**第五层：AI 侧的四类故障一律降级，不影响主流程**

| 故障 | 处理 | 结果 |
| --- | --- | --- |
| 无密钥 | 直接走规则版 | 200 + `rule_fallback` |
| 超时（20s） | 捕获 `OSError` → 规则版 | 200 + `rule_fallback` |
| 输出非 JSON / 字段缺失 / 枚举非法 | `ValueError` → 规则版 | 200 + `rule_fallback` |
| 上下文组装失败 | `_minimal_context` 继续算 | 200 + `rule_fallback` |

> 量化：`try/except` **32 处**、`raise ApiError` **15 处**、`raise ValueError` **9 处**（引擎入参校验）、`logger` 调用 **15 处**；216 条用例里**约 50 条专测异常与边界路径**（暂停交易、超上限、余额不足、脏输出、并发、上下文失败）。

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
| pytest | 单元+集成测试 | `pyproject.toml` | **216 passed / 0 skipped**（CI run #95；截图 17 摄于 134 条的时点，此后补到 216 条） |
| coverage.py | 覆盖率 | 命令行 `--source=app,core_engine` | **98%**（1289/43，≥60% 达标） |
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
python -m pytest                                     # 216 passed
ruff check --select E4,E7,E9,F,C901 code/backend code/core_engine tests
ruff check --select E,W code/backend code/core_engine tests scripts   # PEP8：仅 25 条 E501
pylint code/core_engine code/backend/app/core        # 9.74/10
complexipy code/core_engine                          # 认知复杂度
coverage run --source=app,core_engine -m pytest && coverage report -m # 97%
cd code/frontend; npm ci; npm run build; npm run lint; npm run test:unit

# 代码统计（§3 那张表就是它跑出来的）
git ls-files | Select-String -Pattern '\.py$|\.vue$|\.ts$|\.md$|\.css$|\.html$|\.json$|\.ya?ml$'

# §1 的日志/异常清单（数字都可复核）
git grep -n "logger\." -- code/backend code/core_engine      # 12 处调用
git grep -c "raise ApiError" -- code/backend                  # 15 处业务异常
git grep -n "pragma: no cover" -- code/backend                # 刻意不测的兜底

# 真实降级日志（§1.1 那条 WARNING，注入超时假 client，不触网）
python -c "import logging; logging.basicConfig(level=logging.INFO); from ai.llm_agent import analyze; analyze({'player_id':1,'name':'ZywOo','current_price':126.0,'change_pct':5.0,'rating':88,'recent_prices':[{'price':120.0},{'price':126.0}],'position':{'quantity':10,'avg_cost':120.0}}, chat=lambda p: (_ for _ in ()).throw(TimeoutError('model did not respond in 20s')))"
```

CI 结果：<https://github.com/July75-bit/Innovation/actions>（最新 run #95 三 job 绿）。
