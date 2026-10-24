# 部署说明

> **负责人**：D ｜ **截止**：第 5 天必须完成并验证 ｜ **状态**：🟡 初稿完成，待第 5 天实测后回填
> **对应课程指标**：#7 部署上线、#22 可运行可复现；验收标准不是"网站能打开"，而是"交易完成后数据能保存"

## 1. 部署架构

| 服务 | 平台 | Root Directory | 构建 | 启动 |
| --- | --- | --- | --- | --- |
| 前端 | Render Static Site | `code/frontend` | `npm install && npm run build` | 静态（`dist/`） |
| 后端 | Render Web Service | `code/backend` | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

> `code/core_engine` 通过 `code/backend/app/core/config.py` 里的 `sys.path` 注入被后端导入，**无需单独安装**；如需标准包形式，可在 `code/backend` 下执行 `pip install -e ../core_engine`。

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

- [x] `code/backend/requirements.txt` 已含 `psycopg2-binary`（连 Postgres 的驱动）
- [x] `code/backend/app/core/config.py` 已把 `postgres://` / 裸 `postgresql://` 归一化成 **`postgresql+psycopg2://`**：① 不转 `postgres://` 会报 `Can't load plugin: sqlalchemy.dialects:postgres`；② **SQLAlchemy 2.1 起裸 `postgresql://` 默认驱动是 psycopg 3（包名 `psycopg`）**，而项目只装 `psycopg2-binary`，不显式写驱动会 `ModuleNotFoundError: No module named 'psycopg'` 直接起不来（第 4 天预检实测，`tests/unit/test_config_db_url.py` 6 条守着）
- [x] `code/backend/app/core/database.py` 已对非 SQLite 开启 `pool_pre_ping`（避免空闲后第一个请求连接失效）
- [x] `code/backend/app/main.py` 在 Render 上检测到 SQLite 会打警告日志（防止"数据总丢"查不出原因）
- [x] 灌数命令就绪：`python scripts/bootstrap_demo_data.py`（种子 + 9 轮价格，干净库实测每人 ≥10 点，见 §3.9）
- [ ] 代码已推到 GitHub 并确认 **要部署的分支**（团队用 `develop`，Blueprint 创建时选它）
      ——⚠️ 当前 `develop` 仍有未推送的本地提交，**部署前必须先 push**，否则 Render 拉不到最新代码

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
2. 本地仓库根目录执行（**一条命令**：种子 + 9 轮价格，让每人 ≥10 个价格点）：

   ```powershell
   $env:DATABASE_URL="<External Database URL>"
   python scripts/bootstrap_demo_data.py
   Remove-Item Env:\DATABASE_URL   # 用完清掉，别让本地测试连到线上库
   ```

3. 刷新线上前端 → 能看到 8 名选手、进详情页有 10+ 个价格点即成功
4. 依赖已就绪：`scripts/seed_db.py`（B，第 1 天）、`scripts/update_prices.py`（B，第 3 天）
   均已实现；`bootstrap_demo_data.py`（B，第 4 天）只是把这两步 + C 的 `simulate_match.py`
   串成一条命令。只想补价格不动库时加 `--keep`

### 3.7 最终验证

按第 5 节清单逐条打勾，重点三条：
- [ ] 线上买卖各成功一次
- [ ] **重新部署后端后，交易记录仍在**（证明 Postgres 真的生效）
- [ ] 后端日志里**没有** `当前部署在 Render 上却使用本地 SQLite` 这条警告

### 3.8 第 3 天部署预检（2026-10-24，不部署）

> 目的：第 5 天正式部署前先过一遍代码侧可检查项，避免当天才发现配置缺失。**只做静态检查，没有创建任何 Render 服务。**

| # | 检查项 | 结果 | 说明 / 待办 |
| --- | --- | --- | --- |
| 1 | `render.yaml` 后端：`rootDir: code/backend`、`startCommand: uvicorn app.main:app`、`healthCheckPath: /api/health` | ✅ | 与仓库一致，不是手册里的 `main:app` |
| 2 | `render.yaml` 前端：`rootDir: code/frontend`、`npm install && npm run build`、`staticPublishPath: dist`、SPA rewrite 回退 | ✅ | 等 A 的脚手架生成 `package.json` 后才真正生效 |
| 3 | `DATABASE_URL` 用控制台 `sync: false`，填 Render Postgres 的 Internal Database URL | ✅ | 第 5 天填；忘填会回落本地 SQLite，数据随部署丢失 |
| 4 | `postgres://` 自动归一化、`pool_pre_ping`、Render 上误用 SQLite 的告警日志 | ✅ | 已在 `config.py` / `database.py` / `main.py` 实现。**第 4 天补充**：归一化目标改为 `postgresql+psycopg2://`——SQLAlchemy 2.1 的裸 `postgresql://` 默认用 psycopg 3，不写死驱动会 `ModuleNotFoundError: psycopg`（`test_config_db_url.py` 守卫） |
| 5 | `LLM_API_KEY`、`CORS_ORIGINS` 均为 `sync: false` | ✅ | 第 5 天填；CORS 不填前端会跨域失败 |
| 6 | `.env.example` 字段与 `Settings` 一致（含 `LLM_TIMEOUT_SECONDS=20`） | ✅ | 第 4 天已把注释里"挂载磁盘后改 SQLite"改为"线上必须填 Postgres"并写明驱动归一化，与方案 B 一致 |
| 7 | `requirements.lock.txt` 已入库（B，第 2 天） | ✅ | 部署 build 仍用 `requirements.txt`；锁定文件作为"可复现"证据保留 |
| 8 | 演示数据初始化方式 | ✅ | 免费实例无 Shell → 本地连 **External** URL 跑 `python scripts/bootstrap_demo_data.py` 一条命令（种子 + 9 轮价格 = 每人 ≥10 点，见 §3.6） |
| 9 | 线上验收清单（第 5 节 TC-401~406） | ⬜ | 第 5 天执行 |
| 10 | 前端构建产物（`dist/`） | ✅ | A 的脚手架已入库；第 4 天 B 本地复跑 `npm ci` / `npm run build`（58 modules，exit 0）/ oxlint / eslint / vitest 全绿，CI run #30 前端 job 亦绿（见 `test_report.md` §2.4） |

**预检结论**：**后端代码侧已就绪**，第 5 天可先单独部署后端验证 `/api/health` 与 Postgres 持久化；前端部署与线上全流程验收阻塞在 A 的脚手架（第 3–4 天）与第 5 天的控制台操作。**今天不做任何线上操作。**

### 3.9 第 4 天预检（第二步）：代码侧全部就绪，只差控制台点击

> 2026-10-25，B。§3.8 是"不部署的静态预检"，这一节是把**能提前做的都做完**：
> 灌数配方在干净库上跑通、用真实 API 核到点数、把 4 步操作要填的东西写死。
> ⚠️ **第 1–3 步必须用 Render 账号在浏览器里点**（B 没有账号凭据，无法代做）；
> 第 4 步的命令已经就绪并在干净库验证过，等库建好后照抄即可。

| # | 步骤 | 命令 / 要点 | 状态 |
| --- | --- | --- | --- |
| 1 | **Render 注册 + 建免费 Postgres** | Dashboard → New → Postgres；Name `playerstock-db`；**Region = Singapore**；Plan = Free；建好复制 **Internal Database URL** | ✅ 已建（PG 18，Service ID `dpg-dbe8nvrjlhs73ervmu0-a`，**2026-11-23 到期**） |
| 2 | **Blueprint 导入 `render.yaml`** | New → Blueprint → 选仓库 → **分支选 `develop`** → 自动识别 `playerstock-backend` / `playerstock-frontend` 两个服务 | ✅ 已导入（两服务均 "Blueprint managed"，分支 `develop`，Live） |
| 3 | **填环境变量** | 后端：`DATABASE_URL` = 第 1 步的 Internal URL、`CORS_ORIGINS`、`LLM_API_KEY`（留空 → 自动 `rule_fallback`）；前端：`VITE_API_BASE_URL` = 后端公网域（**构建期注入，改完要重新部署**） | ✅ 已生效（前端能取到数据 = CORS 与 `VITE_API_BASE_URL` 都对；线上无密钥时 `/api/analysis` 返回 `rule_fallback`） |
| 4 | **用 External URL 从本地灌数** | `$env:DATABASE_URL="<External Database URL>"` → `python scripts/bootstrap_demo_data.py` → 刷新线上前端，确认每人 ≥10 个价格点 | ✅ 已灌（线上 `/api/players/1/prices` = **11 点**，8 人价格与本地 `--rounds 9` 逐条一致；见 §6 / `test_report.md` §6） |

**第 4 步的配方在干净库上的实测（2026-10-25，B 本机）**

```powershell
$env:DATABASE_URL = "sqlite:///<一个不存在的文件>"     # 模拟"全新库"
python scripts/bootstrap_demo_data.py                  # 一条命令：种子 + 9 轮价格
```

脚本自检输出（`--min-points 10` 默认值）：

```text
=== 结果核对 ===
  OK #1 ZywOo   11 点  现价 108.75
  OK #2 donk    11 点  现价 131.45
  OK #3 m0NESY  11 点  现价 85.08
  OK #4 NiKo    11 点  现价 58.11
  OK #5 ropz    10 点  现价 127.04
  OK #6 jL      11 点  现价 105.27
  OK #7 sh1ro    2 点  现价 136.50（suspended，按规则不定价）
  OK #8 flameZ  11 点  现价 74.45
  price_history 合计 = 78 条；demo 余额 = 5000.00；持仓 = 0 条；流水 = 0 条
```

再用**真实 uvicorn**（同一个库）走 HTTP 核一遍，证明"10+ 点"不是只写在文档里：

| 接口 | 结果 |
| --- | --- |
| `GET /api/players` | 8 名选手 |
| `GET /api/players/1/prices` | **11 个点**，`ts` 升序（`2026-10-24T08:20:21Z` → `2026-11-09T00:00:00Z`），末点 `108.75` = `current_price`，末点 `reason` 含"得分"与 `S=` |
| 其余 7 人点数 | 11 / 11 / 11 / 10 / 11 / 2 / 11（`ropz` 10、`sh1ro` 2 属预期） |
| `GET /api/health` | `{"status":"ok"}` |

> 这一步只证明"命令在任何空库上都能灌出同样的数"；**线上 Render Postgres 上的一次还没做**
> （要等第 1–3 步建库拿 External URL）。做法与上面完全一致，只是把 `DATABASE_URL` 换成 External URL。

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

- [x] `code/backend/requirements.txt` 加入 `psycopg2-binary`
- [x] `config.py` 自动把 `postgres://` 归一化为 `postgresql://`
- [x] `database.py` 对 Postgres 开启 `pool_pre_ping`
- [x] `main.py` 在 Render 上误用 SQLite 时打警告日志

**仍需人工完成的（详见第 3 节操作手册）**：

- [ ] D：注册 Render、建 Postgres、建两个服务、填环境变量
- [ ] D：把 `DATABASE_URL` 设为 **Internal Database URL**
- [x] B：`scripts/seed_db.py` 与一键灌数脚本 `scripts/bootstrap_demo_data.py` 均已实现并在干净库验证（每人 ≥10 点，见 §3.9）
- [ ] B：等 1–2 完成拿到 **External Database URL** 后，从本地跑一次 `bootstrap_demo_data.py` 灌线上库（3.6 节）
- [ ] B：线上跑一次 `python scripts/smoke_test_api.py --base https://<后端>.onrender.com`（第 5 天线上验收的第 4/6 项证据）
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
| 种子数据落库 | ✅ 脚本就绪：`scripts/bootstrap_demo_data.py`（种子 + 9 轮价格；线上用 External URL 执行） |
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
| 前端地址 | https://playerstock-frontend-mdlk.onrender.com （Static Site，`develop`，已重新部署至最新提交，Live） |
| 后端地址 | https://playerstock-backend-mdlk.onrender.com （Web Service，Python 3 / Free，`develop`，Live） |
| Swagger 文档 | https://playerstock-backend-mdlk.onrender.com/docs |
| 数据库 | Render **PostgreSQL 18**，服务名 `playerstock-db`（Service ID `dpg-dbe8nvrjlhs73ervmu0-a`） |
| 部署日期 | 2026-10-25 首次上线（`render.yaml` Blueprint 创建三服务）；同日 **Manual Deploy 重新部署前后端**，与 `develop` 对齐 |
| 已知问题 1 | **数据库 2026-11-23 到期**（免费库到期即删除）。答辩/验收在此之前完成；若之后还要访问，需在到期前升级付费或迁到 Neon（只改 `DATABASE_URL`） |
| 已知问题 2 | 免费实例会休眠，冷启动约 1 分钟 → **演示前 10–15 分钟预热 `/api/health`**（见 §4.4） |
| 已知问题 3 | CORS 目前是 `access-control-allow-origin: *`（提交 `9abacf9`，重新部署后已实测生效），演示可接受；若要收紧，把 `CORS_ORIGINS` 设为前端域名并把中间件改回按白名单 |
| 已知问题 4 | 线上库有 **3 条流水**（2026-10-25 跑 TC-403 留下：#1 BUY ×2、#2/#3 SELL ×1），余额 5000.00、持仓为空。想彻底清空可重跑 `bootstrap_demo_data.py`（`--reset`） |
| 已知问题 5 | ~~线上落后 3 个提交~~ **已解决**：2026-10-25 重新部署后与 `develop` 对齐（证据：CORS 头为 `*`、前端 bundle 变为 `assets/index-we8cxpp9.js`、重新部署后数据仍在 → TC-404 ✅） |

## 7. 常见故障排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 前端报 CORS | `CORS_ORIGINS` 没加前端域名 | 改后重启后端 |
| 前端请求 404 | `VITE_API_BASE_URL` 少了协议或尾部斜杠 | 改成 `https://host`，重新构建 |
| 后端 502 | 启动命令路径错（写成 `main:app`） | 必须是 `uvicorn app.main:app` |
| 后端 import 失败（`No module named core_engine`） | `code/` 未加入 `sys.path` 或未安装 core_engine | 确认 `code/backend/app/core/config.py` 的 sys.path 注入存在；或执行 `pip install -e ../core_engine` |
| 刷新后数据消失 | 用了临时文件系统 | 挂持久盘或换 PostgreSQL |
| 首次访问很慢（约 1 分钟）或先出现加载页 | 免费实例已休眠（15 分钟无入站流量） | 正常现象，不是故障；演示前预热（见 4.4） |
| 重新部署后交易记录全没了 | 免费实例临时文件系统 + 本地 SQLite | 换免费 Postgres（见 4.3 方案 B），并检查 `DATABASE_URL` 是否生效 |
| 前端子路由刷新 404 | 静态站点缺 SPA 回退 | `render.yaml` 的 `routes: rewrite` |

## 8. 回滚

| 场景 | 操作 |
| --- | --- |
| 新版本后端启动失败 | Render → 该服务 → Deploys → 选上一个成功版本 → Redeploy |
| 前端构建失败 | 同上 |
| 数据库被改坏 | 重新 `python scripts/bootstrap_demo_data.py`（演示数据可重建，但真实交易记录会丢——已告知风险） |

## 9. TODO

- [ ] D 第 4 天：先手工建两个服务跑通一次（不依赖 Blueprint）
- [ ] D 第 5 天：完成第 5 节全部打勾，填第 6 节
- [ ] **B/D 上线前**：把 `app/main.py` 的临时提交 `allow_origins=["*"]`（`9abacf9`）改回 `settings.cors_origin_list`，Render 配 `CORS_ORIGINS` 为前端公网地址（合规与安全要求）
- [ ] D 第 6 天：把"重新部署后数据仍在"的截图存进 `docs/acceptance/test_report.md`
