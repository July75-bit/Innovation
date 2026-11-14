# 14 条缺陷的 Issue 准备稿（建 BugTracker 用，可直接粘贴）

> **用途**：课程第 4 天第 2 部分要求「修改作品缺陷：使用 GitHub 的 Issues / BugTracker Project」。
> 仓库已有 `PlayerStock_Bug tracker` 项目（#3），但**14 条缺陷还没逐条建成 Issue**——本文件把它们写成可直接粘贴的标题 + 正文。
> **数据来源**：`docs/acceptance/test_report.md` §9（每条都有能复跑的用例或实测记录）。
> **纪律**：全部**已修复并关闭**；建 Issue 是为了留痕，不要新建"未修复"的问题。

## 0. 两种建法

### 方式 A：网页（每人 2 分钟 × 14 条）

1. 打开 `https://github.com/July75-bit/Innovation/issues/new`
2. 标题粘贴下面对应那行的**标题**
3. 正文粘贴**代码块里的全部内容**
4. 右侧 `Labels` 选 **`bug`**，`Projects` 选 **`PlayerStock_Bug tracker`**
5. `Submit new issue` → 建好后点 **`Close as completed`**（已修完）

### 方式 B：`gh` CLI 批量（本机装了 GitHub CLI 的话，一次建完）

```powershell
gh auth login
cd D:\projects\innovation\Innovation
# 把本文件每条正文存成 md 后：
$items = @(
  @{t="BUG-01 并发卖出超卖并重复入账（P0）"; f="bug01.md"},
  @{t="BUG-02 买入校验顺序违反契约（P1）"; f="bug02.md"}
  # …按下面 14 条顺次补全
)
foreach ($i in $items) {
  gh issue create --title $i.t --body-file $i.f --label bug
}
```

> 建完把 Issue 号回填到 `test_report.md` §9 表格的「备注」列，我这边可以代改。

---

## 1. BUG-01 并发卖出超卖并重复入账（P0）

**标题**

```
BUG-01 并发卖出超卖并重复入账（P0）
```

**正文**

```markdown
## 现象
持仓 3 股时，两条连接各卖 2 股：结果卖出 **4 股**，余额 `5000.00 → 5504.00`，还残留 1 股——凭空多卖一股、多入账 252 元。

## 根因
实现是「先 `SELECT` 查持仓够不够，够了再 `UPDATE` 扣减」。两条连接同时读到「持仓 3 股」，各自判断通过，于是都扣减。

## 修复
把判断写进 SQL 的 `WHERE`，用 `rowcount` 判定成败：
- 减仓：`UPDATE positions SET quantity = quantity - n WHERE quantity > n`
- 卖光：`DELETE FROM positions WHERE quantity = n`
- 判断失败 → 400 `INSUFFICIENT_POSITION`

## 验证
- `tests/unit/test_trades_concurrency.py` 3 条（同样交错时序，修复后只成功一笔）
- 线上并发实测：两个「卖 1」→ 状态码 `[200, 400]`，余额只入账一次
- 修复前后对比：`docs/software/database_design.md` §3.1

## 教训
**先读后写 = 竞态**；判断要交给数据库，而不是应用层。
```

---

## 2. BUG-02 买入校验顺序违反契约（P1）

**标题**

```
BUG-02 买入校验顺序违反契约（P1）
```

**正文**

```markdown
## 现象
用户余额不足时，接口却提示「超过持仓上限 50 股」。用户会以为是自己买多了，实际是没钱。

## 根因
`api/trades.py` 先查持仓上限、后查余额，与 `api_contract.md` §4.7 规定的顺序不一致。

## 修复
把顺序改成契约规定的：**选手 → 数量 → 可交易 → 余额 → 上限**。

## 验证
`tests/unit/test_trades_rule.py::test_buy_checks_balance_before_position_limit`（把顺序钉死，改回去就红）。
```

---

## 3. BUG-03 清仓触发 CHECK 约束导致 500（P1）

**标题**

```
BUG-03 清仓触发 CHECK 约束导致 500（P1）
```

**正文**

```markdown
## 现象
卖出最后一笔（清仓）时返回 500 `INTERNAL_ERROR`。

## 根因
清仓分支把 `positions.quantity` 更新成 `0`，而表上 `ck_positions_quantity_range` 约束是 1–50，0 直接违约。

## 修复
卖光分支改走 `DELETE`（删除持仓行），而不是把数量置 0。

## 验证
`tests/unit/test_trades_rule.py::test_sell_normal`（断言「卖光后持仓行消失」）。
```

---

## 4. BUG-04 价格 reason 里的「得分」被拼两遍（P2）

**标题**

```
BUG-04 价格 reason 里的「得分」被拼两遍（P2）
```

**正文**

```markdown
## 现象
前端与 AI 拿到的 `reason` 出现「本轮得分 88.5 …… 本轮得分 88.5」这类重复片段。

## 根因
C 的定价引擎拼一次得分，B 落库时又拼一次，双方都以为自己是对的。

## 修复
`with_score_in_reason()` 幂等化：以「得分」为标记，命中即原样透传，不再追加。

## 验证
- `test_score_is_not_duplicated_when_c_already_added_it`
- `test_plan_from_json_passes_through_c_reason`
```

---

## 5. BUG-05 临时定价规则污染价格历史（P1）

**标题**

```
BUG-05 临时定价规则污染价格历史（P1）
```

**正文**

```markdown
## 现象
价格历史的 `reason` 里出现「（定价引擎由 C 接管后替换）」，而这段文字会**直接展示给用户和 AI**。

## 根因
早期占位规则把开发备注写进了业务字段。

## 修复
C 的引擎落地后整段删除临时规则，改走真实链路。

## 验证
`tests/unit/test_update_prices_script.py` 9 条（含 reason 来源与格式）。
```

---

## 6. BUG-06 暂停交易选手仍被改价（P1）

**标题**

```
BUG-06 暂停交易选手仍被改价（P1）
```

**正文**

```markdown
## 现象
状态为 `suspended`（比赛中）的选手价格仍被批量更新，与「比赛中暂停交易」的产品规则冲突。

## 修复
`plan_from_engine` 跳过非 `trading` 选手，并在输出中说明「已跳过 N 名暂停选手」。

## 验证
`tests/unit/test_update_prices_script.py::test_suspended_players_are_skipped`。
```

---

## 7. BUG-07 长 reason 写库失败（P2）

**标题**

```
BUG-07 长 reason 写库失败（P2）
```

**正文**

```markdown
## 现象
`price_history.reason` 是 `VARCHAR(200)`，拼接后超长时写库直接失败。

## 修复
统一截断到 200 字符并加省略号。

## 验证
`test_reason_is_truncated_to_column_limit`。
```

---

## 8. BUG-08 Render 上服务起不来（P0 · 部署阻断）

**标题**

```
BUG-08 Render 上服务起不来（P0 · 部署阻断）
```

**正文**

```markdown
## 现象
本地全绿，按 `render.yaml` 填 `DATABASE_URL` 部署后服务直接退出：`ModuleNotFoundError: No module named 'psycopg'`。

## 根因
**SQLAlchemy 2.1 起，`postgresql://` 的默认 DBAPI 从 psycopg2 换成了 psycopg 3**，而项目只装了 `psycopg2-binary`。

## 修复
在 `config.py` 归一化连接串时**显式钉死驱动**：裸 `postgres://` / `postgresql://` → `postgresql+psycopg2://`；已带驱动的串不改写。

## 验证
`tests/unit/test_config_db_url.py` 6 条，其中一条真的 `create_engine()` 并断言解析到 psycopg2。

## 教训
**别相信默认值**——跨版本、跨库的地方，把假设写成代码和用例。
```

---

## 9. BUG-09 WAL 临时文件误入版本库（P2）

**标题**

```
BUG-09 WAL 临时文件误入版本库（P2）
```

**正文**

```markdown
## 现象
SQLite 开 WAL 后生成 `*.db-wal` / `*.db-shm`，`.gitignore` 没覆盖，跑一次后端就出现在 `git status`，容易被 `git add -A` 顺手提交。

## 修复
`.gitignore` 补两条规则，并用 `git check-ignore` 验证命中。
```

---

## 10. BUG-10 Windows 中文控制台下测试报编码错（P1）

**标题**

```
BUG-10 Windows 中文控制台下测试报编码错（P1）
```

**正文**

```markdown
## 现象
本机 Windows 跑 `test_bootstrap_demo_data.py` 时 pytest 抛 `UnicodeDecodeError 0xd2`，1 failed + 1 error；CI 的 ubuntu 不暴露该问题。

## 根因
`seed_db.py` 没把 stdout 切成 UTF-8：子进程按 GBK 输出中文，而 pytest 的 fd 捕获按 UTF-8 解码。

## 修复
① `seed_db.py` 统一 `reconfigure(encoding="utf-8")`；
② 测试给子进程显式 `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`。

## 验证
用旧版脚本复现出 `0xd2`，修复后在 `PYTHONIOENCODING=gbk` 下也全绿。
```

---

## 11. BUG-11 线上 `/market` 刷新白屏（P2）

**标题**

```
BUG-11 线上 /market 刷新白屏（P2）
```

**正文**

```markdown
## 现象
`/players/1` 按 F5 正常，但 `/market` 按 F5 后**只剩页头**——没有 404、也没有页面，比 404 更像站点挂了。

## 根因
市场页路由是 `/`，`/market` 没有任何路由匹配，也没有兜底；静态站的 SPA rewrite 仍返回 `index.html`。

## 修复
补两条：`/market` → `/` 重定向、`/:pathMatch(.*)*` → `/` 兜底。

## 验证
- 新增 `src/router/__tests__/router.spec.ts` 4 条（`/market` 与未知路径都落市场页，正常子路由不受影响）
- `vitest` / `npm run build` / oxlint / eslint 全绿
- 线上 bundle 里已能检索到 `/market`、`pathMatch`、`redirect` 三个标记

## 教训
**白屏比 404 更危险**：404 至少告诉你地址错，白屏看起来是站坏了。
```

---

## 12. BUG-12 线上前端被跨域拦掉（P0 · 线上可用性）

**标题**

```
BUG-12 线上前端被跨域拦掉（P0 · 线上可用性）
```

**正文**

```markdown
## 现象
CORS 改为「按 `CORS_ORIGINS` 白名单」后部署，浏览器请求 `*-backend.onrender.com` 拿不到 `access-control-allow-origin`，页面显示「连接失败」。

## 根因
代码没错：**Render 控制台没填 `CORS_ORIGINS`**，按默认值只放行 `localhost:5173`。

## 修复（三处一起，防「再忘一次」）
① `render.yaml` 把 `CORS_ORIGINS` 写成前端公网地址（部署配置进仓库）；
② `resolve_cors_origins()` 增加「线上却还是本地默认值 → 退化 `*` 并 WARNING」；
③ `cors_origin_list` 去掉尾部斜杠。

## 验证
- `tests/unit/test_cors_config.py` 8 条（含「线上误配」回归）
- 线上实测：`Origin: 前端域名` → 回显该域名；`Origin: evil.example.com` → **无该头**（白名单生效，不是 `*`）
- 证据：`docs/acceptance/evidence/online/backend-debug-db.md` §2

## 教训
**「改了代码」≠「线上生效」**；兜底要么别做，要做就做到「误配时也能用 + 有声音」。
```

---

## 13. BUG-13 测试里的「日期炸弹」（P2）

**标题**

```
BUG-13 测试里的「日期炸弹」（P2）
```

**正文**

```markdown
## 现象
`test_prices_recalc.py` 在 2026-11-07 当天必红 2 条，换一天跑又全绿。

## 根因
用例把 `PLAYED_AT` 写死成 `2026-11-07`，而 `conftest` 用 `now-2h` / `now-1h` 造种子历史——机器时间正好是那天时，两条历史落进本轮去重窗口 `[played_at, played_at+1d)`，接口把两名选手判成「该轮已计价」。

## 修复
改为「未来 30 天」的相对日期（`datetime.now(UTC).date() + 30d`），并同步断言里的日期。

## 教训
**测试里不要写死「今天附近的日期」**——它会和时间耦合，制造只在某一天失败的假红灯。
```

---

## 14. BUG-14 答辩稿生成脚本写死绝对路径（P2）

**标题**

```
BUG-14 答辩稿生成脚本写死绝对路径（P2）
```

**正文**

```markdown
## 现象
换台机器 / 换个 clone 目录跑 `build_deck.py` 就 `FileNotFoundError`，PDF 无法重新生成；且稿内数字停留在「120 条用例 / 10 条缺陷」。

## 根因
`ROOT = Path(r"D:\projects\innovation\Innovation")` 写死了 D 本机的目录结构。

## 修复
`ROOT` 改为按 `__file__` 反推仓库根；稿内数字同步为真实值（用例数、缺陷数、路由数、前端版本号），并用 Edge headless 重新导出 `defense.pdf`。

## 教训
**任何「本机路径」都不该进仓库**；脚本要能在别人的机器上直接跑。
```
