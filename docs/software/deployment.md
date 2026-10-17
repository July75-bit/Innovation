# 部署说明

> **负责人**：D ｜ **截止**：第 5 天必须完成并验证 ｜ **状态**：🟡 初稿完成，待第 5 天实测后回填
> **对应课程指标**：#7 部署上线、#22 可运行可复现；验收标准不是"网站能打开"，而是"交易完成后数据能保存"

## 1. 部署架构

| 服务 | 平台 | Root Directory | 构建 | 启动 |
| --- | --- | --- | --- | --- |
| 前端 | Render Static Site | `frontend` | `npm install && npm run build` | 静态（`dist/`） |
| 后端 | Render Web Service | `backend` | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

> 仓库根目录的 `render.yaml` 已写好这两个服务，可以在 Render 里直接 New → Blueprint 导入。

## 2. 环境变量清单

### 后端（Render Web Service → Environment）

| 变量 | 值 | 是否密钥 |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.12.6` | 否 |
| `DATABASE_URL` | 粘贴 Postgres 服务的 **Internal Database URL**（`postgresql://user:pass@dpg-xxx-a/playerstock_db`） | ✅ **是**（含密码） |
| `CORS_ORIGINS` | 前端公网地址，例 `https://playerstock-frontend.onrender.com` | 否 |
| `INITIAL_BALANCE` | `5000` | 否 |
| `MAX_POSITION_PER_PLAYER` | `50` | 否 |
| `PRICING_ALPHA` / `PRICING_BETA` / `PRICING_FLOOR` | `0.15` / `0.0` / `1.0` | 否 |
| `LLM_PROVIDER` / `LLM_MODEL` | `openai` / `gpt-4o-mini` | 否 |
| `LLM_API_KEY` | 真实密钥 | ✅ **是** |
| `LLM_TIMEOUT_SECONDS` | `20` | 否 |

### 前端（Render Static Site → Environment）

| 变量 | 值 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 后端公网地址 | 构建时注入，改完必须重新部署 |

## 3. 部署操作手册（方案 B：免费前后端 + 免费 Postgres）

> 目标：2 个服务 + 1 个数据库，全部免费，预计 30–45 分钟。
> ⚠️ **顺序不能乱**：先建数据库 → 再建后端（要粘数据库地址）→ 再建前端（要粘后端地址）→ 最后回填 CORS。

### 3.0 前置条件（代码侧已就绪）

- [x] `backend/requirements.txt` 已含 `psycopg2-binary`（连 Postgres 的驱动）
- [x] `backend/app/core/config.py` 已把 Render 的 `postgres://` 自动转成 `postgresql://`（不转会启动报 `Can't load plugin: sqlalchemy.dialects:postgres`）
- [x] `backend/app/core/database.py` 已对非 SQLite 开启 `pool_pre_ping`（避免空闲后第一个请求连接失效）
- [x] `backend/app/main.py` 在 Render 上检测到 SQLite 会打警告日志（防止"数据总丢"查不出原因）
- [ ] 代码已推到 GitHub；确认 **要部署的分支**（团队当前用 `develop`，Blueprint 创建时选它，否则推了不自动部署）

### 3.1 注册并授权 Render

1. 打开 <https://dashboard.render.com/register>，用 **GitHub 账号**登录
2. 授权 Render 读取 `July75-bit/Innovation` 仓库

### 3.2 先建免费 Postgres

1. Dashboard → **New → Postgres**
2. Name：`playerstock-db`；**Region 选 Singapore**（必须与后端同区，才能用 Internal URL）
3. Plan：**Free**（1GB；⚠️ **创建后 30 天到期**，到期前 14 天可升级保留）
4. 建好后进服务页 → 复制 **Internal Database URL**（形如 `postgresql://user:pass@dpg-xxxx-a/playerstock_db`）
5. 把创建日期记到 `docs/retrospection/daily_summary.md`，设个到期提醒

### 3.3 建后端 Web Service

1. Dashboard → **New → Blueprint** → 选仓库 + 分支（`develop`）→ Render 自动识别 `render.yaml` 里的两个服务
2. 后端 `playerstock-backend` 的环境变量：
   - `DATABASE_URL` = 3.2 的 **Internal Database URL**（含密码，控制台填写，不进仓库）
   - `LLM_API_KEY` = 模型密钥（暂时没有就留空，AI 自动走规则兜底）
   - `CORS_ORIGINS` = **先留空**，3.5 节回填
3. 等 Deploy 成功 → 打开 `https://<后端>.onrender.com/api/health`，应返回 `{"status":"ok","service":"playerstock-backend"}`

### 3.4 建前端 Static Site

1. Blueprint 的第二个服务 `playerstock-frontend`：
   - `VITE_API_BASE_URL` = 3.3 的后端公网地址（`https://xxx.onrender.com`，**不要带尾部斜杠、不要带 127.0.0.1**）
2. 等 Deploy 成功 → 打开前端地址，页面能加载
3. ⚠️ `VITE_API_BASE_URL` 是**构建时**注入：改了必须重新部署前端才生效

### 3.5 回填 CORS 并重启后端

1. 后端服务 → Environment → `CORS_ORIGINS` 改为前端公网地址（如 `https://playerstock-frontend.onrender.com`）
2. 保存 → 后端自动重新部署
3. 前端 F12 Network：`/api/players` 不再报 CORS 错误

### 3.6 初始化演示数据（免费实例没有 Shell，必须在本地跑）

> ⚠️ 免费 Web Service **不提供 Shell / SSH**，也不能跑 one-off job，所以种子数据不能在线上执行，
> 要连 Render 的 **External Database URL** 从本地写入。

1. 后端启动时会自动建表（`init_db()`），此时表是空的 → 前端会显示"没有选手"
2. 本地仓库根目录执行：

   ```powershell
   cd backend
   $env:DATABASE_URL="<External Database URL>"
   python ../scripts/seed_db.py
   ```

3. 刷新线上前端 → 能看到 8 名 CS2 选手即成功
4. 依赖：**B 必须先实现 `scripts/seed_db.py`**（当前仍是 TODO 桩，属第 2 天任务）

### 3.7 最终验证

按第 5 节清单逐条打勾，重点三条：
- [ ] 线上买卖各成功一次
- [ ] **重新部署后端后，交易记录仍在**（证明 Postgres 真的生效）
- [ ] 后端日志里**没有** `当前部署在 Render 上却使用本地 SQLite` 这条警告

## 4. 数据持久化（必须解决，否则第 5 天验收不过）

### 4.1 已确认的平台事实

> 核实时间：2026-10-17 ｜ 依据：Render 官方文档（[Deploy for Free](https://render.com/docs/free)、[Persistent Disks](https://render.com/docs/disks)）
> 状态：✅ 三条关键结论均已核实，非传闻

| # | 结论 | 对本项目的影响 | 来源 |
| --- | --- | --- | --- |
| 1 | **前端 Static Site + 后端 Web Service 的拆分成立**：静态站点免费托管在全球 CDN 上；只有 Web Service 能跑 Python/FastAPI | 与仓库 `render.yaml` 现有配置一致，拆分方式不用改 | free 文档 § Static sites |
| 2 | **免费 Web Service 15 分钟无入站流量就休眠**，下次请求**约 1 分钟**冷启动，期间浏览器显示 Render 的加载页 | 老师第一次打开会以为"打不开"，演示前必须预热 | free 文档 § Spinning down on idle |
| 3 | **免费实例的文件系统是临时的**：本地 SQLite 数据会在**重新部署 / 重启 / 休眠**时**全部丢失** | "重启后交易记录还在"这条 M5 验收在免费实例上**必然失败** | free 文档 § Local files lost on redeploy |
| 4 | **免费 Web Service 不能挂 Persistent Disk**；付费盘也只保证"挂载路径下"的数据持久，且会失去零停机部署、无法多实例 | 想靠 SQLite 持久化就必须升级付费实例 | disks 文档 开头与 § Disk limitations |
| 5 | **免费 Postgres 有 30 天有效期**（1 个 workspace 限 1 个、1GB；到期后 14 天宽限，之后连同数据删除） | 够覆盖 6 天课程 + 答辩，但**课程结束约 30 天后会消失** | free 文档 § Free Postgres |

**结论一句话**：① 前端 Static Site / 后端 Web Service ✅ 成立；② 免费实例会休眠（15 分钟无流量，冷启动约 1 分钟）✅；③ 免费实例上本地 SQLite 必丢数据 ✅。

### 4.2 方案对比

| 方案 | 成本 | 数据是否持久 | 改动量 | 是否满足 M5 验收 |
| --- | --- | --- | --- | --- |
| **A. 付费实例 + 1GB 持久盘** | 约 $7/月起 | ✅ 部署/重启不丢 | 加 `disk` 配置，`DATABASE_URL=sqlite:////var/data/playerstock.db` | ✅ |
| **B. 免费 Postgres（✅ 推荐）** | 免费 | ✅ 数据在托管数据库里，重新部署不影响 | `requirements.txt` 加 `psycopg2-binary`，换 `DATABASE_URL`；SQLAlchemy 代码不用改 | ✅ |
| **C. 免费实例 + 本地 SQLite** | 免费 | ❌ 重新部署/重启/休眠即全部丢失 | 零改动（**当前 `render.yaml` 就是这个状态**） | ❌ |

### 4.3 决策（已定）：方案 B —— 免费前后端 + Render 免费 Postgres

> 决策日期：2026-10-17 ｜ 决策人：团队 ｜ 执行人：D

选它的理由：
1. **全免费**，不用为课程作业付费；
2. 30 天有效期覆盖"第 4–5 天部署 → 第 6 天答辩"；
3. 改动最小：SQLAlchemy 代码不用改，只换 `DATABASE_URL` + 一个驱动依赖；
4. 能满足 M5「重新部署后数据仍在」这条验收。

**代码侧已完成的铺垫（不需再做）**：

- [x] `backend/requirements.txt` 加入 `psycopg2-binary`
- [x] `config.py` 自动把 `postgres://` 归一化为 `postgresql://`
- [x] `database.py` 对 Postgres 开启 `pool_pre_ping`
- [x] `main.py` 在 Render 上误用 SQLite 时打警告日志

**仍需人工完成的（详见第 3 节操作手册）**：

- [ ] D：注册 Render、建 Postgres、建两个服务、填环境变量
- [ ] D：把 `DATABASE_URL` 设为 **Internal Database URL**
- [ ] B：实现 `scripts/seed_db.py`，然后用 **External Database URL** 从本地灌种子数据（3.6 节）
- [ ] 全员：第 5 天按第 5 节验收清单逐条打勾

**风险与兜底**：

- Free Postgres **30 天后到期**（到期后 14 天宽限，之后删库）。答辩结束后若老师还要访问，改走方案 A 或用 Neon 免费 Postgres（同样只换 `DATABASE_URL`）。
- 若忘记填 `DATABASE_URL`，代码会静默回落到本地 SQLite → 数据随部署丢失。用 `main.py` 的警告日志 + 3.7 节第 3 条来兜底检查。

### 4.4 免费实例休眠带来的操作要求

| 场景 | 必须做的事 |
| --- | --- |
| 答辩/演示前 | **提前 10–15 分钟**用浏览器打开一次后端 `/api/health` 和前端首页，把服务唤醒 |
| 老师突然访问 | 首次约 1 分钟加载属正常现象；在演示开场或 README 里提前写明，避免被误判为"打不开" |
| 长期无访问 | 休眠期间不消耗每月 750 小时免费额度，但本地 SQLite 数据（方案 C）已丢失 |

### 4.5 当前状态与 TODO

| 项 | 状态 |
| --- | --- |
| 方案选择 | ✅ 已定：方案 B（免费前后端 + 免费 Postgres） |
| 代码侧铺垫 | ✅ 已完成（驱动、URL 归一化、连接探活、误用 SQLite 告警） |
| `render.yaml` | ✅ 已改为 `DATABASE_URL` 由控制台填写（`sync: false`） |
| Render 账号 / 服务 | ⬜ 未创建（D 本人操作） |
| 种子数据落库 | ⬜ 待 B 实现 `scripts/seed_db.py` |
| 实测回填 | ⬜ 第 5 天部署后填：冷启动秒数、重启后数据是否仍在 |

> 提醒：免费实例休眠（15 分钟无流量，冷启动约 1 分钟）→ 演示前 10–15 分钟预热，见 4.4。

## 5. 线上验收清单（必须逐条打勾）

- [ ] `GET https://<backend>/api/health` 返回 `{"status":"ok",...}`
- [ ] 前端页面能打开，且不是白屏
- [ ] 前端成功拉到 `/api/players`（浏览器 Network 无 CORS 报错）
- [ ] 线上完成一次买入：余额减少、持仓增加、流水新增
- [ ] 线上完成一次卖出：余额增加、持仓减少
- [ ] **重新部署一次后端，然后刷新页面**：前面那笔交易和持仓**仍在**（验证持久化）
- [ ] 后端日志无 `当前部署在 Render 上却使用本地 SQLite` 警告（有则说明 `DATABASE_URL` 没生效）
- [ ] Postgres 控制台能看到 `players` / `trades` 等表（表由启动时 `init_db()` 自动创建）
- [ ] 线上点一次 AI 分析，返回合法结构（`source` 为 `llm` 或 `rule_fallback` 均可）
- [ ] 断开/清空 `LLM_API_KEY` 后，交易功能仍可用
- [ ] **演示前预热**：提前 10–15 分钟访问一次 `/api/health`（免费实例会休眠，冷启动约 1 分钟，见 4.4）
- [ ] 记录访问地址与已知问题（见下）

## 6. 访问地址与已知问题

| 项 | 内容 |
| --- | --- |
| 前端地址 | ______ |
| 后端地址 | ______ |
| Swagger 文档 | ______/docs |
| 部署日期 | ______ |
| 已知问题 1 | ______ |
| 已知问题 2 | ______ |

## 7. 常见故障排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 前端报 CORS | `CORS_ORIGINS` 没加前端域名 | 改后重启后端 |
| 前端请求 404 | `VITE_API_BASE_URL` 少了协议或尾部斜杠 | 改成 `https://host`，重新构建 |
| 后端 502 | 启动命令路径错（写成 `main:app`） | 必须是 `uvicorn app.main:app` |
| 后端 import 失败 | 用了 `../core_engine` 这类跨目录 import | 定价/AI 必须在 `backend/` 内 |
| 刷新后数据消失 | 用了临时文件系统 | 挂持久盘或换 PostgreSQL |
| 首次访问很慢（约 1 分钟）或先出现加载页 | 免费实例已休眠（15 分钟无入站流量） | 正常现象，不是故障；演示前预热（见 4.4） |
| 重新部署后交易记录全没了 | 免费实例临时文件系统 + 本地 SQLite | 换免费 Postgres（见 4.3 方案 B），并检查 `DATABASE_URL` 是否生效 |
| 前端子路由刷新 404 | 静态站点缺 SPA 回退 | `render.yaml` 的 `routes: rewrite` |

## 8. 回滚

| 场景 | 操作 |
| --- | --- |
| 新版本后端启动失败 | Render → 该服务 → Deploys → 选上一个成功版本 → Redeploy |
| 前端构建失败 | 同上 |
| 数据库被改坏 | 重新 `python scripts/seed_db.py`（演示数据可重建，但真实交易记录会丢——已告知风险） |

## 9. TODO

- [ ] D 第 4 天：先手工建两个服务跑通一次（不依赖 Blueprint）
- [ ] D 第 5 天：完成第 5 节全部打勾，填第 6 节
- [ ] D 第 6 天：把"重新部署后数据仍在"的截图存进 `docs/acceptance/test_report.md`
