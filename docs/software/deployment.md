# 部署与发布

> 最后核对：2026-11-21。线上 demo 用 Render 免费档，够 4 人课程演示，不面向真实流量。

## 0. 课程要求对照

| 课程要求 | 本文落点 |
| --- | --- |
| 部署方式选型 | §1 架构与选型 |
| 构建、环境变量、域名与 HTTPS | §2 环境变量、§1.3 |
| 标准发布流程 | §3 发布流程 |
| 灰度 / 回滚 / 故障方案 | §4 监控与持久化、§8 回滚 |
| 上线前中后检查单 | §5 检查单（A–G） |
| 健康检查与监控 | §4.3 监控、§7 排障 |

## 1. 架构与选型

### 1.1 系统组成

| 服务 | 平台 | 说明 |
| --- | --- | --- |
| 前端 | Render Static Site | `code/frontend` 构建出 `dist/`，CDN + HTTPS |
| 后端 | Render Web Service | `code/backend`，`uvicorn app.main:app` |
| 数据库 | Render Postgres | 9 张表；本地开发用 SQLite |
| 定时任务 | Render Cron | 每 10 分钟保温 + 刷新简报（白天） |
| CI/CD | GitHub Actions | 4 个 job 全绿才允许部署 |

### 1.2 为什么用 Render

免费、HTTPS、GitHub 自动部署、Postgres 托管，Blueprint（`render.yaml`）可复现。
代价是免费实例 0.1 vCPU、15 分钟休眠、Postgres 30 天到期——都写进 §6 限制。

### 1.3 域名、HTTPS 与跨域

- 地址均为 `*.onrender.com`，HTTPS 由 Render 自动签发，未配自定义域名。
- 前端 `VITE_API_BASE_URL` 指向后端公网 origin（无尾斜杠）；后端 `CORS_ORIGINS` 精确匹配前端 origin。
- SPA 刷新 404 由 Static Site 的 rewrite 处理：`/* → /index.html`。

## 2. 环境变量

后端（Render → Environment）：

| 变量 | 值 / 说明 |
| --- | --- |
| `DATABASE_URL` | Postgres Internal URL（代码归一化为 `postgresql+psycopg2://`） |
| `LLM_API_KEY` | DeepSeek Key，`sync: false`，不进仓库/日志 |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | `deepseek-flash` |
| `CORS_ORIGINS` | 前端 origin，逗号分隔，无尾斜杠 |
| `DEBUG_ENDPOINTS` | 验收期 1，验收后改 0 |
| `RESEED_TOKEN` | 随机值；重灌演示数据需带此令牌 |

前端（构建期）：

| 变量 | 值 |
| --- | --- |
| `VITE_API_BASE_URL` | 后端公网地址 |
| `VITE_USE_MOCK` | `false` |

> 改前端环境变量必须重新构建部署，静态站不会自动生效。

## 3. 发布流程

### 3.1 分支纪律

- `develop` 是部署分支，push 即触发 CI 与 Render 自动部署。
- 功能分支 `feat/*` 合并回 `develop`；不在 `develop` 上直接改大功能。
- 发布窗口选白天，演示前 1 小时不做大改动。

### 3.2 CI 门禁（4 个 job）

1. 仓库健康：冲突标记检查
2. 后端：ruff（E4/E7/E9/F/C901）+ pytest
3. 前端：eslint + vitest + build
4. 交付物完整性检查

### 3.3 日常发布

1. 本地跑与 CI 同口径的检查（见 README「快速开始」）。
2. push 到 `develop`，等 CI 4/4 绿。
3. 等 Render 两个服务 Deploys 变 `Live`。
4. 执行 §3.4 冒烟，记录到 §10 发布记录。
5. 异常按 §8 回滚。

### 3.4 发布后冒烟（必须）

| 检查 | 通过标准 |
| --- | --- |
| `/api/health` | 200，`service=playerstock-backend` |
| `/api/debug/db` | 方言 `postgresql`、`是否 SQLite: false`、players=16 |
| 前端首页 | 200，控制台无严重报错 |
| 交易闭环 | 买入 → 持仓/流水出现 → 刷新后仍在 |
| AI | `/api/analysis/1` 返回 6 字段；无 Key 时 `source=rule_fallback` 且仍 200 |
| 简报 | `/api/agent/brief` 的 `generated_at` 不超过 30 分钟 |

演示前 10 分钟跑 `python scripts/prewarm.py`，避免冷启动。

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

### 4.2 持久化

- 业务数据全部进 Postgres；代码启动检测到 SQLite 会打警告。
- 演示数据可随时重建：`python scripts/bootstrap_demo_data.py`（固定 seed，16 人 / 演示账户 / 价格历史）。
- 重建不会清掉私人注册账号（BUG-15 已修）。
- 涉及数据变更前手工备份：`pg_dump "$External URL" --no-owner -f backup.sql`。

### 4.3 监控

| 层级 | 手段 | 阈值 |
| --- | --- | --- |
| 存活 | Render 健康检查 `/api/health` | 失败自动重启 |
| 业务 | players / prices / account | 发布后全 200 |
| 数据 | `/api/debug/db` | 方言 postgresql、表非空 |
| AI | `/api/analysis/1` 的 `source` | rule_fallback 属正常降级 |
| 简报 | `generated_at` | 超过 30 分钟算异常 |
| 平台 | Render Metrics / Logs | 5xx 明显升高即回滚 |

免费档没有自定义告警，靠发布后人工检查 + cron。

## 5. 上线检查单（A–G）

每次发布复制一份，逐项打勾；本项目无对象存储 / 缓存 / MQ / 支付，相关项标 N/A 并写原因。

| 组 | 必查项 |
| --- | --- |
| A 发布准备 | 版本/范围确定；CI 绿；构建产物有 commit 标识；发布与验证负责人明确 |
| B 配置 | 生产环境变量齐全；API 地址无尾斜杠；CORS 精确；密钥在 Render；DEBUG 开关正确 |
| C 数据库 | schema 无变更或已评估；演示数据可重建；失败有回滚路径 |
| D 基础设施 | 服务 Live；HTTPS 正常；健康检查通过；日志可查 |
| E 发布执行 | 记录上一版 commit；部署后看日志无连续 5xx；异常立即停 |
| F 发布后验证 | 首页、静态资源、SPA 刷新、登录、交易闭环、AI 降级、移动端 |
| G 发布完成 | 记录最终 commit/Deploy；通知团队；保留上一版以便回滚 |

一页版（每次只带这张）：

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
| 9 | 390px 无横向溢出、深浅色可切 |
| 10 | 记录回滚点；数据变更前已备份 |

## 6. 地址与限制

| 项 | 值 |
| --- | --- |
| 前端 | <https://playerstock-frontend-mdlk.onrender.com> |
| 后端 | <https://playerstock-backend-mdlk.onrender.com> |
| API 文档 | <https://playerstock-backend-mdlk.onrender.com/api/docs> |
| 部署源 | `develop` + `render.yaml` |

已知限制：冷启动 30–60s；Postgres 30 天到期；无灰度/自动备份/告警；单实例 0.1 vCPU 不适合真实高并发。

## 7. 常见故障

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 前端 CORS 报错 | `CORS_ORIGINS` 未填或带尾斜杠 | 改成精确 origin，重部署 |
| 首次打开转圈 | 免费实例冷启动 | 等 30–60s，或跑 prewarm |
| 502 | 后端启动/构建失败 | 看 Render Logs，必要时回滚 |
| 启动报 psycopg | SQLAlchemy 2.1 驱动变化 | 确认连接串是 `postgresql+psycopg2://` |
| 每次部署数据丢 | 用了 SQLite | 配 `DATABASE_URL` 并重灌数据 |
| 刷新 `/players/1` 404 | 缺 SPA rewrite | 配 `/* → /index.html` |
| AI 一直 rule_fallback | 无 Key / 超时 / 坏 JSON | 查 Key 与模型配置；降级不影响交易 |
| 简报不更新 | cron 失败或后端休眠 | 看 Cron 日志，手动触发 |
| Postgres 连接失败 | 到期或连接数上限 | 迁移/升级，恢复备份 |

## 8. 回滚

触发：核心链路 5xx、前端白屏 10 分钟无法定位、数据异常、5xx/延迟明显恶化。

步骤（推荐 Render 控制台）：

1. Render → 服务 → Deploys，选上一个 Live 的部署 → Rollback。
2. 等 Live，跑 §3.4 冒烟。
3. 记录原因、时间、结果到 §10。

代码回滚可用 `git revert <bad>` 后正常发布；**代码回滚不等于数据回滚**，数据坏了用备份或重建演示数据。

## 9. 本地复现

```bash
git clone https://github.com/July75-bit/Innovation.git && cd Innovation
# 后端
cd code/backend && python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
cd ../.. && python scripts/bootstrap_demo_data.py
(cd code/backend && uvicorn app.main:app --port 8000)
# 前端（另开终端）
cd code/frontend && npm ci && npm run dev
# 测试
python -m pytest
cd code/frontend && npm run lint && npm run test:unit -- --run && npm run build
```

验收：本地能起、数据可重建、线上同 commit 可复现、能从行情走到买卖闭环。

## 10. 发布记录

| 时间 | commit | 内容 | CI | 结果 / 回滚点 |
| --- | --- | --- | --- | --- |
| 2026-11-21 08:45 | `ccf6447` | 移除 /ui-kit 展示页、手机端导航简化 | 4/4 | 通过；上一版 `c234962` |
| 2026-11-21 01:xx | `caefef1` | 拆函数修复 ruff C901 | 4/4 | 后端恢复绿 |
