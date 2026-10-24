# 交接：PlayerStock 第 1 天后端（B 同学）

> 用途：把上一个会话的上下文交给 **工作区 = `D:\创新创业\main\Innovation`** 的新会话。
> 新会话开工前先读完本文件，再按第 10 节的第一句话启动。
> 读完后可直接删除本文件（它不属于课程交付物）。

---

## 1. 仓库与当前状态

| 项 | 值 |
| --- | --- |
| 仓库 | `D:\创新创业\main\Innovation`（远程 `github.com/July75-bit/Innovation`） |
| 分支 | `develop` |
| 交接时状态 | 后端改动已提交并推送：`408a4df feat(backend): 第 1 天后端骨架与交易闭环`（`develop` 与 `origin/develop` 同步）；工作区除本交接文件外干净 |
| 数据库 | 仓库内没有 `playerstock.db`（`*.db` 已忽略）；需要时用 seed 脚本生成 |
| 虚拟环境 | 仓库内没有 `.venv`，需要按第 7 节新建 |

## 2. 角色与边界（新人最容易踩线的地方）

- 本上下文对应 **B：后端与交易系统**，做完了 `day1 (1).md` 里 B 的第 1 天任务。
- **不要动**：
  - `code/frontend/`（A 的前端）
  - `code/core_engine/`、`data/seed_players.json`（C 的定价与数据）
  - `code/backend/ai/`、`code/backend/app/api/ai.py`（D 的智能体）
  - `docs/` 下除 `software/api_contract.md`、`software/database_design.md` 之外的文档（D 维护）
- B 可改：`code/backend/app/{api,models,schemas,core}`、`code/backend/requirements.txt`、`scripts/seed_db.py`、`tests/`。

## 3. 已完成（均已验证，不是"写完了"）

| 模块 | 内容 |
| --- | --- |
| `app/models/` | `users / players / positions / trades / price_history` 五张表，与 `docs/software/database_design.md` 一一对应 |
| `app/schemas/` | `PlayerSummary / PlayerDetail / AccountResponse / PositionItem / PricePoint / PriceHistoryResponse / TradeRequest / TradeResponse / TradeItem` |
| `app/api/` | 9 个接口：health、players 列表/详情、prices、account、positions、trades 买入/卖出/流水；新增 `deps.py`（demo 账户） |
| `app/core/` | 新增 `rules.py`（交易规则纯函数）、`errors.py`（统一错误格式）、`time.py`（ISO 8601 UTC）；`config.py` 修 SQLite 相对路径；`database.py` 开外键/WAL/busy_timeout |
| `scripts/seed_db.py` | 读 `data/seed_players.json` 落库 8 名选手 + 初始价格历史 + demo 账户，支持 `--reset` / `--check` |
| `tests/` | `conftest.py` 改为独立临时库；`test_trades_rule.py` 去掉 9 条 skip；新增 `test_api_players.py`、`test_trade_rules_unit.py` |
| `docs/software/` | `api_contract.md` 状态列改为已实现；`database_design.md` 补变更记录、勾选 TODO、附录贴实测 `.schema` |

实测验收数据：

- `python -m pytest` → **27 passed, 7 skipped**（5 条 C 的定价、2 条 D 的集成，按分工保留）
- `python scripts/seed_db.py --reset` → `players=8`、`price_history=15`、`users=1`，demo 余额 5000
- 接口：买入 2 股 @126.00 → 余额 4748.00、持仓 2 股、流水 1 条；卖出 1 股 → 4874.00

## 4. 契约不变量（改代码前必须记住）

完整字段见 `docs/software/api_contract.md`，这里只列最容易写错的：

- 主键叫 `player_id`（不是 `id`）；价格叫 `current_price` / `prev_price`；
- `change_pct` 由后端算好（`(current - prev) / prev × 100`），前端不重算；
- `rating` 是 **0–100 的项目模拟综合分**，不是 HLTV Rating，UI 必须标注"模拟"；
- `status ∈ {trading, suspended}`，`side ∈ {BUY, SELL}`；
- 价格历史返回 `{player_id, points: [...]}`：升序、每条带 `reason`、空数组不 404；
- 数量非法 → **422 `VALIDATION_ERROR`**；业务失败 400/404 + 中文 `message` + 机器 `code`；
- 时间统一 ISO 8601 UTC（`...Z`），金额两位小数；
- 校验顺序：选手存在 → 数量 → 是否暂停 → 余额 → 持仓上限 50 股 → 事务提交；
- 余额/持仓/流水必须同事务；`positions` 有 `UNIQUE(user_id, player_id)` 与 `quantity 1–50` 的 CHECK；
- `data/seed_players.json` 的 `initial_price` 不是 `players` 字段，落成 `price_history` 第一条（`reason = 初始价格`）。

## 5. 未完成（交接给其他人 / 后续）

| 归属 | 事项 |
| --- | --- |
| B | 提交已完成（`408a4df`，直接提交到 `develop` 并推送）；后续改动建议按 `feat/b-backend` 分支 + PR 流程，第 2 天继续交易侧（并发/幂等、手续费若采纳、签到补给等） |
| A | Vue 前端 4 条路由、`VITE_API_BASE_URL` 接入、`rating` 标注"模拟" |
| C | `test_pricing.py` 5 条 skip、`scripts/simulate_match.py`、由谁触发 `price_history` 写入 |
| D | `GET /api/analysis/{player_id}`（`api/ai.py` 仍是 TODO）、2 条 integration skip、部署文档与 README 定稿 |
| 全员 | `api_contract.md` §7 四人签字仍是空的（B 主持，A/C/D 未签） |

## 6. 交接说明

实际提交信息（已在 `develop` 的 `408a4df`）：

```text
feat(backend): 第 1 天后端骨架与交易闭环（5 张表 / 9 个接口 / 27 条测试通过）

实现 docs/software/api_contract.md 中除 AI 分析外的 9 个接口，落成 5 张表，
补上交易规则与接口契约测试，并同步更新接口契约与数据库设计文档。

验证：python -m pytest → 27 passed, 7 skipped；
seed 后 players=8 / price_history=15 / users=1；
买入 2 股 @126.00 → 余额 4748.00、持仓 2 股、流水 1 条。
```

## 7. 在新工作区恢复环境并验证

```powershell
cd D:\创新创业\main\Innovation

# ① 建虚拟环境（3.12 / 3.13 均可，.venv 已被 .gitignore 忽略）
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r code/backend/requirements.txt

# ② 跑测试（应看到 27 passed, 7 skipped）
python -m pytest

# ③ 造演示数据并启动
python scripts/seed_db.py --reset
cd code/backend
python -m uvicorn app.main:app --reload --port 8000
# 另开窗口： Invoke-RestMethod http://127.0.0.1:8000/api/health
```

`DATABASE_URL` 的相对路径统一按 `code/backend/` 解析，所以从仓库根目录 seed、
从 `code/backend` 启动，读的是同一个 `playerstock.db`（这是本次顺手修的坑）。

## 8. 本机环境坑（Windows + DSH 沙箱，避免重复踩）

1. **HTTPS 出网不可用**（PyPI/GitHub HTTPS 超时），pip 走 HTTP 镜像：
   `python -m pip install -r code/backend/requirements.txt --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
2. **以 0700 权限创建的临时目录会变成"无法访问"**（`Permission denied`），pip / pytest 默认就会这么做。
   若遇到：把 `TEMP`/`TMP` 指向工作区内目录，并用一个把 `os.mkdir/mkdtemp` 的 mode 改成 `0o777`
   的 runner 启动；pytest 也可用 `--basetemp <工作区内目录>`。这是环境问题，**不是项目代码问题**，
   不要把 workaround 写进仓库。
3. 控制台按 GBK 解码，中文日志可能显示乱码；文件本身是 UTF-8，用编辑器/`read` 确认，不要"修"编码。
4. 上一次验证用的是仓库外的 venv（`D:\dsh\code\PlayerStock\code\backend\.venv`）；
   新工作区请按第 7 节在仓库内重建。
5. 删除/写入仓库外目录、以及 ACL 异常的目录，可能触发沙箱审批；只删自己确认过绝对路径的临时产物。

## 9. 会话里做过、但仓库里看不出来的判断

- 卖出（契约第 8 项）原计划第 2 天，因与买入共用校验和事务，本次一并实现并在文档标注"提前完成"。
- 金额字段用 `NUMERIC(12,2)`（`avg_cost` 12,4），SQLite 仍按 REAL 存，但应用层用 `Decimal` 计算；
  已在 `database_design.md` 的"实现说明"里写明，JSON 仍是两位小数，契约不变。
- 未提交、未推送：按团队 PR 流程，交给 B 建分支后提交。
- 沙箱临时文件（pip/pytest 的临时目录、staging 副本）已全部清理，仓库里没有残留。

## 10. 给新会话的第一句话（直接粘贴）

> 读仓库根目录的 `HANDOFF_day1_backend.md`，按里面的边界继续 B 同学的工作。
> 先按第 7 节跑 `python -m pytest`，确认 27 passed / 7 skipped，再开始第 2 天任务；
> 动手前先看 `docs/software/api_contract.md` 和 `docs/software/database_design.md`。
