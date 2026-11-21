# 技术调研与选型

> 记录本项目为什么选这套技术、放弃了哪些备选。详细版本号见 README / 技术选型页。

## 1. 调研范围

前端框架、后端框架、数据库与 ORM、AI 模型与调用方式、部署平台、测试工具。

## 2. 选型对照

| 领域 | 候选 | 采用 | 原因 |
| --- | --- | --- | --- |
| 前端 | Vue 3 / React | Vue 3 + Vite + TypeScript | 团队熟、上手快、Vite 冷启动快、类型安全 |
| 后端 | FastAPI / Flask / Django | FastAPI | 自动生成 Swagger、Pydantic 校验、路由清晰 |
| 数据库 | SQLite / PostgreSQL | 本地 SQLite、线上 Render Postgres | 本地零配置，线上持久化；同一套 SQLAlchemy |
| AI | DeepSeek / OpenAI / 本地规则 | DeepSeek + 规则兜底 | 中文与价格可接受；超时/无 Key 自动降级，不影响交易 |
| 部署 | Render / 自建云服务器 | Render | 免费档含 HTTPS、自动部署、Postgres，课程量级足够 |
| 测试 | pytest / Vitest / Playwright | pytest + Vitest | 单元/集成覆盖够用；E2E 当前用人工验收替代 |

## 3. 主动放弃的方案

- **OpenAI gpt-4o-mini**：成本与网络稳定性不如 DeepSeek；OpenCode Zen 免费档实测 403 / 429。
- **JWT**：撤销与时钟漂移处理麻烦，改用不透明令牌 + 30 天过期。
- **缓存 / 消息队列**：课程数据量与并发不需要，先保证数据一致。
- **微服务拆分**：6 天团队维护不了，单体分层足够。

## 4. 依据与延伸阅读

- 架构与分层：`docs/software/architecture.md`
- 前端工程与性能：`docs/software/frontend_setup.md`、`docs/software/frontend_performance.md`
- 接口与数据：`docs/software/api_contract.md`、`docs/software/database_design.md`
- 定价算法：`docs/algorithm/pricing_model.md`
