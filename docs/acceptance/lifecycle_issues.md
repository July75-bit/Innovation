# 生命周期主要问题与解决汇总（汇报 3.4）

> **对应要求**：3.4「整个生命周期，如分析、设计、开发、测试和部署运维中遇到的主要问题及解决方法汇总，可用表格表示」
> **口径**：只收**真实发生过**的问题，每一条都能在仓库里找到修复提交与回归用例；不写"预想的风险"（风险见 `docs/mgmt/risk_plan.md`）。
> **来源**：`docs/acceptance/test_report.md` §9（BUG-01~13）、`docs/acceptance/defect_stories.md`（4 个深度复盘）、`docs/software/deployment.md`、本项目开发日志。
> **截止**：2026-11-07 · 测试基线 219 passed / 0 skipped（覆盖率 97%，auth 模块扩容后待 D 复测）。

## 1. 汇总表

| 类别 | 问题名称 | 发生原因 | 解决办法 |
| --- | --- | --- | --- |
| 开发 · 交易一致性 | **并发卖出超卖并重复入账**（BUG-01，P0） | 实现是"先 `SELECT` 查够不够、再 `UPDATE` 扣减"；两条连接同时读到"持仓 3 股"，各自判断通过 | 把判断写进 SQL 的 `WHERE`（减仓 `quantity > n`、卖光 `DELETE ... AND quantity = n`），以 `rowcount` 判定成败；`test_trades_concurrency.py` 3 条用例，线上并发实测只成功一次 |
| 开发 · 交易一致性 | 清仓触发 CHECK 约束报 500（BUG-03，P1） | 卖光时把 `positions.quantity` 更新为 0，违反 `ck_positions_quantity_range`（1–50） | 卖光分支改走 `DELETE` 删除持仓行；`test_sell_normal` 覆盖"卖光后行消失" |
| 开发 · 交易一致性 | 校验顺序违反契约，没钱却提示"超过持仓上限"（BUG-02，P1） | 代码先查上限后查余额，与 `api_contract.md` §4.7 规定的顺序不一致 | 顺序改为 选手→数量→可交易→余额→上限；新增 `test_buy_checks_balance_before_position_limit` 锁死顺序 |
| 开发 · 数据与契约 | 价格 `reason` 里的"得分"被拼两遍（BUG-04，P2） | C 的引擎拼一次、B 落库时再拼一次，双方都以为自己是对的 | `with_score_in_reason()` 幂等化：以"得分"为标记，命中即透传；两条用例覆盖 |
| 开发 · 数据与契约 | 临时定价规则写进价格历史并展示给用户（BUG-05，P1） | 早期占位规则把"（定价引擎由 C 接管后替换）"直接写进 `reason` | C 引擎落地后整段删除临时规则，改走真实链路；`test_update_prices_script.py` 9 条 |
| 开发 · 数据与契约 | 暂停交易选手仍被改价（BUG-06，P1） | 改价脚本没有过滤 `status`，与"比赛中暂停交易"的产品规则冲突 | `plan_from_engine` 跳过非 `trading` 选手并在输出中说明；`test_suspended_players_are_skipped` |
| 开发 · 数据与契约 | 长 `reason` 写库失败（BUG-07，P2） | 字段是 `VARCHAR(200)`，拼接后超长 | 统一截断到 200 并加省略号；`test_reason_is_truncated_to_column_limit` |
| 测试 | Windows 中文控制台下测试报 `UnicodeDecodeError 0xd2`（BUG-10，P1） | `seed_db.py` 未把 stdout 切成 UTF-8，子进程按 GBK 输出，pytest 按 UTF-8 解码 | 脚本统一 `reconfigure(encoding="utf-8")`；测试给子进程显式 `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`；已用旧版复现并验证修复 |
| 测试 | 测试里的"日期炸弹"（BUG-13，P2） | 用例把 `PLAYED_AT` 写死成 `2026-11-07`，与 `conftest` 的 `now-1h/-2h` 种子历史撞进同一去重窗口，当天必红、次日全绿 | 改为"未来 30 天"的相对日期并同步断言；教训：测试里不写死"今天附近的日期" |
| 部署运维 | **Render 上服务直接起不来**（BUG-08，P0） | SQLAlchemy 2.1 起 `postgresql://` 默认 DBAPI 从 psycopg2 换成 psycopg 3，而项目只装了 `psycopg2-binary` | 连接串归一化时**显式钉死驱动** `postgresql+psycopg2://`（已带驱动的串不改写）；`test_config_db_url.py` 6 条，含真实 `create_engine()` 断言 |
| 部署运维 | **线上 `/market` 刷新白屏**（BUG-11，P2） | 市场页路由是 `/`，`/market` 无匹配也无兜底；静态站 rewrite 仍返回 `index.html` → 没有 404、也没有页面 | 补 `/market → /` 重定向 + `/:pathMatch(.*)*` 兜底；新增 `router.spec.ts` 4 条；线上 bundle 已检索到修复标记 |
| 部署运维 | **线上前端被跨域拦掉**（BUG-12，P0） | CORS 已改为按 `CORS_ORIGINS` 白名单，但 Render 上没填该变量 → 默认只放行 `localhost:5173` | 三处一起补：`render.yaml` 写死前端域名、误用本地默认值时退化 `*` 并 WARNING、尾斜杠归一化；`test_cors_config.py` 8 条；线上实测白名单生效 |
| 仓库卫生 | WAL 临时文件被误提交（BUG-09，P2） | SQLite 开 WAL 后产生 `*.db-wal` / `*.db-shm`，`.gitignore` 未覆盖 | 补两条规则并用 `git check-ignore` 验证 |
| 开发环境 | 全仓 pytest 在 agent 沙箱内全部 ERROR（`PermissionError [WinError 5]`） | pytest 以 0700 权限创建临时目录，被 workspace-write 沙箱拒绝；与代码无关 | 跑全仓测试时申请一次完全权限授权；重定向 TMP 无效（已实测） |
| 开发环境 | 前端依赖装不上 | `registry.npmjs.org` 与国内镜像均连接重置，本机无 `node_modules` | 前端构建只认 CI（`npm ci` → lint → build）；本地只做静态核对，不声称"构建通过" |
| 协作 | 两个会话同时写一个仓库，提交被 `git add -A` 扫走、出现两次冲突 | 并行会话共用工作区，没有任何互斥 | 动 git 前先查 `git status` 与 `MERGE_HEAD`；改完文件重读确认未被覆盖；`docs/mgmt/day5.md` 与 `PlayerDetailView.vue` 的冲突按两边内容合并而非二选一 |

## 2. 按阶段分布

| 阶段 | 条数 | 代表问题 |
| --- | ---: | --- |
| 分析 / 设计 | 2 | 校验顺序与契约不一致（BUG-02）、CORS 口径决策缺失（BUG-12 的来源） |
| 开发 | 5 | 并发超卖（BUG-01）、CHECK 约束（BUG-03）、`reason` 双拼/超长/污染（BUG-04/05/07）、暂停选手被改价（BUG-06） |
| 测试 | 2 | GBK 编码（BUG-10）、日期炸弹（BUG-13） |
| 部署运维 | 3 | 驱动默认值变更（BUG-08）、子路由白屏（BUG-11）、线上跨域（BUG-12） |
| 工具链 / 协作 | 3 | 沙箱 pytest、npm 源不可达、双会话改同仓 |

## 3. 三条可复用的经验（答辩口径）

1. **不要相信默认值**：SQLAlchemy 换了默认驱动、npm 换了源、pytest 换了临时目录权限——每一处都让"本机全绿"变成"线上起不来"。凡是跨环境的地方，把假设写进代码和用例。
2. **白屏比 404 更危险**：404 至少告诉你地址错了，白屏看起来就是"站坏了"。前端路由和静态站 rewrite 必须成对设计，并有用例覆盖"未知路径落到哪里"。
3. **"改了代码"≠"线上生效"**：CORS 的 BUG-12 根因是部署变量没填，代码本身没错。兜底要么别做，要做就做到"误配时也能用 + 有声音（WARNING）"。
