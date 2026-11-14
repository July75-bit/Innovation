# 代码质量报告（`docs/software/code_quality.md`）

> **为什么有这个文件**：课程第 3 天第 2 部分代码质量检查点（SWIEP.pdf p.174）要求提交
> `docs/software/code_quality.md`（扫描报告截图 + 重构前后对比）。本文件是**该路径的正式交付件**，
> 详细数据与逐条对比保存在 [`docs/acceptance/code_quality_report.md`](../acceptance/code_quality_report.md)。
> **负责人**：D 王泽棠 ｜ **最近更新**：2026-11-07

## 1. 用的静态分析工具

| 工具 | 用途 | 配置 | 是否进 CI |
| --- | --- | --- | --- |
| **ruff 0.17.4** | 静态分析 + 风格（兼容 pycodestyle E/W、"真实缺陷"规则 F、圈复杂度 C901） | `pyproject.toml` `[tool.ruff.lint]`，`line-length = 100` | ✅ 四条命令分档卡门禁 |
| **Pylint 4.1.3** | 语义分析（未定义变量、隐蔽的编码错误） | 命令行，范围为 `core_engine` + `app/core` | ⬜ 只做体检（结果进报告） |
| **complexipy 8.3.0** | 认知复杂度（与 VSCode 插件同内核） | 命令行 | ⬜ 只做体检 |
| **coverage.py** | 覆盖率 | `--source=app,core_engine` | ⬜ 本地复跑（97%） |
| **ESLint + oxlint + vue-tsc** | 前端规范与类型 | `code/frontend` | ✅ CI 前端 job |

## 2. 扫描指标（重构前 → 现状）

| 指标 | 第 3 天首次扫描 | 重构后 | 当前（2026-11-07） |
| --- | --- | --- | --- |
| ruff 问题数 | 51 | 44（Top5 重构后） | **72**（新增代码带来的新增项，D 负责文件 **0**） |
| 重复率 | 16.09%（dup-report 口径） | 12.52% | — |
| 业务代码最高圈复杂度 | 11（`scripts/simulate_match.py`） | **7** | 7 |
| 认知复杂度（complexipy） | 未统计 | 最大 27 / 均值 3.31（>15 全在 `scripts/`） | 同左 |
| pytest | 65 passed / 5 skipped | 81 passed / 0 skipped | **216 passed / 0 skipped** |
| 覆盖率 | 未统计 | 91% | **96%**（1515 语句 / 60 未覆盖） |

## 3. Top 5 最严重问题与重构方式

> 规则：**先补测试，再重构**（课件要求）。每一条都能在 `git log` 里找到对应提交与用例。

| # | 问题 | 怎么重构 | 守护用例 |
| --- | --- | --- | --- |
| 1 | `context.py` 里 `_pct` 与接口层重复实现涨跌幅 | 抽 `pct_change()` 公共函数，两条路径共用 | `test_ai_context` 相关断言 + e2e |
| 2 | `llm_agent.py` 捕获过宽（裸 except 倾向） | 收窄为 `ImportError/ValueError`（配置）与 `OSError/ValueError`（网络/JSON），并补 `logger.warning` | `test_llm_agent.py` 13 条 |
| 3 | `scripts/simulate_match.py::main` 圈复杂度 11 | 拆成 4 个函数（参数装配 / 跑批次 / 汇总 / 输出） | `test_simulate_match_cli.py` |
| 4 | e2e 用例单函数 63 条语句 | 抽 `_get_json / _post_json / _assert_*` 六个辅助函数 | `test_e2e_flow.py` 2 条仍全绿 |
| 5 | 响应拼装里魔术数字与重复字符串 | 提常量（`CENT`、阈值、提示模板） | 全量回归 |

## 4. 复跑命令（评委可现场验证）

```powershell
cd D:\projects\innovation\Innovation
conda activate playerstock

ruff check --select E4,E7,E9,F,C901 code/backend code/core_engine tests   # 业务/测试
ruff check --select E4,E7,E9,F,C901 scripts                               # 脚本（阈值 12）
ruff check --statistics .                                                  # 全仓统计（72 项）
pylint code/core_engine code/backend/app/core                              # 9.74/10
coverage run --source=app,core_engine -m pytest && coverage report -m      # 97%
```

## 5. 截图

- `docs/acceptance/evidence/17-code-quality-scan.png`：静态扫描 + 测试 + CI 门禁
- `docs/acceptance/evidence/18-quality-pylint-pep8.png`：Pylint 评分 / PEP8（仅 25 条 E501）/ 格式化体检
- `docs/acceptance/evidence/19-complexity-stats.png`：认知复杂度 + 代码统计
- `docs/acceptance/evidence/37-pytest-coverage.png`：回归 + 覆盖率（264 条 / 96%）

## 6. 已知不足（如实交代）

- `ruff format` 未设 CI 门禁（避免一次性大 diff 淹没评审），只做健康度记录；
- 依赖漏洞扫描（pip-audit）未接入；
- Pylint 只覆盖核心计算与事务层，不是全仓。
