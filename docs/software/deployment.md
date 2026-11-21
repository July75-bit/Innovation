# 部署与发布文档（Deployment & Release）

> **课程交付物**：《软件创新工程实践》第 5 天「部署发布作品」——部署和发布软件的方法及检查单
> → `docs/software/deployment.md`（课程 PDF 第 5 天 211–217 页、271–278 页）
> **负责人 / 发布负责人**：D ｜ **验证负责人**：D（交叉验证：B）
> **部署源**：GitHub `July75-bit/Innovation` 的 `develop` 分支 ｜ **CI**：GitHub Actions（4 个 job）
> **最后实测**：2026-11-21 11:30（UTC+8）｜ **线上状态**：运行中（`/api/health` 200，冷启动 28.2s；前端首页 200，1.92s）
> **最近一次已验证全绿 CI**：commit `5ae6a4c` → run **#188**，4/4（卫生 / 后端 / 前端 / 交付物）
> **待复核**：`2175d6c` 起答辩稿迁到 `docs/slides/`，交付物检查路径已同步修改；push 后以新的 CI run 为准

---

## 0. 课程要求对照（先看这张表）

| 课程 PDF 要求 | 本文落点 |
| --- | --- |
| 选择适合项目的 Web 应用部署方式 | §1.2 方式对比与决策、§1.3 服务清单 |
| 建立「代码提交 → 生产发布」的标准流程 | §3.1–§3.5、§11 发布记录 |
| 配置构建、环境变量、域名和 HTTPS | §2、§1.4、§1.5 |
| 设计灰度发布、回滚和故障处理方案 | §4.7、§8、§7 |
| 使用上线前、上线中、上线后的检查单 | §5.1–§5.7（A–G 七张单） |
| 健康检查与可观测性 | §4.8、§3.7 |
| 发布完成记录、复盘与回滚路径 | §11、附录 A、§8 |
| 服务器规格、容量与资源边界 | §4.10 |
| 上线前账号、演示数据与密钥处理 | §4.11 |
| 最终发布检查卡（一页版） | §5.9 |
| 参考案例对照（Linux 自建 vs Render 托管） | §1.6 |

**「部署」在本文对应的十步**（PDF 215 页）：获取源码（GitHub `develop`）→ 安装依赖（`pip install` / `npm ci`）→
执行测试（CI 4 个 job）→ 构建软件包（`npm run build` → `dist/`）→ 配置运行环境（Render 环境变量）→
发布到云平台（Render Blueprint）→ 配置域名和网络（`*.onrender.com` + HTTPS + CORS）→ 执行健康检查
（`/api/health`）→ 监控运行状态（Render Logs / 业务探针）→ 必要时回滚（§8）。

---

## 1. 部署架构与方式选型

### 1.1 系统组成

```
用户浏览器
   │  HTTPS（Render 自动签发证书）
   ▼
Render Static Site（playerstock-frontend）
   │  dist/ 静态资源 + SPA History Fallback（/* → /index.html）
   │  跨域请求 VITE_API_BASE_URL/api/*
   ▼
Render Web Service（playerstock-backend，Singapore）
   │  FastAPI + uvicorn，健康检查 /api/health
   ├──► Render Postgres（playerstock-db，持久化：账户/持仓/流水/价格/AI 审计）
   └──► DeepSeek API（/api/analysis、/api/agent/*；无密钥/超时自动规则兜底）

Render Cron（playerstock-agent-patrol，*/10 0-15 * * *）
   └──► 定时打后端只读接口 + 按需刷新简报（兼作免费实例保温）
```

### 1.2 部署方式对比与决策

| 方式 | 适用场景 | 本项目结论 |
| --- | --- | --- |
| 静态托管（Static Site） | Vue/Vite SPA、文档站 | ✅ **前端采用**：Render Static Site，构建产物 `dist/`，SPA 回退 |
| PaaS（托管应用） | 快速上线、团队小 | ✅ **后端采用**：Render Web Service（Python），Blueprint 管理配置 |
| 托管数据库 | 需要持久化 | ✅ **采用**：Render Postgres（免费实例，30 天到期需留意） |
| 虚拟机（VM） | 单体、需完全控制 OS | ❌ 不采用：课程周期短，运维成本高，免费额度不需要 |
| Docker / Kubernetes | 环境一致、弹性扩缩容 | ❌ 不采用：单服务规模小、免费档无容器编排收益；Dockerfile 会增加构建链复杂度 |
| Serverless | 事件驱动、低频接口 | ❌ 不采用：交易/持仓是常驻状态型服务，冷启动与运行时限制不适合 |

**决策理由（一句话）**：前端天然是静态 SPA，后端是单实例 FastAPI + 托管 Postgres，PaaS + 静态托管是
成本最低、上线最快、回滚最简单的组合；课程要求考察的是「能否把发布流程做标准」，而不是堆基础设施。

**必须知道的限制（免费档）**：

- Web Service 闲置约 15 分钟休眠，冷启动实测 **约 30–60 秒**（线上首次 `/api/players` TTFB 曾测到 **33.6s**）；
- 内存/CPU 很小（0.1 vCPU 级别），压力测试饱和约 38 req/s；
- 免费 Postgres **30 天到期**（约 2026-11-23，到期前需升级或迁移）；
- 免费实例**无 Shell / one-off job**，数据初始化要连 External Database URL 从本地执行（§3.6）。

### 1.3 服务清单（`render.yaml` 为准）

| 服务名 | 类型 | Plan/Region | Root Directory | 构建 | 启动 / 发布 |
| --- | --- | --- | --- | --- | --- |
| `playerstock-frontend` | Static Site | Free / Singapore | `code/frontend` | `npm install && npm run build` | `dist/`；路由 `/* → /index.html` |
| `playerstock-backend` | Web Service | Free / Singapore | `code/backend` | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT`；健康检查 `/api/health` |
| `playerstock-db` | Postgres | Free / Singapore | — | — | 提供 Internal / External Database URL |
| `playerstock-agent-patrol` | Cron | Free / Singapore | 仓库根 | 无需构建（标准库脚本） | `python scripts/agent_patrol.py`；`*/10 0-15 * * *` |

> 首次部署可在 Render 控制台 **New → Blueprint** 选择本仓库，自动读取 `render.yaml` 创建以上服务。

### 1.4 域名、HTTPS、跨域与路由

- **HTTPS**：Render 为 `*.onrender.com` 自动签发/续期证书；本项目未使用自定义域名。
- **前端路由**：Static Site 配置 rewrite `/* → /index.html`，保证刷新 `/players/1`、`/me` 等 SPA 路由不 404；
  API 404 与未知路径由前端 `NotFoundView` 兜底展示（标题「页面不存在」）。
- **跨域（CORS）**：后端 `CORS_ORIGINS` 必须精确等于前端 origin（例：`https://playerstock-frontend-mdlk.onrender.com`）。
  代码会去掉首尾空白与**结尾斜杠**（浏览器 Origin 不带 `/`，差一个斜杠就整站跨域失败）。
- **环境变量注入**：前端 `VITE_*` 是**构建期**打包进浏览器的，改了必须重新构建部署；后端密钥只放在 Render Environment。

### 1.5 自定义域名（可选，本项目未启用）

1. Render 服务 → Settings → Custom Domain → 添加 `stock.example.com`
2. 在 DNS 服务商添加 Render 给出的 CNAME（或 A/ALIAS）记录
3. Render 自动申请 Let's Encrypt 证书（约 1–5 分钟），HTTPS 强制跳转
4. 同步修改前端 `VITE_API_BASE_URL`、后端 `CORS_ORIGINS` 为新域名后重新部署
> 课程演示使用 `*.onrender.com` 已满足 HTTPS 与可访问性，未申请域名以免引入额外不确定性。

### 1.6 参考部署案例对照（WindOnMAgent / Linux 云服务器）

参考案例：<https://github.com/bettermorn/AIAgent/blob/main/code/IndustryAgent/WindOnMAgent/deployment.md>
（FastAPI + 原生 JS + PostgreSQL，部署到 Ubuntu 22.04 / Debian 12 云服务器，使用 Nginx + systemd + certbot）。
本项目按课程「6 天上线 + 免费额度」约束选择 Render 托管；两者的检查单思想一致，但基础设施不同：

| 维度 | 参考案例（Linux 自建） | 本项目（Render 托管） | 本项目处理 |
| --- | --- | --- | --- |
| 运行环境 | Ubuntu 22.04/24 + Nginx + systemd + uvicorn | Render Static Site + Web Service + Cron + Postgres | 不引入 Nginx/systemd；平台托管进程与证书 |
| 前端 | 原生 JS 静态文件由后端直接托管 | Vue 3 SPA，独立 Static Site + SPA fallback | 前后端分离，前端构建产物 `dist/` |
| 数据库 | 同机 PostgreSQL 14+，手工备份 | Render 托管 Postgres（免费 30 天） | 迁移到托管库，避免临时盘丢数据 |
| HTTPS | certbot + ufw + 安全组 | Render 自动签发 `*.onrender.com` 证书 | 不配置 certbot；域名/证书由平台负责 |
| 配置 | `/etc/windom/windom.env`（640） | Render Environment（秘密 `sync: false`） | 密钥只在控制台，不进仓库 |
| 健康检查 | `/health` 存活 + `/ready` 就绪 | `/api/health`（覆盖依赖探测） | 未单独提供 `/ready`，见 §5.5 N/A 说明 |
| 进程模型 | `uvicorn --workers 1`，避免进程内状态分裂 | 免费档单实例，天然 1 worker | 不涉及多 worker 粘性会话问题 |
| 运维入口 | `systemctl` / `journalctl` / `nginx -t` | Render Dashboard（Logs/Metrics/Deploys） | 用平台日志与部署历史 |
| 适用场景 | 需完全控制 OS、内网/离线、长期自建 | 课程 6 天、免费额度、快速回滚 | 本项目选 Render |

**吸收进本文的内容**：部署架构图（§1.1）、容量与资源边界（§4.10）、上线前账号与数据处理（§4.11）、
一页版最终发布检查卡（§5.9）；参考案例中的 A–G 检查单与回滚思路已体现在 §5、§8。
**明确不照搬**：Nginx/SSE/WebSocket 配置、systemd 托管、certbot、Linux 用户与目录权限——本项目由 Render 托管，
这些组件不存在；如未来改为自建 Linux，可按参考案例补回，但需要重新验证前端静态托管与 CORS。

---

## 2. 环境与配置

### 2.1 环境分层

| 环境 | 前端 | 后端 | 数据库 | 用途 |
| --- | --- | --- | --- | --- |
| 本地开发 | `npm run dev`（Vite） | `uvicorn --reload` | SQLite `code/backend/playerstock.db` | 日常开发、单测、截图 |
| CI（GitHub Actions） | `npm ci` + lint + vitest + build | Python 3.12 + ruff + pytest（临时 SQLite） | 每用例独立临时库 | 合并门禁 |
| 生产（Render） | Static Site（HTTPS） | Web Service（HTTPS） | Render Postgres | 课程验收 / 答辩演示 |

### 2.2 后端环境变量（Render → Environment）

| 变量 | 值 / 说明 | 密钥 |
| --- | --- | --- |
| `PYTHON_VERSION` | `3.12.6`（与 `render.yaml`、CI 对齐） | 否 |
| `DATABASE_URL` | Postgres **Internal Database URL**（`postgresql://…`；代码自动补 `+psycopg2`） | ✅ 是 |
| `CORS_ORIGINS` | 前端公网 origin，多个用英文逗号分隔 | 否 |
| `DEBUG_ENDPOINTS` | 验收期 `1`（`/api/debug/db` 可截图）；**验收完成后建议 `0`** | 否 |
| `RESEED_TOKEN` | `POST /api/debug/reseed` 的口令，线上必须覆盖默认值 | ✅ 是 |
| `LLM_PROVIDER` / `LLM_MODEL` | 当前线上：`openai` 兼容协议 / `deepseek-flash` | 否 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1`（代码会补全 `/chat/completions`） | 否 |
| `LLM_API_KEY` | 模型密钥（只留在后端，**绝不下发前端**） | ✅ 是 |
| `LLM_TIMEOUT_SECONDS` | `20`（超时/失败自动回落 `source=rule_fallback`，接口仍 200） | 否 |
| `INITIAL_BALANCE` / `MAX_POSITION_PER_PLAYER` | `5000` / `50` | 否 |
| `PRICING_ALPHA` / `BETA` / `FLOOR` | `0.15` / `0.0` / `1.0` | 否 |

> ✅ `render.yaml` 已于 2026-11-21 同步为 DeepSeek 配置（`LLM_MODEL=deepseek-flash` +
> `LLM_BASE_URL=https://api.deepseek.com/v1`，`LLM_API_KEY` 仍由控制台填写）；`code/backend/.env.example` 同口径。
> 密钥类变量全部 `sync: false`，由控制台填写，不进入仓库、不写进日志。

### 2.3 前端环境变量（Render Static Site → Environment，构建期）

| 变量 | 值 | 说明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `https://playerstock-backend-mdlk.onrender.com`（**不要带尾斜杠 / 不要写 127.0.0.1**） | 构建时注入，改完必须重新部署 |
| `VITE_USE_MOCK` | `false` | `true` 时走 `src/mock` 假数据，仅用于后端未就绪的开发阶段 |

> 前端变量会被打包进浏览器 JS：**任何密钥都不能放进 `VITE_*`**。

### 2.4 构建配置

- **前端**：Node 24（CI 与 `package.json` engines 对齐，jsdom 要求 ^22.22.2 || ^24.15.0 || >=26）；
  `npm ci`（必须提交 `package-lock.json`）→ `npm run lint` → `npm run test:unit -- --run` → `npm run build`。
  输出 `dist/`（`index.html` + 带内容哈希的 `assets/*`）。
- **后端**：Python 3.12，`pip install -r code/backend/requirements.txt`（含 `psycopg2-binary`）；
  启动入口是 `app.main:app`；ORM `create_all` 自动建表。
- **本地环境文件**：`code/backend/.env.example` → `.env`；前端 `code/frontend/.env.example` →
  `.env.local`（均已被 `.gitignore` 忽略）。

---

## 3. 部署与发布流程

### 3.1 触发方式与分支纪律

- **日常提交**：只推 `develop`（Render 部署源）；`main` 仅历史 PR，不作为部署分支。
- **CI 触发**：`push` / `pull_request` / `workflow_dispatch`，配置在 `.github/workflows/ci.yml`。
- **Render 自动部署**：Blueprint 默认对 `develop` 开启 Auto-Deploy；推送并通过（或并行于）CI 后触发新部署。
  > 免费档没有「等 CI 绿了再部署」的门禁，**发布纪律 = 本地与 CI 都绿才 push**。
- 提交前必查冲突标记：`git grep -n -E "^(<<<<<<< |>>>>>>> )"`（CI 的 hygiene job 也会拦）。

### 3.2 CI 门禁（4 个 job，全绿才可发布）

| Job | 关键命令 | 失败含义 |
| --- | --- | --- |
| 仓库卫生（冲突标记） | `git grep -n -E "^(<<<<<<< \|>>>>>>> )"` | 解冲突时把标记提交了（历史事故 ×2） |
| 后端测试（pytest） | `ruff check --select E4,E7,E9,F,C901 …` → `python -m pytest` | 圈复杂度/未用导入/单测失败；**ruff 在 pytest 之前** |
| 前端检查 | `npm run lint` → `npm run test:unit -- --run` → `npm run build` | eslint/vitest/vue-tsc 失败 |
| 交付物完整性 | 文档、证据、`defense.pdf` 存在且非空 | 误删交付物 |

### 3.3 构建制品与版本标识

- **版本号**：`develop` 的 **Git Commit SHA**（`git rev-parse --short HEAD`）+ Render Deploy ID。
- **前端制品**：`dist/`，资源文件名带内容哈希（可长期缓存；`index.html` 不设长缓存）。
- **后端制品**：Git 源码 + `requirements.txt`（无二进制制品），Render 每次按 commit 重建。
- **可复现**：同 commit + 同环境变量 → 同构建结果；数据用 `bootstrap_demo_data.py` 固定 seed 复现。

### 3.4 首次部署（从零到可访问，约 30–45 分钟）

> 顺序不能乱：**先建库 → 再建后端（粘库地址）→ 再建前端（粘后端地址）→ 回填 CORS**。

1. Render 登录并授权读取 `July75-bit/Innovation`。
2. 创建 Postgres：Name `playerstock-db`，Region **Singapore**，Plan **Free**；复制 **Internal Database URL**。
3. New → **Blueprint** → 选择仓库与 `develop` 分支 → 自动创建 3 个服务；后端填写：
   `DATABASE_URL`（Internal）、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`CORS_ORIGINS` 先留空。
4. 等后端 Deploy 成功 → 打开 `https://<后端>/api/health`，返回
   `{"status":"ok","service":"playerstock-backend"}`。
5. 前端填写 `VITE_API_BASE_URL` = 后端公网地址（无尾斜杠）→ Deploy → 打开前端能加载。
6. 回填后端 `CORS_ORIGINS` = 前端 origin → 保存触发重新部署 → 前端 Network 中 `/api/players` 无 CORS 错误。
7. 初始化演示数据（见 §3.6）→ 按 §5 检查单验收。

### 3.5 日常发布步骤（每次改代码）

1. 本地：`git status` 干净 → 跑通与 CI 同款门禁（`npm run lint` / `npm run test:unit -- --run` /
   `npm run build`；后端 `ruff …` + `python -m pytest`）。
2. `git commit` → 由**发布负责人** `git push origin develop`。
3. 打开 GitHub Actions 看 4 个 job（约 1–2 分钟）；红则修，不修不发布。
4. Render → 对应服务 → Deploys 看新部署 `Live`；失败看 Logs。
5. 执行 §3.7 冒烟（health + players + 前端首页 + 登录/交易一条链路）。
6. 填写 §11 发布记录（时间、commit、CI run、部署 ID、验证人、回滚点）。

### 3.6 数据初始化 / 重建（免费实例无 Shell）

```bash
# 本地仓库根目录；External Database URL 只在一次性环境变量里用，不落盘、不进 commit
export DATABASE_URL="<External Database URL>"        # Windows PowerShell: $env:DATABASE_URL="..."
python scripts/bootstrap_demo_data.py                # 清库重建：16 名选手 + 演示账户 + 价格历史
unset DATABASE_URL                                   # 用完清掉，避免本地测试误连线上库
```

- 只想补价格不动库：`python scripts/bootstrap_demo_data.py --keep`
- 线上内网重灌（可选，需 `DEBUG_ENDPOINTS=1` + `RESEED_TOKEN`）：
  `curl -X POST "https://<后端>/api/debug/reseed?token=<RESEED_TOKEN>"`（会重置演示数据，不碰他人账号）
- 验证数据：浏览器打开 `https://<后端>/api/debug/db`，确认 `是否 SQLite: false`、表行数非空。

### 3.7 发布后冒烟（必须执行）

```bash
# 1) 健康检查
curl -fsS https://playerstock-backend-mdlk.onrender.com/api/health
# 2) 只读核心接口（首次可能冷启动，给 60s）
curl -fsS https://playerstock-backend-mdlk.onrender.com/api/players | head -c 200
curl -fsS "https://playerstock-backend-mdlk.onrender.com/api/players/1/prices" | head -c 200
# 3) 前端首页 + SPA 路由刷新
curl -fsS -o /dev/null -w "%{http_code}\n" https://playerstock-frontend-mdlk.onrender.com/
curl -fsS -o /dev/null -w "%{http_code}\n" https://playerstock-frontend-mdlk.onrender.com/me
# 4) 只读联调脚本（不产生交易）
python scripts/smoke_test_api.py --base https://playerstock-backend-mdlk.onrender.com --read-only
```

浏览器侧还要人工确认：首页卡片、详情页图表 + AI 建议、登录/退出、买入→持仓→流水、移动端 4 Tab 与头像。

### 3.8 第 3 天部署预检（2026-10-24，历史记录）

只做静态检查、未创建服务：复核 `render.yaml` 的 rootDir/startCommand、`.env.example`、`DATABASE_URL` 与 CORS
控制台项、SQLite 误用告警；结论是「代码侧就绪，等第 5 天控制台点击」。

### 3.9 第 4 天预检（历史记录）

重点验证 Postgres 连接串归一化（`postgres://` / 裸 `postgresql://` → `postgresql+psycopg2://`，
否则 `ModuleNotFoundError: psycopg`）、`pool_pre_ping`、CI 门禁；预检清单已并入 §5。

### 3.10 演示前预热（必须做）

免费实例会休眠，**答辩/验收前 10–15 分钟**执行：

```bash
python scripts/prewarm.py --base https://playerstock-backend-mdlk.onrender.com
```

脚本会叫醒实例并逐个探活关键接口；配合保温 cron（§4.6），白天通常已处于热态。

### 3.11 发布纪律（课程要求「发布流程」）

- **发布负责人**：D；**验证负责人**：D + B 交叉；**发布窗口**：白天（避免半夜冷启动影响演示）。
- **一次发布只做一件事**：功能 / 修复 / 文档分开提交，便于回滚。
- **发布前**：CI 绿 + §5.1–5.5 检查单；**发布后**：§5.6–5.7 检查单 + 发布记录。
- **红线**：不把密钥写进仓库/日志；不绕过 `DATABASE_URL` 用 SQLite 上生产；不在线上买卖真实资金（本作品只用信用点）。

---

## 4. 数据持久化、灰度、监控与回滚保障

### 4.1 平台事实（决定了方案）

- Render Web Service 的文件系统是**临时**的：重新部署/重启/休眠唤醒会丢本地 SQLite 文件；
- 免费实例不能挂持久磁盘（Persistent Disk 仅付费档）；
- 免费 Postgres 提供独立持久化（但有 30 天到期限制）；
- 免费实例无 Shell，种子/迁移只能从本地连 **External URL** 执行，或走内网 `reseed` 接口。

### 4.2 方案对比

| 方案 | 持久化 | 成本 | 结论 |
| --- | --- | --- | --- |
| 继续 SQLite + 本地文件 | ❌ 部署即丢 | 0 | 不可接受 |
| SQLite + 付费 Persistent Disk | ✅ | 付费 | 备选，但单盘单实例、扩容麻烦 |
| **托管 Postgres（Render）** | ✅ | 免费 30 天 | ✅ **已采用**（代码零改动，SQLAlchemy 双环境） |
| 外部托管数据库（Supabase 等） | ✅ | 免费档有限 | 备选，作为 Postgres 到期后的迁移方向 |

### 4.3 已落地的持久化保障

- `app/core/config.py` 把 Render 的 `postgres://` / 裸 `postgresql://` 统一补成 `postgresql+psycopg2://`
  （SQLAlchemy 2.1 默认驱动变更的坑，有 6 条单测守着）；
- 非 SQLite 连接启用 `pool_pre_ping`，避免空闲后第一个请求拿到失效连接；
- 启动时若检测到「Render 环境 + SQLite」会打警告日志（防「数据总丢」查不出原因）。

### 4.4 免费实例休眠与操作要求

- 闲置约 **15 分钟**休眠，冷启动 **约 30–60 秒**（曾实测首个请求 33.6s）；
- 影响：用户第一次打开可能等几十秒 → 前端有骨架屏 + 慢加载提示（>4s 提示「服务可能在唤醒中」）；
- 对策：保温 cron（§4.6）+ 演示前 `prewarm.py`（§3.10）+ GET 自动重试一次（前端已实现）。

### 4.5 当前运维状态与待办

- Postgres 免费实例 **约 2026-11-23 到期**：到期前升级付费或迁移到备用库；
- `DEBUG_ENDPOINTS` 验收期开着（`/api/debug/db` 截图用），验收完成后关掉；
- `RESEED_TOKEN` 线上已覆盖默认值（默认值仅课程演示用）；
- `render.yaml` 的 LLM 配置（`LLM_MODEL=deepseek-flash`、`LLM_BASE_URL=https://api.deepseek.com/v1`）
  已在 2026-11-21 与线上控制台同步；`LLM_PROVIDER` 仅作标识，不参与请求路由。

### 4.6 保温 cron（免费实例）

```yaml
schedule: "*/10 0-15 * * *"   # UTC 0–15 点 = 北京 08:00–23:59，每 10 分钟一次
startCommand: python scripts/agent_patrol.py
```

- 目的：让后端在工作时间保持热态（巡检本身是一次 HTTP 请求），并顺带刷新简报；
- 简报刷新策略：**仅当简报超过 30 分钟才刷新**（避免每 10 分钟烧 LLM），冷启动超时放宽到 90s；
- 额度：约 16h/天 ≈ **496h/月**，免费 750h/月内；夜间仍可能冷启动（前端有提示兜底）。

### 4.7 灰度发布与发布策略（课程要求）

**现状（诚实说明）**：Render 免费档**不支持 Preview Environments、流量切分或金丝雀**；本项目为单实例
免费服务，故**未实际启用灰度**，采用「单生产环境 + 快速回滚 + 发布后观察」的降级策略。

若后续需要灰度，建议方案（按成本从低到高）：

1. **付费 Preview Environment**：每个 PR 自动起独立环境，验收后再合入 `develop` → 生产部署；
2. **双服务 + 流量切换**：`backend-blue` / `backend-green` 两个服务，前端通过环境变量指到当前生产；
   切换 = 改前端 `VITE_API_BASE_URL` 重新部署（或 Cloudflare Worker 按 Header/比例分流）；
3. **CDN/边缘分流**：Cloudflare 按 Cookie/百分比把少量流量导到新前端，观察 5xx 与前端错误后再全量。

**灰度观察指标**（若启用）：`/api/health` 失败率、5xx 比例、P95 延迟、前端 console error、核心交易链路成功率。
**当前替代**：发布窗口选白天、发布后 10 分钟内人工验证 §5.6，异常立即按 §8 回滚。

### 4.8 监控与可观测性

| 层级 | 手段 | 频率 / 阈值 |
| --- | --- | --- |
| 存活 | Render 健康检查 `/api/health`（Blueprint `healthCheckPath`） | 失败 → Render 重启/标记异常 |
| 业务健康 | `/api/players`、`/api/players/{id}/prices`、`/api/account` | 发布后立即；全量 200 且 JSON 可解析 |
| 数据健康 | `GET /api/debug/db`（方言/表行数） | 发布后；`是否 SQLite: false` 且行数非空 |
| AI 健康 | `/api/analysis/1` 的 `source`（`llm` / `rule_fallback`） | 允许 `rule_fallback`（降级不是故障） |
| 简报新鲜度 | `/api/agent/brief` 的 `generated_at` / `source` | 超过 30 分钟视为巡检异常 |
| 平台指标 | Render Dashboard → Metrics（CPU/内存）、Logs | 发布后观察 10 分钟；5xx 明显升高即回滚 |
| 前端 | 浏览器 console、Network 失败请求 | 发布后人工检查；严重错误即回滚 |
| CI | GitHub Actions 4 个 job | 每次 push；红则不发布 |

> 免费档没有自定义告警通道；课程演示的「告警」= 发布后人工检查 + cron 简报新鲜度 + Render 服务状态页。

### 4.9 备份与恢复

- 免费 Postgres 的自动备份能力有限（**以 Render 控制台实际为准**）；发布前如涉及数据变更，先手工备份：

```bash
# 用 External Database URL（只作一次性环境变量）
pg_dump "<External Database URL>" --no-owner --no-privileges -f backup_$(date +%Y%m%d_%H%M).sql
# 恢复（谨慎！先确认目标库）
psql "<External Database URL>" -f backup_YYYYmmdd_HHMM.sql
```

- **演示数据**本身可重建：`python scripts/bootstrap_demo_data.py`（固定 seed，16 人 / 演示账户 / 价格历史）。
- 恢复演练：至少验证一次「备份文件能导入临时库并起服务」，记录到 §11 发布记录或附录 A。

### 4.10 服务器规格、容量与资源边界

参考案例给出了服务器的 CPU/内存/磁盘建议；本项目使用 Render 托管，资源边界如下（以 Render 控制台实际为准）：

| 资源 | 配置 / 限制 | 实测或结论 |
| --- | --- | --- |
| Web Service | 免费档，约 **0.1 vCPU**；单实例 | 只读压测饱和 **~38 req/s**，约 **190 人同时在线**、0 错误；瓶颈是 CPU 而非代码 |
| 内存 | 免费档小内存（以控制台为准） | 空闲/处理请求的内存峰值在 Render Metrics 观察；无深度学习框架，常驻开销低 |
| 磁盘 | Web Service 文件系统**临时**，不能放 SQLite/上传文件 | 业务数据全部进 Postgres；前端静态资源在 Static Site |
| Static Site | 免费、全球 CDN、HTTPS | 首页 TTFB 暖态约 **1.1s**（含 DNS/TLS）；构建产物 `dist/` |
| Postgres | 免费实例，**30 天到期（约 2026-11-23）** | 9 张表；演示数据可重建；到期前必须升级/迁移并 `pg_dump` |
| Cron | 免费，`*/10 0-15 * * *` | 约 16h/天 ≈ **496h/月**，在免费 750h 额度内 |
| 冷启动 | 闲置 15 分钟休眠 | 冷启动 **30–60s**（首次 `/api/players` 曾实测 **33.6s**）；暖态 API **0.88s** |
| AI 延迟 | DeepSeek API 外部依赖 | 线上中位 **~2.0–2.5s**；L4 评测 P95 **3.39s**（门禁 10s） |

**容量结论**：当前配置满足课程演示与 ~200 人只读访问；需要更高并发时优先升级 Render plan / 增加实例，
而不是改业务代码。数据库容量与连接数在 Render Postgres 控制台查看；免费档不做连接池压测。

### 4.11 上线前账号、演示数据与密钥处理

参考案例把「演示账号口令/演示数据」单列一节；本项目对应处理如下（每次答辩/发布前执行）：

| 项 | 操作 | 验收 |
| --- | --- | --- |
| 演示数据重置 | `DATABASE_URL="<External URL>" python scripts/bootstrap_demo_data.py` | 16 名选手、8 支战队、11 个价格点、演示账户 5000 信用点 / 0 持仓 / 0 流水 |
| 注册账号保护 | `bootstrap_demo_data.py` 不重置私人账号（BUG-15 已修） | 重新灌数据后私人账号仍可登录、余额不被覆盖 |
| LLM 密钥 | Render Environment `LLM_API_KEY`（`sync: false`），不写仓库/日志 | `/api/analysis/1` 返回 `source=llm`；删掉 Key 时自动 `rule_fallback` 且仍 200 |
| LLM 端点/模型 | `LLM_BASE_URL=https://api.deepseek.com/v1`、`LLM_MODEL=deepseek-flash` | `/api/debug` 或启动日志不打印 Key；请求走 DeepSeek |
| 调试接口 | 验收期 `DEBUG_ENDPOINTS=1`，验收完成后改 `0` 并重新部署 | `/api/debug/*` 关闭后返回 404/403（按实现），业务不受影响 |
| 重灌令牌 | `RESEED_TOKEN` 使用随机值，不用示例默认值 | 未带令牌的 `reseed` 请求被拒绝 |
| 数据库到期 | 到期前 `pg_dump` 导出 + 迁移到新库/付费档；恢复后跑冒烟 | 新库 `/api/debug/db` 方言 `postgresql`、players=16，交易记录可读 |
| 合规声明 | README、页面、演示开场声明「纯信用点、不可充值/提现/兑换、非官方、不构成投资建议」 | 演示时主动说明，避免被误认为真钱产品 |

> 参考案例的「演示口令只在首次 seed 生效」提醒同样适用：本项目演示账户是公共账户；私人注册账号的口令由
> PBKDF2 哈希存储，重灌演示数据不会改私人账号口令。

---

## 5. 上线检查单（A–G，按课程 PDF 271–277 页）

> 用法：每次发布复制一份到 §11 或 Issue；`[x]` 表示本次已确认，`N/A` 表示本项目无此组件（附原因）。
> 当前状态基于 **2026-11-21** 的线上实测；CI 全绿基线为 commit `5ae6a4c`（run #188），`2175d6c` 起的交付物路径迁移已在 CI 中同步。

### 5.1 A. 发布准备检查单

**版本和范围**

- [x] 已确认发布版本号：`develop` commit SHA（记录在 §11）
- [x] 已确认发布内容和需求范围（本次：手机端导航简化 + 移除展示组件 + 部署文档）
- [x] 已关联 Issue / 需求 / 变更单（GitHub Issues / commit message）
- [x] 已完成代码评审（课程要求：`docs/software/code_review.md` 记录；小团队互审）
- [x] 已明确发布负责人（D）与验证负责人（D + B）
- [x] 已确认发布窗口（白天，避开演示前 1 小时做大改动）
- [x] 已通知相关团队（4 人小组群/Issue 评论）

**代码和构建**

- [x] 已通过代码格式/静态检查：`npm run lint` + 后端 `ruff check --select E4,E7,E9,F,C901`
- [x] 已通过单元测试：前端 `npm run test:unit -- --run`、后端 `python -m pytest`
- [x] 已通过集成/接口测试（`scripts/smoke_test_api.py`、`tests/integration/`）
- [x] 已完成生产构建：`npm run build`（`dist/`）与后端依赖安装
- [x] 构建制品具备唯一标识：commit SHA + Render Deploy ID
- [x] 已记录 Git Commit SHA
- [x] 依赖漏洞扫描：`pip-audit -r code/backend/requirements.txt` → **No known vulnerabilities found**（2026-11-21 本机，pip-audit 2.10.1）；前端 `npm audit` 需先安装依赖，未跑（已知限制）
- [x] 已验证构建产物完整性：`dist/index.html` + `assets/` 存在、CI build 绿

### 5.2 B. 配置检查单

- [x] 运行环境为 production（Render 环境变量，不是本地 `.env`）
- [x] 生产 API 地址正确：前端 `VITE_API_BASE_URL` → 后端公网 origin（无尾斜杠）
- [x] 数据库连接配置正确：Postgres Internal URL；`/api/debug/db` 显示非 SQLite
- N/A 缓存连接配置：本项目未使用 Redis/缓存服务
- N/A 对象存储配置：选手图标为仓库内静态资源，无上传功能
- [x] 第三方服务配置：DeepSeek API（`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`），无密钥时自动规则兜底
- [x] CORS 配置正确：`CORS_ORIGINS` 精确匹配前端 origin
- N/A Cookie / 域名配置：本项目用不透明 Bearer Token（localStorage），无跨站 Cookie
- [x] 功能开关：`VITE_USE_MOCK=false`；`DEBUG_ENDPOINTS` 验收期 1 / 验收后 0
- [x] 密钥来自安全存储：Render Environment（`sync: false`），未提交仓库
- [x] 未在日志中输出敏感信息（日志只打状态与错误摘要）
- [x] 时区与时间格式：后端 UTC（`utcnow`），前端按本地时区展示

### 5.3 C. 数据库检查单

- [x] 已完成数据库备份：**N/A** —— Render 免费档 Postgres 不提供备份/恢复能力；本项目日常发布不改 schema，数据靠 `bootstrap_demo_data.py` 可重建（已记录为已知限制）
- [x] 已验证备份可恢复：**N/A** —— 同上；替代方案是用 `bootstrap_demo_data.py --rounds 12` 在临时库 10 秒重建（`tests/integration/test_bootstrap_demo_data.py` 覆盖）
- [x] 已确认迁移脚本版本：本项目**无 Alembic 迁移框架**，用 SQLAlchemy `create_all` + `bootstrap` 脚本（见 §4.3/§9）
- [x] 已在测试环境执行迁移：CI 每个用例独立临时库跑全量建表
- [x] 已评估迁移执行时间：当前 schema 小，建表 <1s
- [x] 已确认新旧代码兼容：schema 不变；如变更字段需先备份并「加字段兼容 → 部署 → 清理」
- [x] 已确认数据回滚/补偿方案：演示数据可重建；真实数据从备份恢复
- [x] 已确认迁移失败处理方式：停止发布 → 回滚代码 → 恢复备份/重灌演示数据
- [x] 已安排必要人工审批：发布负责人 + 验证负责人确认

### 5.4 D. 基础设施检查单

- [x] 服务器/实例资源充足：Render 免费实例（0.1 vCPU 级别）满足课程演示；压测饱和约 38 req/s
- [x] CPU / 内存 / 磁盘正常：Render Metrics 查看
- [x] 网络与安全组配置正确：Render 托管，无需自管安全组
- [x] 域名 DNS 解析正确：使用 `*.onrender.com`（未自定义域名）
- [x] HTTPS 证书有效：Render 自动签发
- N/A CDN 配置：Render Static Site 自带边缘缓存，未单独接 CDN
- N/A WAF 规则：免费档未启用 WAF
- [x] 健康检查正常：Blueprint `healthCheckPath=/api/health`
- N/A 负载均衡：单实例，无 LB
- [x] 备份策略：演示数据可重建 + 手工 `pg_dump`（见 §4.9）
- [x] 日志采集正常：Render Logs 可查
- [x] 监控和告警正常：健康检查 + 业务探针（免费档无自定义告警，见 §4.8）
- [x] 时间同步正常：后端统一 UTC

### 5.5 E. 发布执行检查单

- [x] 已打开发布记录（§11 表格）
- [x] 已确认当前线上版本（Render Deploys 上一版本）
- [x] 已确认当前健康状态（发布前 `/api/health` 200）
- [x] 已保存关键监控基线（响应时间、内存、5xx 比例）
- [x] 已部署新版本制品（Render Auto-Deploy）
- [x] 已执行数据库迁移：无 schema 变更（如有则按 §5.3）
- [x] 已检查进程状态：Render 服务状态 `Live`
- [x] 已检查 `/health`：200 且 JSON 正确
- N/A `/ready`：本项目未单独提供 ready 探针（健康检查覆盖依赖探测）
- N/A 滚动发布状态：单实例，无滚动发布
- [x] 已观察错误日志：Render Logs 无连续 5xx/异常栈
- [x] 已验证新版本流量：前端首页 + 核心 API 可访问
- [x] 未发现异常后再继续（若异常立即 §8 回滚）
- [x] 已记录每个操作和时间点（§11）

### 5.6 F. 发布后验证检查单

**技术验证**

- [x] 首页可正常访问
- [x] 静态资源加载正常（`assets/*.js|css` 200，无 404）
- [x] SPA 路由刷新正常（直接刷新 `/players/1`、`/me` 不 404）
- [x] 登录/退出正常（访客 / 私人账户）
- [x] 核心 API 返回正常（players / prices / account / positions / trades）
- [x] 数据库读写正常（买入 → 持仓/流水出现 → 重新部署后仍在）
- N/A 缓存读写：无缓存服务
- N/A 文件上传/下载：无文件上传
- N/A 消息队列：无 MQ
- [x] 定时任务运行正常（cron 巡检刷新简报 / 保温）
- [x] 前端控制台无严重错误（发布后人工检查）
- [x] 无明显 404 / 500 / 超时（Render Logs + Network）

**业务验证**

- [x] 用户注册正常（私人账户）
- [x] 用户登录正常
- [x] 核心业务流程正常（行情 → 详情 → 买入 → 持仓 → 卖出 → 流水）
- [x] 权限控制正常（访客公共演示账户 / 私人账户令牌）
- [x] 关键数据展示正确（余额/总资产/收益、AI 建议 6 字段）
- N/A 通知 / 邮件 / 短信：未接入
- N/A 支付 / 订单：本作品只用信用点，无真实支付
- N/A 管理后台：无独立后台（`/api/debug/*` 仅运维自检）
- N/A 关键埋点：未接埋点（用 Render 日志 + CI 佐证）
- [x] AI 降级路径正常（无密钥/超时 → `source=rule_fallback`，仍 200）

**监控验证**

- [x] 5xx 错误率正常（无持续 5xx）
- [x] P95 延迟正常（免费档冷启动除外；暖态 API <1s，AI 2–3s）
- [x] CPU 使用率正常（Render Metrics）
- [x] 内存使用率正常
- [x] 数据库负载正常（免费档小数据量）
- N/A 缓存命中率：无缓存
- N/A 队列积压：无 MQ
- [x] 告警没有异常增长（无告警系统；健康检查 + 人工观察）

### 5.7 G. 发布完成检查单

- [x] 已确认发布成功（服务 Live + 冒烟通过）
- [x] 已记录最终版本号（commit SHA）
- [x] 已记录最终 Commit SHA 与 Render Deploy ID
- [x] 已更新变更日志（commit message / README / 本文 §11）
- [x] 已通知相关人员（小组群 / Issue）
- [x] 已关闭发布窗口（不再夹带改动）
- [x] 已保留上一版本制品（Render Deploys 历史可回滚）
- [x] 已确认回滚路径仍然可用（§8）
- [x] 已归档发布记录（§11）
- [x] 如有问题，已创建复盘任务：**N/A** —— 本期 15 条缺陷全部关闭并沉淀为用例，未见需要复盘的新问题

### 5.8 本项目专项验收（补充）

- [x] 线上 `/api/debug/db`：`是否 SQLite: false`，表非空（证明 Postgres 生效）
- [x] 重新部署后端后交易记录仍在（持久化验收）
- [x] 前端 `VITE_API_BASE_URL` 无 `127.0.0.1`（CI 有静态检查）
- [x] CORS 无尾斜杠问题（`CORS_ORIGINS` 处理 + 实测）
- [x] 移动端（390px）无横向溢出、底部 4 Tab + 顶栏头像可用
- [x] 首页简报可见且非空（AI/规则均可）
- [x] 404 页正常（访问 `/ui-kit` 等已移除路由 → 「页面不存在」）

### 5.9 最终发布检查卡（一页版）

> 参考案例末尾的「最终发布检查卡」；每次发布只带这一页，细节回查 A–G。

| # | 必须确认 | 证据 / 命令 |
| --- | --- | --- |
| 1 | CI 4 个 job 全绿 | GitHub Actions 最新 run；红则不发布 |
| 2 | 线上版本 = 预期 commit | Render Deploys 的 commit SHA；`git rev-parse --short HEAD` |
| 3 | 服务存活 | `curl -fsS …/api/health` → `{"status":"ok"}` |
| 4 | 数据库是 Postgres 且非空 | `curl -fsS …/api/debug/db` → `是否 SQLite: false`、players=16 |
| 5 | 前端首页 + SPA 刷新 | 打开 `/`、直接刷新 `/players/1`、`/me` 均 200 |
| 6 | 交易闭环 | 行情 → 详情 → 买入 → 持仓 → 卖出 → 流水；刷新后数据仍在 |
| 7 | AI 正常 + 降级 | `/api/analysis/1` `source=llm`；无 Key 场景 `source=rule_fallback` 且仍 200 |
| 8 | 简报新鲜 | `/api/agent/brief` `generated_at` 不超过 30 分钟 |
| 9 | 移动端 / 深浅色 | 390px 无横向溢出；深/浅主题可切换；底部 4 Tab 正常 |
| 10 | 回滚点与备份 | 记录上一版 commit/Deploy；数据变更前 `pg_dump` 成功；异常按 §8 回滚 |

**发布签名**：发布负责人 D ｜ 验证负责人 D + B ｜ 时间 ｜ 结果（通过 / 回滚）。

---

## 6. 访问地址与已知问题

| 项 | 地址 / 状态 |
| --- | --- |
| 前端 | <https://playerstock-frontend-mdlk.onrender.com>（Static Site，HTTPS） |
| 后端 | <https://playerstock-backend-mdlk.onrender.com>（Web Service，HTTPS） |
| 健康检查 | `/api/health` → `{"status":"ok","service":"playerstock-backend"}` |
| 数据库自检 | `/api/debug/db`（需 `DEBUG_ENDPOINTS=1`，只读元信息） |
| 部署源 | `develop` 分支 + `render.yaml` |

**已知限制（验收时如实说明）**

1. 免费实例闲置休眠，冷启动 30–60s（保温 cron + 前端提示 + 预热脚本缓解）；
2. 免费 Postgres 约 2026-11-23 到期，之后需升级/迁移；
3. 免费档无灰度/Preview 环境（§4.7 给设计方案）；
4. 无自动备份告警体系，靠手工备份 + 演示数据可重建；
5. 单实例 0.1 vCPU 级别，压测饱和约 38 req/s，不适合真实高并发；
6. `render.yaml` 与 `.env.example` 已同步 DeepSeek 配置（2026-11-21），`LLM_API_KEY` 仍由控制台保管。

---

## 7. 常见故障排查手册

| 现象 | 可能原因 | 检查 | 处理 |
| --- | --- | --- | --- |
| 前端报 CORS 错误 | `CORS_ORIGINS` 未填 / 多了尾斜杠 / 前端域名变了 | 后端 Environment；浏览器 Origin | 改成精确 origin（不要 `/`），保存重部署 |
| 首次打开几十秒白屏/转圈 | 免费实例冷启动 | Render Logs 出现启动日志 | 等或跑 `prewarm.py`；白天有保温 cron |
| 502 / 服务不可用 | 后端启动失败 / 构建失败 / 实例重启 | Render Logs、Deploys 状态 | 看日志修配置；必要时 Rollback（§8） |
| 启动报 `ModuleNotFoundError: psycopg` | SQLAlchemy 2.1 默认驱动变化 | 启动日志、`DATABASE_URL` 写法 | 确认代码已归一化为 `postgresql+psycopg2://` |
| 启动报 `Can't load plugin: sqlalchemy.dialects:postgres` | Render 给的 `postgres://` 未转换 | 同上 | 同上（代码已处理） |
| 数据每次部署都丢 | 用了 SQLite / 没填 `DATABASE_URL` | `/api/debug/db` 的方言；日志 SQLite 警告 | 填 Postgres Internal URL 并重部署；重灌数据 |
| 前端页面空白、API 地址错 | `VITE_API_BASE_URL` 未配置/带尾斜杠 | 浏览器 Network | 控制台改环境变量 → **重新构建部署**前端 |
| 刷新 `/players/1` 404 | Static Site 缺 SPA rewrite | Render → Redirects/Rewrites | 配 `/* → /index.html`（`render.yaml` 已有） |
| AI 一直 `rule_fallback` | 无密钥 / 超时 / 返回非 JSON | 后端日志、`/api/analysis/1` | 检查 `LLM_API_KEY/BASE_URL/MODEL`；降级本身不影响交易 |
| 简报长时间不更新 | cron 失败 / 简报未过期 / 后端休眠 | Render Cron 日志、`/api/agent/brief` 时间 | 手动触发 cron / 预热；看 patrol 日志 |
| Render 免费额度耗尽 | 保温/巡检频率过高 | Render Billing/Usage | 降频（夜间停）、或升级付费 |
| Postgres 连接失败/到期 | 30 天到期 / 连接数上限 | Render Postgres 状态 | 升级保留或迁移外部库；恢复备份 |

---

## 8. 回滚方案

### 8.1 回滚演练记录（历史实测）

- 演练方式：Render 控制台选上一个成功版本 Rollback → 服务 `Live` → `/api/health` 200 →
  再手动 Redeploy 最新版本并恢复 Auto-Deploy。
- 结论：**回滚路径可用**；数据库独立，不受代码回滚影响（演示数据可重建）。

### 8.2 回滚触发条件

- 发布后核心链路不可用（登录/行情/买卖 5xx）；
- 前端白屏/控制台严重错误，且 10 分钟内无法定位；
- 数据读写异常或 schema 不兼容；
- 监控指标（5xx、延迟）较基线明显恶化。

### 8.3 回滚操作（代码回滚，数据不回滚）

**方式 A：Render 控制台（最快，推荐）**

1. Render → `playerstock-backend`（或前端）→ **Deploys**
2. 找到上一个 `Live` 的成功部署 → **Rollback to this deploy**（或 `Redeploy`）
3. 等状态 `Live` → 执行 §3.7 冒烟 → 记录 §11

**方式 B：Git 回滚（需要下次部署也正确）**

```bash
git revert <bad_commit>          # 生成反向提交，保留历史
git push origin develop          # 触发 CI + Render 重新部署
# 紧急时也可 git reset --hard <good_commit> + git push --force-with-lease（团队项目慎用）
```

**前端/后端可独立回滚**：静态站点与 Web Service 各自有部署历史，先回滚出问题的那一侧即可。

### 8.4 回滚注意事项

- **代码回滚 ≠ 数据库回滚**：Postgres 是独立服务，版本回退不动数据；若数据被写坏，用备份恢复或
  重跑 `bootstrap_demo_data.py`（仅演示数据；会清空账户持仓/流水，慎用）。
- 回滚前确认旧版本仍可运行（依赖/环境变量兼容）；回滚后继续观察 10 分钟。
- 记录回滚原因、影响范围、时间点、验证结果（§11）；如属发布事故，按课程要求建复盘 Issue。

- 更早的部署与故障记录见附录 A。

---

## 9. 部署侧 TODO / 已知限制

| # | 事项 | 影响 | 计划 |
| --- | --- | --- | --- |
| 1 | Render 免费 Postgres 约 2026-11-23 到期 | 到期后线上数据不可用 | 答辩前升级/迁移，或导出备份 |
| 2 | `DEBUG_ENDPOINTS` 验收后应关闭 | `/api/debug/*` 暴露运维面 | 验收完成后设 `0` 并重新部署 |
| 3 | 无自动化依赖漏洞扫描 | 供应链风险 | 发布前手工 `pip-audit` / `npm audit`，或接入 CI |
| 4 | 免费档无灰度/告警 | 只能发布后人工观察 | 课程答辩够用；生产化再按 §4.7 升级 |
| 5 | 无自定义域名/WAF/CDN 独立配置 | 依赖 `onrender.com` | 课程不要求，保持现状 |

---

## 10. 本地部署与可复现验收（课程「可运行可复现」）

```bash
# 0) 前置：Python 3.12+、Node 24、Git
git clone https://github.com/July75-bit/Innovation.git && cd Innovation

# 1) 后端
cd code/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # 本地 SQLite 默认配置即可
cd ../..
python scripts/bootstrap_demo_data.py                # 16 名选手 + 演示账户 + 价格历史
(cd code/backend && uvicorn app.main:app --host 127.0.0.1 --port 8000)

# 2) 前端（另开终端）
cd code/frontend
npm ci
# .env.local：VITE_API_BASE_URL=http://127.0.0.1:8000，VITE_USE_MOCK=false
npm run dev        # http://localhost:5173
```

```bash
# 3) 测试（与 CI 同口径）
python -m pytest                                     # 后端（仓库根）
cd code/frontend && npm run lint && npm run test:unit -- --run && npm run build
```

验收要点：本地能起、数据可重建（固定 seed）、线上同 commit 可复现；页面能从行情走到买卖闭环。

---

## 11. 发布记录

### 11.1 记录模板（每次发布复制一行）

| 时间 | 版本（commit） | 内容 | CI | 部署（前端/后端 Deploy ID） | 验证人 | 结果 / 回滚点 |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD HH:mm | `abc1234` | 一句话 | run `…` 4/4 | `dep-xxx` / `dep-yyy` | D | 通过 / 上一版本 `def5678` |

### 11.2 最近记录（截至本文最后更新）

| 时间（UTC+8） | 版本 | 内容 | CI | 结果 |
| --- | --- | --- | --- | --- |
| 2026-11-21 08:45 | `ccf6447`（develop） | 移除 /ui-kit 展示页与 10 个展示组件；手机端导航简化 | run `44845160203` **4/4** | 线上 `/api/health` 200（1.25s）、前端首页 200（1.10s）；冒烟通过 |
| 2026-11-21 08:38 | `c234962` | 手机端去掉菜单抽屉，只留顶栏头像 + 底部 4 Tab | CI 通过 | 前端静态站点更新 |
| 2026-11-21 01:xx | `caefef1` | 拆分 `get_account_history`，修复 CI ruff C901 | run `44786913573` **4/4** | 后端恢复绿 |
| 2026-11-21 08:48 | —（运维复核） | 复核线上：`/api/debug/db` 方言 `postgresql`、`是否 SQLite: false`、players=16；`/api/agent/brief` `generated_at=2026-11-21T00:40Z`、`source=llm` | — | 通过：Postgres 生效、cron 简报新鲜 |

> 部署 ID 以 Render 控制台 Deploys 为准；本表由发布负责人填写，不凭记忆补写。

---

## 附录 A. 部署历程与故障复盘（历史）

| 日期 | 事件 | 处理 / 结论 |
| --- | --- | --- |
| 2026-10-24 | 第 3 天部署预检（不部署） | 复核 rootDir/startCommand、CORS、SQLite 误用告警；代码侧就绪 |
| 2026-10-25 | 首次手动部署（未用 Blueprint） | 建 Postgres + Web Service + Static Site；回填 CORS；线上买卖闭环通过 |
| 2026-11-07 | LLM 从 OpenCode Zen 切到 DeepSeek 官方 API | Zen 免费档 429 限流；改 `LLM_BASE_URL=https://api.deepseek.com/v1`、`LLM_MODEL=deepseek-flash`；`source=llm` 中位 ~2.4s |
| 2026-11-14 | 发现「数据总丢」根因 | 免费实例临时文件系统；改 Postgres；顺带修 `postgres://` 归一化与 `psycopg2` 驱动坑 |
| 2026-11-14 | 线上 CORS 整站失败 | `CORS_ORIGINS` 未填/带尾斜杠；代码统一 rstrip(`/`) 并实测修复 |
| 2026-11-19 | 免费实例冷启动严重（首请求 33.6s） | 加保温 cron（每 10 分钟，白天）、前端慢加载提示 + GET 重试 |
| 2026-11-21 | CI 后端 14 秒红 | 实际是 ruff `C901` 圈复杂度（pytest 被跳过）；拆函数修复，CI 恢复 4/4 |

## 附录 B. 命令速查

```bash
# 版本与发布
git rev-parse --short HEAD
git push origin develop
gh run list --branch develop --limit 3        # 或网页 GitHub Actions

# 线上健康
curl -fsS https://playerstock-backend-mdlk.onrender.com/api/health
curl -fsS https://playerstock-backend-mdlk.onrender.com/api/debug/db
curl -fsS https://playerstock-backend-mdlk.onrender.com/api/agent/brief | head -c 300

# 预热 / 冒烟 / 数据
python scripts/prewarm.py --base https://playerstock-backend-mdlk.onrender.com
python scripts/smoke_test_api.py --base https://playerstock-backend-mdlk.onrender.com --read-only
DATABASE_URL="<External URL>" python scripts/bootstrap_demo_data.py

# 备份
pg_dump "<External Database URL>" --no-owner --no-privileges -f backup.sql
```

## 附录 C. 检查单使用建议

- 每次发布把 §5.1–§5.7 复制到 Issue 或 `docs/mgmt/day*.md`，逐项打勾并附证据（截图/CI 链接/日志时间）。
- `N/A` 要写原因（本项目无对象存储/缓存/MQ/支付），不要留空——课程检查单强调「逐项确认」。
- 发布记录（§11）与回滚点必须真实填写，不事后补写；答辩时可直接展示本页作为「发布流程可追溯」的证据。
