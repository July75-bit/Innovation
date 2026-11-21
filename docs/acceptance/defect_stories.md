# 缺陷故事：四个真实 bug 从发现到修复（答辩素材）

> **用途**：第 6 天答辩的「工程与测试」部分（8 分钟幻灯片里 1–2 页 / 5 分钟 QA 备用）。
> **原则**：只写**真实发生过、有证据**的缺陷；每条都给出「怎么发现的 → 根因 → 怎么修 → 怎么证明修好了」。
> 负责人：B（后端），可与 A/C/D 的素材合并。

## 为什么讲「缺陷故事」而不是「我们没 bug」

老师在课程第 4 天（p.178）专门讲"测试和修复软件缺陷"。真正加分的不是"0 bug"，
而是**能说清一个 bug 是怎么被发现的、根因在哪一层、修完怎么防止再犯**。
下面四条覆盖了四种典型的"发现方式"：

| # | 缺陷 | 怎么发现的 | 教训一句话 |
| --- | --- | --- | --- |
| 1 | 并发卖出超卖并重复入账（P0） | 我自己写并发用例时想到"两个 worker 同时卖会怎样" | **先读后写 = 竞态**，判断要交给数据库 |
| 2 | Render 上直接起不来（P0） | 部署预检时在本地把 `postgresql://` 真造了一次引擎 | **依赖的默认值会变**，要显式钉死 |
| 3 | 线上 `/market` 白屏（P2） | 验收子路由刷新时按 F5 | **白屏比 404 更危险**，它不报错但看起来像挂了 |
| 4 | 线上前端被跨域拦掉（P0） | 性能实测时顺手看了 `access-control-allow-origin` | **"改了代码"≠"线上生效"**，配置漏填要能被日志抓到 |

---

## 故事 1：两笔并发的卖出，把 3 股卖成了 4 股（P0）

**现象**：持仓 3 股时，两条连接各卖 2 股，结果**卖出 4 股、余额凭空多 252 元**，还残留 1 股。

**根因**：实现是"先 `SELECT` 查持仓够不够，够就 `UPDATE` 扣减"。两条连接同时读到"持仓 3 股"，
各自都判断"卖 2 股够"，于是都执行了扣减 —— **判断和写入不是一个原子操作**。

**修法**：把判断写进 SQL 的 `WHERE`，用 `rowcount` 判断成败：

```sql
-- 减仓：条件不成立就一行都不改
UPDATE positions SET quantity = quantity - :n
 WHERE user_id = :u AND player_id = :p AND quantity > :n;
-- 卖光：quantity 有 1–50 的 CHECK，不能写 0，改用 DELETE 做原子判断
DELETE FROM positions WHERE user_id = :u AND player_id = :p AND quantity = :n;
```

另外两条配套：买入/卖出都**先锁账户行再动持仓**（两条路径加锁顺序一致，不会互相死锁），
任一步失败整体 `rollback`，钱货一起回原样。

**证明**：`tests/unit/test_trades_concurrency.py` 3 条用例；同样的交错时序，修复后
是 `400 INSUFFICIENT_POSITION` + 余额 5252.00 + 卖出 2 股、剩余 1 股。
**线上同款验证**：`smoke_test_api.py` 在 Render 上并发两个「卖 1」，状态码 `[200, 400]`，余额只入账一次。

---

## 故事 2：一切就绪，一部署就 `ModuleNotFoundError: psycopg`（P0）

**现象**：所有测试在本机全绿（本地用 SQLite），但按 `render.yaml` 把 `DATABASE_URL` 填成
Postgres 连接串后，服务启动直接挂：`ModuleNotFoundError: No module named 'psycopg'`。

**根因**：**SQLAlchemy 2.1 起，`postgresql://` 的默认 DBAPI 从 psycopg2 换成了 psycopg 3**。
仓库只装了 `psycopg2-binary`，于是"能跑的代码"在换库时立刻炸。这类问题单测永远发现不了——
只有真的用目标数据库造一次引擎才会暴露。

**修法**：在 `config.py` 归一化连接串时**显式钉死驱动**：`postgres://` / 裸 `postgresql://`
统一补成 `postgresql+psycopg2://`（显式写了 `+psycopg` / `+asyncpg` 的不动）。

**证明**：`tests/unit/test_config_db_url.py` 6 条，其中一条真的 `create_engine()` 并断言
`dialect.driver == "psycopg2"` —— 这条如果哪天依赖又换了默认值，CI 会先红。

**教训**：**别相信"默认值"**。跨库/跨版本的地方，把假设写成代码和用例。

---

## 故事 3：线上 `/market` 打开是白屏，而且不报错（P2）

**现象**：验收"子路由刷新"时，`/players/1` 按 F5 一切正常；但 `/market` 按 F5 后**只剩页头**，
内容区空白，控制台也没有明显报错。

**根因**：市场页的路由是 `/`，`/market` 根本没有对应的路由；而静态站又配了 SPA rewrite
（`/*` → `/index.html`），所以 `/market` **返回 200 和一份正常 HTML**，
vue-router 匹配不到组件、又没有兜底路由，于是渲染出空页面。
**白屏比 404 更危险**：404 至少告诉你"地址不对"，白屏看起来就是"站点坏了"。

**修法**：`router/index.ts` 补两条

```ts
{ path: '/market', redirect: '/' },              // 手输/旧书签
{ path: '/:pathMatch(.*)*', redirect: '/' },     // 任何拼错都回首页
```

**证明**：新增 `src/router/__tests__/router.spec.ts` 4 条（`/market` 与未知路径都要落到市场页）。
过程中还踩了一个坑：第一版用 `router.resolve()` 断言，**它不跟随 redirect**，
改用 `router.push()` 真实导航才测到点子上 —— 这个坑写进了测试文件的注释。

---

## 故事 4：代码改对了，线上却把前端拦了（P0）

**现象**：把 CORS 从硬编码 `allow_origins=["*"]` 改成"按 `CORS_ORIGINS` 白名单"后部署，
前端开始报跨域；实测 `access-control-allow-origin` 直接**没有这个头**。

**根因**：代码没错，**部署平台的变量没填**。`CORS_ORIGINS` 在 `render.yaml` 里是
`sync: false`（要在控制台手填），忘了填就落到 `config.py` 的默认值 `localhost:5173` ——
于是线上只放行本地地址，前端被拦。这是典型的"**改了代码 ≠ 线上生效**"。

**修法**（三处，防的是"再忘一次"）：

1. `render.yaml` 把 `CORS_ORIGINS` 直接写成前端公网地址 —— 部署配置进仓库，不靠记忆；
2. `resolve_cors_origins()` 增加一条：**线上却还是本地默认值 → 退化为 `*` 并 WARNING**；
3. `cors_origin_list` 去掉尾部斜杠（手填 `https://x/` 时浏览器 `Origin` 不带 `/`，差一个字符就全站跨域失败）。

**证明**：`tests/unit/test_cors_config.py` 8 条（含"线上误配"回归）；启动日志会打印
`数据库：Postgres（持久化生效）` 与 `CORS 放行来源：…` —— 现在这两个值**一眼可见**，
故障不再是"猜"。

**教训**：**兜底要么别做，要做就做到"误配时也能用 + 有声音"**。静默退化最难查。

---

## 附：QA 可能追问的三句话答案

| 问题 | 一句话回答 |
| --- | --- |
| 你们凭什么说并发是安全的？ | 判断写进 SQL 的 `WHERE` + `rowcount`，并用并发用例和线上并发请求都验过只成功一次 |
| 为什么不用 `*` 放行 CORS？ | 依据非功能需求 NFR-S-04；现在按 `CORS_ORIGINS` 白名单，误配时退化但会告警 |
| 这些 bug 是 AI 发现的吗？ | AI 辅助定位过，但**发现时机和判定标准由人定**：并发交错、部署预检、按 F5、看响应头，都是人工设计的检查动作 |
