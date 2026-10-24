# 代码质量报告（第 3 天检查点）

> **负责人**：D ｜ **日期**：2026-10-24 ｜ **对应课程要求**：第 3 天第 2 部分「代码质量」实践与检查点（SWIEP.pdf p.144–158）：配置至少一个静态分析工具 → 扫描并记录指标 → 选 Top5 最严重问题逐一重构（先补测试）→ 重新扫描对比 → 形成质量报告（**检查点：扫描报告截图 + 重构前后对比**）。
> **对应交付物**：`docs/acceptance/test_report.md`、`docs/acceptance/test_plan.md`

## 1. 工具与配置

| 项 | 内容 |
| --- | --- |
| 静态分析工具 | **ruff**（Python 官方生态最活跃的 linter，可一条命令完成规则检查 + 自动修复） |
| 版本 | ruff 0.17.2（本地经 `uv tool run` 运行；CI 中 `pip install ruff`） |
| 配置文件 | `pyproject.toml` 已有 `[tool.ruff]`：`line-length = 100`、`target-version = "py312"` |
| 扫描范围 | `code/backend`、`code/core_engine`、`tests`、`scripts`（52 个 `.py` 文件，4446 行；去掉空行/纯注释后 3352 行） |
| 复现命令 | 见 §6 |

**为什么选 ruff**：一条命令同时覆盖 E/F（语法与真实 Bug）、B（bugbear）、UP（现代化）、I（导入序）、RUF（ruff 自身规则）、C901（圈复杂度）；且 `--fix` 能自动修 32 项低风险问题，适合 6 天工期。

## 2. 初始扫描（重构前，develop @ `01f53c1`）

```text
$ uv tool run ruff check code/backend code/core_engine tests scripts --statistics
15  B008    function-call-in-default-argument
10  UP037   quoted-annotation
10  I001    unsorted-imports
 6  RUF100  unused-noqa
 4  BLE001  blind-except
 3  UP017   datetime-timezone-utc
 1  UP035   deprecated-import
 1  RUF022  unsorted-dunder-all
 1  FURB157 verbose-decimal-constructor
Found 51 errors.  [*] 32 fixable with `--fix`.
```

| 指标 | 数值 | 说明 |
| --- | --- | --- |
| 总问题数 | **51** | 52 个文件 / 4446 行 |
| Bug 级（E4/E7/E9/F） | **0** | 无未定义名、无语法错误、无重复定义等真实缺陷 |
| Code Smell / 风格 | 51 | B008 15（FastAPI 依赖注入惯用法，工具误报）、UP037 10、I001 10、RUF100 6、BLE001 4、UP017 3、UP035 1、RUF022 1、FURB157 1 |
| 圈复杂度 | 最大 **6**（`trades.buy`、`seed_db.seed`）；> 10 的函数 **0 个** | `ruff --select C901 --config "lint.mccabe.max-complexity = 10"` 无输出 |
| 重复率（粗算） | **16.09%**（535 / 3325 有效行） | 连续 5 行窗口；Top 重复块基本是各文件头部的 import 样板（见 §5） |

## 3. Top 5 问题与重构（先补测试，再改代码）

> 纪律：每次改动前先确认有测试覆盖；改完全仓 `python -m pytest` 必须仍是 **65 passed / 5 skipped**（重构不改变外部行为）。
> 说明：D 的写权限边界是 `code/backend/ai/`、`docs/`、`.github/`、`render.yaml`；因此 Top5 全部选在 D 负责范围内，其余问题按归属移交（§4），不擅自改 B/C 的代码。

| # | 问题（扫描规则） | 位置（重构前） | 重构动作 | 重构后 |
| --- | --- | --- | --- | --- |
| 1 | **PLR0915** 函数过长（63 条语句 > 阈值 50） | `tests/integration/test_e2e_flow.py::test_full_trade_flow` | 抽出 `_get_json` / `_post_json` / `_assert_market_contract` / `_assert_price_history` / `_assert_account` / `_assert_holding` / `_assert_trades` 7 个辅助函数，主用例只保留流程与关键断言 | 主用例降到 **< 50 条语句**，PLR0915 消失；断言一条没少，pytest 仍全绿 |
| 2 | **BLE001** 盲捕获 `Exception` ×4（AI 链路，可能掩盖真实异常） | `ai/context.py`、`ai/llm_agent.py` ×2、`app/api/ai.py` | 拆分"必须兜底"与"意外异常"：`_load_settings` 收窄为 `(ImportError, ValueError)`；`_default_chat` 收窄为 `(OSError, ValueError)`；`analyze()` 与上下文回落保留兜底但加 `# noqa: BLE001` + 理由，并**补 `logging.warning` 记录回落原因**（之前是静默吞掉） | BLE001 **4 → 0**；AI 硬约束不变（故障仍 200 + `rule_fallback`），但日志可追溯 |
| 3 | **UP035** 使用已弃用导入（`typing.Callable`） | `ai/llm_agent.py` | 改为 `from collections.abc import Callable`（ruff 自动修复） | 0 |
| 4 | **I001** 导入顺序/格式不规范 ×2 | `app/api/ai.py`、`tests/unit/test_llm_agent.py` | ruff `--fix` 自动排序、合并空行 | 0 |
| 5 | **重复代码**：涨跌幅 helper `_pct` 在 `ai/context.py` 与 `app/api/ai.py` 各写一份 | 两份 `_pct` | 在 `ai/context.py` 抽出公共 `pct_change(prev, current)`，接口层「最小上下文」直接复用；删除重复实现 | 重复实现 **2 → 1**；重复率 16.09% → **15.66%** |

## 4. 重构前后对比

| 指标 | 重构前 | 重构后 | 变化 |
| --- | --- | --- | --- |
| ruff 总问题数 | 51 | **44** | −7（D 负责文件由 8 → **0**） |
| D 负责文件的问题数 | 8 | **0** | ✅ 全部清零 |
| Bug 级（E4/E7/E9/F） | 0 | 0 | 无新增 |
| 圈复杂度（最大） | 6 | 6 | 重构未引入更复杂函数；> 10 仍为 0 |
| 重复率（5 行窗口粗算） | 16.09% | 15.66% | −0.43pp（`_pct` 重复实现消除） |
| pytest | 65 passed / 5 skipped | **65 passed / 5 skipped** | 行为不变 |

**剩余 44 项按文件归属移交（不改他人代码，避免越界）**

| 归属 | 问题 | 建议动作 |
| --- | --- | --- |
| B（`app/models`、`app/api`、`app/core`、`scripts/seed_db.py`、`tests/conftest.py`） | UP037 10、UP017 3、RUF022 1、FURB157 1、I001 5、RUF100 5、B008 14 | 一条 `ruff check --fix <这些文件>` 可自动修 29 项；B008 为 FastAPI 依赖注入惯用法，建议工具配置豁免（不改代码） |
| C（`scripts/simulate_match.py`、`tests/unit/test_pricing.py`） | I001 2、RUF100 1 | 同上自动修复 |
| 交叉/工具误报 | B008 15（全部） | FastAPI 标准写法，建议加 per-file ignore 或 `# noqa: B008` |

> CI 的门槛只对 **Bug 级 + 圈复杂度**（`E4,E7,E9,F,C901`）做强制校验（当前全仓 0 违规），风格类问题由各负责人按上表清理，避免一上线就红。

## 5. 重复率的口径与已知限制

- ruff 不直接输出重复率，本报告用自写脚本粗算：把每个 `.py` 去掉空行/纯注释后按**连续 5 行**做滑动窗口，出现 ≥2 次视为重复；重复行数 / 有效行数 = 重复率。
- 因此 import 头部、类型定义等"结构性样板"会显著抬高数值（Top 重复块都是 import 段），**该指标只用于同一项目前后对比，不能与 SonarQube 等工具的重复率直接比较**。
- 业务逻辑层面的真实重复（`_pct`）已按 Top5 #5 消除。

## 6. 复现命令

```bash
# 安装/运行（本地经 uv；CI 用 pip install ruff）
uv tool run ruff check code/backend code/core_engine tests scripts --statistics
uv tool run ruff check code/backend code/core_engine tests scripts --select C901 \
  --config "lint.mccabe.max-complexity = 10"
uv tool run ruff check code/backend/ai code/backend/app/api/ai.py \
  tests/unit/test_llm_agent.py tests/unit/test_api_ai.py \
  tests/unit/test_ai_fallback.py tests/integration/test_e2e_flow.py   # D 负责文件：All checks passed

# 重复率（报告用临时脚本，不入库）
python - <<'PY'
...  # 见报告 §5 方法；扫描 git ls-files 的 .py，5 行窗口统计
PY

# 回归（重构前后一致）
python -m pytest   # 65 passed / 5 skipped
```

## 7. 结论

- 项目**没有 Bug 级**静态问题；主要问题是风格/一致性（51 项中 32 项可自动修）。
- D 负责的 AI 模块与测试已做到 **ruff 0 残留**，并通过"收窄异常 + 补日志 + 抽公共函数 + 拆分长测试"完成 Top5 重构，重构前后 pytest 结果一致。
- 剩余 44 项已按归属移交 B/C；B008 建议作为框架惯用法统一豁免。
