# 线上环境证据（后端 · 只读自检 / CORS / 前端构建）

> 采集人：B ｜ 时间：2026-10-25 ｜ 对应检查单：B7（后端日志无 SQLite 警告 / 库表清单）、TC-402（CORS）、TC-405（子路由刷新）
>
> 为什么用**文本证据**而不是截图：这些是"可复制、可 diff、可复跑"的东西——截图会被压糊、
> 也无法验证。命令与原始输出都在下面，任何人重跑一次就能得到同样结果；需要图片时再截同一屏即可。

## 1. 后端自检接口 `GET /api/debug/db`（证明线上用 Postgres、表在库里）

```bash
curl https://playerstock-backend-mdlk.onrender.com/api/debug/db
```

原始响应（2026-10-25）：

```json
{
  "状态": "线上内网连接成功（只读自检）",
  "数据库方言": "postgresql",
  "是否 SQLite": false,
  "表清单": ["players", "positions", "price_history", "trades", "users"],
  "表行数": {
    "players": 8,
    "positions": 0,
    "price_history": 78,
    "trades": 5,
    "users": 1
  },
  "业务核对": {
    "选手数": 8,
    "价格历史条数": 78,
    "持仓条数": 0,
    "流水条数": 5,
    "demo 余额": "5000.00"
  },
  "提示": "只读元信息，不含连接串与个人数据；可用 DEBUG_ENDPOINTS=0 关闭本接口"
}
```

**结论**：`数据库方言 = postgresql`、`是否 SQLite = false` → 线上确实跑在 Render Postgres 上；
5 张表齐全；`price_history` 78 条（9 轮配方）、`trades` 5 条（TC-403 的 3 条 + 性能实测的 2 条）、
`players` 8 名、`demo 余额 5000.00`（净额为 0 的买卖后回到初始值）。

> 这与 `deployment.md` §4.5.1 的期望完全一致；接口是只读探针，功能验收后可 `DEBUG_ENDPOINTS=0` 关掉。

## 2. CORS 实测（证明前端域名被放行，且不是 `*`）

```bash
curl -s -D - -o /dev/null -H "Origin: https://playerstock-frontend-mdlk.onrender.com" \
  https://playerstock-backend-mdlk.onrender.com/api/health
```

| 请求 `Origin` | 返回的 `access-control-allow-origin` |
| --- | --- |
| `https://playerstock-frontend-mdlk.onrender.com` | `https://playerstock-frontend-mdlk.onrender.com` ✅ |
| `https://evil.example.com` | （无该头，被拦）✅ |

**结论**：`render.yaml` 里的 `CORS_ORIGINS` 已生效，走的是**白名单**而不是 `*`；
`localhost:5173` 与前端域名各走各的——上一轮"线上前端被拦"（BUG-12）已闭环。

## 3. 前端构建产物（证明 `/market` 白屏修复已上线）

```bash
curl -s https://playerstock-frontend-mdlk.onrender.com | grep -o 'assets/[^"]*\.js'
curl -s https://playerstock-frontend-mdlk.onrender.com/assets/index-DQQqv-MS.js | grep -c 'pathMatch'
```

- 当前 bundle：`assets/index-DQQqv-MS.js`（97 kB / gzip 38 kB）+ `assets/index-DpGZtqYP.css`
- 在该 bundle 中检索到 `"/market"`、`"pathMatch"`、`"redirect"`、`"players/:id"` 全部命中
  → 说明已部署的代码包含 `BUG-11` 的修复（`/market → /` 重定向 + 兜底路由）

**结论**：`/market` 直接访问不会再白屏，会跳到市场页（`/`）。
服务端 `GET /market` 也返回 200（SPA rewrite 生效），服务器与前端两侧都成立。

## 4. 复现方式

```bash
# 1) 只读自检（Postgres / 表 / 行数）
curl https://playerstock-backend-mdlk.onrender.com/api/debug/db

# 2) CORS（应回显前端域名；陌生来源应无该头）
curl -s -D - -o /dev/null -H "Origin: https://playerstock-frontend-mdlk.onrender.com" \
  https://playerstock-backend-mdlk.onrender.com/api/health

# 3) 前端 bundle 是否含路由修复
curl -s https://playerstock-frontend-mdlk.onrender.com/assets/index-DQQqv-MS.js | grep -c pathMatch

# 4) 演示前预热（顺带核对每人 ≥10 个价格点）
python scripts/prewarm.py --base https://playerstock-backend-mdlk.onrender.com --min-points 10
```
