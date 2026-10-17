# 部署说明

> **负责人**：D ｜ **截止**：第 5 天必须完成并验证 ｜ **状态**：⬜ 待填写
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
| `DATABASE_URL` | `sqlite:///./playerstock.db`（免费版）或 `sqlite:////var/data/playerstock.db`（挂盘） | 否 |
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

## 3. 部署步骤（第 5 天）

1. 代码推到 GitHub `main` 分支
2. Render → New → Blueprint → 选仓库 → 自动读取 `render.yaml`
3. 填两个 `sync: false` 的密钥（`LLM_API_KEY`、`CORS_ORIGINS`、`VITE_API_BASE_URL`）
4. 等两个服务都 Deploy succeeded
5. 验证（见第 5 节）

## 4. SQLite 持久化（必须解决，否则第 5 天验收不过）

| 方案 | 成本 | 数据是否持久 | 步骤 |
| --- | --- | --- | --- |
| A. Persistent Disk（推荐先试） | 付费 | ✅ 重启不丢 | 加 `disk` 配置，挂 `/var/data`，改 `DATABASE_URL` |
| B. 托管 PostgreSQL（推荐长期） | 免费额度 | ✅ | 用 Render Postgres，改 `DATABASE_URL`，SQLAlchemy 无需改代码 |
| C. 免费实例 + 临时盘 | 免费 | ❌ 重新部署即丢 | **只够演示**，必须向老师说明这是已知限制 |

> 课程材料明确警告过这个问题。若只能用方案 C，答辩时要**主动说明**，并把"数据持久化方案对比"写进文档（这反而是加分项）。

## 5. 线上验收清单（必须逐条打勾）

- [ ] `GET https://<backend>/api/health` 返回 `{"status":"ok",...}`
- [ ] 前端页面能打开，且不是白屏
- [ ] 前端成功拉到 `/api/players`（浏览器 Network 无 CORS 报错）
- [ ] 线上完成一次买入：余额减少、持仓增加、流水新增
- [ ] 线上完成一次卖出：余额增加、持仓减少
- [ ] **重新部署一次后端，然后刷新页面**：前面那笔交易和持仓**仍在**（验证持久化）
- [ ] 线上点一次 AI 分析，返回合法结构（`source` 为 `llm` 或 `rule_fallback` 均可）
- [ ] 断开/清空 `LLM_API_KEY` 后，交易功能仍可用
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
