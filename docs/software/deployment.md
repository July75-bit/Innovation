# PlayerStock 虚拟选手股交易系统 — Render 部署指南

本文档说明如何把本项目（Vue 3 前端 + FastAPI 后端 + PostgreSQL）部署到 Render，并给出上线前、中、后的检查单。内容按本项目实际配置与实测结果编写，按部署指南的常用顺序组织。

> 本项目是**课程演示系统**：全部交易使用虚拟信用点，不可充值 / 提现 / 兑换，不接真实资金、不接真实赛事数据。上线仅为课程审查与演示，不面向真实用户或生产流量。
>
> 为兼容其他文档的引用，章节编号沿用旧版：§2 环境与配置、§3 部署步骤、§4 持久化/监控、§5 检查单、§6 地址与限制、§7 排障、§8 回滚。旧 §3.8/§3.10 已并入 §3.4/§3.6。

---

## 1. 部署架构

```text
用户浏览器 ──HTTPS──> Render Static Site（CDN）
                          │  dist/ 静态文件，SPA rewrite /* → /index.html
                          │
                          └── XHR/fetch ──> Render Web Service（FastAPI / uvicorn）
                                                │
                       ┌────────────────────────┼──────────────────────────┐
                       │                        │                          │
               Render PostgreSQL          DeepSeek API               Cron 巡检
               9 张业务表（账本/审计）     api.deepseek.com           每 10 分钟保活 + 刷简报
                       ▲
                       │
              GitHub Actions（CI 4 job）── push develop ──> 自动部署
```

与自建 Linux 服务器方案的关键差异，影响部署决策：

| 项目 | 本项目（Render） |
|---|---|
| 服务器 | 不自己买服务器、不装 Nginx/systemd；前端 Static Site、后端 Web Service 均由 Render 托管 |
| 构建 | 前端在 Render 构建 `npm run build`；后端直接 `pip install -r requirements.txt` 后启动 |
| 数据库 | **必须用 Render PostgreSQL**；Web Service 文件系统是临时的，用 SQLite 会在重启/部署后丢数据 |
| 配置 | 环境变量在 Render 控制台或 `render.yaml` 里配置；`.env` 只用于本地 |
| HTTPS | Render 自动签发证书，无需 Certbot |
| 冷启动 | 免费实例闲置 15 分钟休眠，首次请求 30–60 秒（实测 33.6 秒） |
| 定时任务 | Render Cron 调脚本（保活 + 刷新简报），不常驻后台线程 |

**资源与容量（免费档）**

| 资源 | 配置 / 限制 | 实测或结论 |
| --- | --- | --- |
| Web Service | 约 0.1 vCPU，单实例 | 只读压测饱和 **~38 req/s**，约 **190 人同时在线**、0 错误；瓶颈是实例规格 |
| 内存 | 小内存，以控制台为准 | 无深度学习框架，常驻开销低 |
| 磁盘 | **临时文件系统**，不能放 SQLite / 上传文件 | 业务数据全部进 PostgreSQL |
| Static Site | 免费、全球 CDN、HTTPS | 构建产物 `dist/` |
| PostgreSQL | 免费实例，**约 30 天到期（2026-11-23 前后）** | 9 张表；演示数据可重建；到期前必须备份并迁移/续期 |
| Cron | 免费，`*/10 0-15 * * *` | 约 496 h/月，在免费 750 h 额度内 |
| 冷启动 | 闲置 15 分钟休眠 | 冷启动 30–60 s；暖态 API 约 0.88 s |
| AI 延迟 | DeepSeek 外部依赖 | 线上中位 2.0–2.5 s；L4 P95 3.39 s（门禁 10 s） |

---

## 2. 环境与配置

### 2.1 账号与前置条件

- GitHub 仓库：`github.com/July75-bit/Innovation`（public，分支 `develop`）
- Render 账号（可用 GitHub 登录）
- DeepSeek API Key（可选；没有 Key 时 AI 自动降级为规则版，交易功能不受影响）
- 本地只用于改代码 / 灌演示数据：Git、Python 3.12+、Node.js 20+

```bash
git clone https://github.com/July75-bit/Innovation.git
cd Innovation && git checkout develop && git rev-parse HEAD
```

### 2.2 环境变量

后端（Web Service → Environment）：

| 变量 | 值 / 说明 |
| --- | --- |
| `DATABASE_URL` | Postgres **Internal Database URL**；代码自动归一化为 `postgresql+psycopg2://` |
| `LLM_API_KEY` | DeepSeek Key，`sync: false`，只在控制台填写 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | `deepseek-flash` |
| `CORS_ORIGINS` | 前端 origin，英文逗号分隔，**不能带尾斜杠** |
| `DEBUG_ENDPOINTS` | 验收期 `1`；验收结束改 `0` 并重新部署 |
| `RESEED_TOKEN` | 随机串；重灌演示数据时必须携带 |

前端（Static Site → Environment，**构建期生效**）：

| 变量 | 值 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端公网地址（无尾斜杠） |
| `VITE_USE_MOCK` | `false` |

> 改前端环境变量必须重新构建部署；静态站不会自动读取新值。

### 2.3 CORS、HTTPS 与 SPA 路由

- 前端 origin 必须与 `CORS_ORIGINS` 完全一致；尾斜杠会导致整站跨域失败（BUG-12）。
- HTTPS 由 Render 自动签发，无需配置证书。
- Static Site 的 rewrite `/* → /index.html` 负责 SPA 刷新，避免 `/players/1` 404（BUG-11）。

---

## 3. 部署步骤

### 3.1 用 Blueprint 创建服务

Render 控制台 → **New → Blueprint** → 选择本仓库，读取根目录 `render.yaml`，自动创建：

| 服务 | 类型 | 作用 |
| --- | --- | --- |
| `playerstock-backend` | Web Service | FastAPI 后端，健康检查 `/api/health` |
| `playerstock-frontend` | Static Site | 前端构建产物，SPA rewrite |
| `playerstock-agent-patrol` | Cron | 每 10 分钟保温 + 刷新简报 |

> 也可以不启用 Blueprint，手工创建同样两个服务，配置照抄 `render.yaml`。

### 3.2 首次部署与日常发布

1. push 到 `develop`，GitHub Actions 触发 4 个 job（健康、后端、前端、交付物）。
2. CI 全绿后，Render 自动部署；Cron 按计划运行。
3. 等后端 Deploys 变 **Live**，执行 §3.4 冒烟。
4. 发布窗口选白天；演示前 1 小时不做大改动。

### 3.3 数据库初始化 / 演示数据重建

用 Postgres 的 **External Database URL** 在本地灌数据（Internal URL 只在 Render 内网）：

```bash
# Windows PowerShell；bash 用 export DATABASE_URL="..."
$env:DATABASE_URL = "<External Database URL>"
python scripts/bootstrap_demo_data.py
```

写入 16 名选手 / 8 支战队 / 11 个价格点、演示账户 5000 信用点、0 持仓 0 流水。可重复执行；不会清掉私人注册账号（BUG-15 已修）。

### 3.4 发布后冒烟（必须）

```bash
BASE=https://playerstock-backend-mdlk.onrender.com
curl -fsS $BASE/api/health
curl -fsS $BASE/api/debug/db          # 方言 postgresql、players=16
curl -fsS $BASE/api/players | head -c 200
curl -fsS $BASE/api/agent/brief | head -c 300
```

| 检查 | 通过标准 |
| --- | --- |
| `/api/health` | 200，service 为 playerstock-backend |
| `/api/debug/db` | 方言 postgresql、是否 SQLite: false、players=16 |
| 前端首页 | 200，控制台无严重报错 |
| 交易闭环 | 买入 → 持仓/流水出现 → 刷新后仍在 |
| AI | 6 字段建议；无 Key 时 `source=rule_fallback` 且仍 200 |
| 简报 | `generated_at` 不超过 30 分钟 |

### 3.6 演示前预热

免费实例休眠后首次请求很慢；演示前 10 分钟执行：

```bash
python scripts/prewarm.py --base https://playerstock-backend-mdlk.onrender.com
```

---

## 4. 持久化、监控与容量

### 4.1 平台事实

| 项 | 限制 |
| --- | --- |
| CPU | 免费档约 0.1 vCPU；压测饱和 ~38 req/s、约 190 人同时在线、0 错误 |
| 内存 / 磁盘 | 小内存；文件系统临时，**不能放 SQLite** |
| Postgres | 免费实例约 30 天到期（2026-11-23 前后），到期需迁移或续期 |
| 休眠 | 闲置 15 分钟休眠，冷启动 30–60s（曾实测首请求 33.6s） |
| Cron | `*/10 0-15 * * *`，约 496h/月，在免费额度内 |
| AI | DeepSeek 中位 ~2.0–2.5s；L4 P95 3.39s |

### 4.2 持久化与备份

- 业务数据全部进 Postgres；代码启动检测到 SQLite 会打警告。
- 演示数据可随时重建：`python scripts/bootstrap_demo_data.py`。
- 重建不会清掉私人注册账号（BUG-15 已修）。
- 涉及数据变更前手工备份：

```bash
pg_dump "<External Database URL>" --no-owner --no-privileges -f backup.sql
psql "<External Database URL>" -f backup.sql      # 恢复前确认目标库
```

### 4.3 监控

| 层级 | 手段 | 阈值 |
| --- | --- | --- |
| 存活 | Render 健康检查 `/api/health` | 失败自动重启 |
| 业务 | players / prices / account | 发布后全 200 |
| 数据 | `/api/debug/db`（§4.5.1） | 方言 postgresql、表非空 |
| AI | `/api/analysis/1` 的 `source` | rule_fallback 属正常降级 |
| 简报 | `generated_at` | 超过 30 分钟算异常 |
| 平台 | Render Metrics / Logs | 5xx 明显升高即回滚 |

免费档没有自定义告警，靠发布后人工检查 + Cron + Render 服务状态页。

### 4.5.1 只读数据库自检

`GET /api/debug/db` 返回数据库方言、表清单与行数，只读，不含连接串与个人数据；`DEBUG_ENDPOINTS=0` 时返回 404。验收标准：方言 `postgresql`、players=16。

---

## 5. 发布检查单（A–G）

每次发布复制一份，逐项打勾；本项目无对象存储 / 缓存 / MQ / 支付，相关项标 N/A 并写原因。

### A. 发布准备

- [ ] 已确认发布版本 / 范围，并关联 Issue 或变更记录
- [ ] 本地与 CI 同口径检查通过（pytest / vitest / lint / build）
- [ ] CI 4 个 job 全绿
- [ ] 已记录本次 commit SHA 与上一版回滚点
- [ ] 已明确发布负责人与验证负责人

### B. 配置

- [ ] 后端环境变量齐全，`DATABASE_URL` 是 Postgres Internal URL
- [ ] `LLM_API_KEY` 只在 Render 控制台，未写进仓库
- [ ] `CORS_ORIGINS` 精确匹配前端 origin，无尾斜杠
- [ ] 前端 `VITE_API_BASE_URL` 指向后端公网地址
- [ ] `DEBUG_ENDPOINTS` 在验收结束后已改 0
- [ ] `RESEED_TOKEN` 已改为随机值

### C. 数据库

- [ ] 确认数据在 Postgres，不是临时盘 SQLite
- [ ] schema 无未评估的变更；如有，先备份
- [ ] 演示数据可重建（`bootstrap_demo_data.py`）
- [ ] 私人注册账号未被重灌覆盖
- [ ] 数据库未到期（免费档约 2026-11-23）

### D. 基础设施

- [ ] 两个服务 Deploys 均为 Live
- [ ] HTTPS 正常，前端域名可访问
- [ ] 后端健康检查通过
- [ ] Render Logs 可查，无连续 5xx
- [ ] Cron 最近一次执行成功

### E. 发布执行

- [ ] 记录本版 commit 与部署时间
- [ ] 部署过程中观察日志，异常立即停止
- [ ] 保留上一版部署记录，便于回滚

### F. 发布后验证

- [ ] 首页、静态资源、SPA 刷新（`/players/1`）正常
- [ ] 登录 / 访客进入正常
- [ ] 买入 → 持仓 → 卖出 → 流水，刷新后仍在
- [ ] AI 正常或按预期 `rule_fallback`
- [ ] 简报 30 分钟内更新
- [ ] 390 px 无横向溢出，深浅色可切

### G. 发布完成

- [ ] 记录最终 commit / Deploy 与验证结果到 §10
- [ ] 通知团队与演示负责人
- [ ] 保留回滚点；数据变更前已备份

**一页版（每次只带这张）**

| # | 必须确认 |
| --- | --- |
| 1 | CI 4/4 绿 |
| 2 | 线上 commit 与预期一致 |
| 3 | `/api/health` 200 |
| 4 | 数据库是 Postgres 且 players=16 |
| 5 | 首页 + SPA 刷新 200 |
| 6 | 买入→持仓→卖出→流水，刷新后仍在 |
| 7 | AI 正常或按预期 rule_fallback |
| 8 | 简报 30 分钟内 |
| 9 | 390 px 无横向溢出，深浅色可切 |
| 10 | 已记录回滚点；数据变更前已备份 |

---

## 6. 地址与限制

| 项 | 值 |
| --- | --- |
| 前端 | <https://playerstock-frontend-mdlk.onrender.com> |
| 后端 | <https://playerstock-backend-mdlk.onrender.com> |
| API 文档 | <https://playerstock-backend-mdlk.onrender.com/api/docs> |
| 部署源 | 分支 `develop` + `render.yaml` |

**已知限制**：冷启动 30–60 s；免费 Postgres 约 30 天到期；无灰度 / 自动备份 / 自定义告警；0.1 vCPU 不适合真实高并发。

---

## 7. 常见故障

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 前端 CORS 报错 | `CORS_ORIGINS` 未填或带尾斜杠 | 改成精确 origin，重新部署 |
| 首次打开转圈 | 免费实例冷启动 | 等 30–60 s，或跑 prewarm |
| 502 | 后端启动 / 构建失败 | 看 Render Logs，必要时回滚 |
| 启动报 psycopg | SQLAlchemy 2.1 驱动变化 | 确认连接串是 `postgresql+psycopg2://` |
| 每次部署数据丢 | 用了 SQLite / 临时盘 | 配 `DATABASE_URL` 为 Postgres 并重灌数据 |
| 刷新 `/players/1` 404 | 缺 SPA rewrite | 配 `/* → /index.html` |
| 刷新 `/market` 白屏 | 无路由匹配且无兜底 | 用 `/` 入口；已加 `/market` 重定向 |
| AI 一直 rule_fallback | 无 Key / 超时 / 坏 JSON | 查 Key 与模型配置；降级不影响交易 |
| 简报不更新 | Cron 失败或后端休眠 | 看 Cron 日志，手动触发 |
| Postgres 连接失败 | 到期或连接数上限 | 迁移 / 升级，恢复备份 |
| 前端构建失败 | 依赖或类型错误 | 本地 `npm ci && npm run build` 复现 |

---

## 8. 回滚

触发条件：核心链路 5xx、前端白屏 10 分钟无法定位、数据异常、5xx/延迟明显恶化。

1. Render → 对应服务 → **Deploys** → 选上一版 **Live** 的部署 → **Rollback**。
2. 等状态变 Live，执行 §3.4 冒烟。
3. 记录原因、时间、结果到 §10。
4. 代码回滚用 `git revert <bad-commit>` 后正常发布。

> **代码回滚不等于数据回滚**：如果数据被写坏，用备份恢复或重建演示数据；回滚前先确认数据影响面。

### 8.1 回滚演练记录（2026-11-07）

Render 选 09:26 版本 Rollback → 部署成功 → `/api/health` 200 → 再手动 Redeploy 最新版本并重开 Auto-Deploy。结论：代码可快速回退；已写入数据库的演示数据不会随代码回退，需要单独重建。

---

## 9. 待办与本地复现

### 9.1 待办

- 免费 Postgres 到期前完成备份与迁移 / 续期。
- 演示前重置演示数据并预热，避免冷启动与脏数据。
- 验收结束后关闭 `DEBUG_ENDPOINTS`。

### 9.2 本地复现

```bash
git clone https://github.com/July75-bit/Innovation.git && cd Innovation
# 后端
cd code/backend && python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env        # bash: cp .env.example .env
cd ../.. && python scripts/bootstrap_demo_data.py
(cd code/backend && uvicorn app.main:app --port 8000)
# 前端（另开终端）
cd code/frontend && npm ci && npm run dev
# 测试
python -m pytest
cd code/frontend && npm run lint && npm run test:unit -- --run && npm run build
```

---

## 10. 发布记录

| 时间 | commit | 内容 | CI | 结果 / 回滚点 |
| --- | --- | --- | --- | --- |
| 2026-11-21 08:45 | `ccf6447` | 移除 /ui-kit 展示页、手机端导航简化 | 4/4 | 通过；上一版 `c234962` |
| 2026-11-21 01:xx | `caefef1` | 拆函数修复 ruff C901 | 4/4 | 后端恢复绿 |

> 课程要求对照：部署方式选型见 §1，环境变量见 §2.2，标准发布流程见 §3.2，检查单见 §5，回滚见 §8。
