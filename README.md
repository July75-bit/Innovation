# PlayerStock

> 虚拟选手股交易 + 智能体市场模拟 · 软件新技术创新实践课程作品

[![CI](https://github.com/July75-bit/Innovation/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/July75-bit/Innovation/actions/workflows/ci.yml)
[![许可](https://img.shields.io/badge/license-see%20LICENSE-blue)](LICENSE)

## 它是什么

用 **5000 信用点**买卖 CS2 选手的虚拟股，价格随模拟比赛表现变化；内置 **AI 智能体**：会拉行情、多角色分析、人在环采纳、全程留审计，**只给建议、不自动下单**。

- 16 名选手 / 8 支战队，每人 11 个价格点
- 每条涨跌都有原因（reason），可逐条追溯
- 智能体固定 6 字段契约；没 Key、超时、坏 JSON 都走规则兜底，接口仍 200
- 交易、定价、结算由确定性代码完成；智能体只读，不碰余额
- 浅色 / 深色双模式，移动端可用

## 合规声明

全程使用 **信用点**，不可充值、不可提现、不可兑换。选手姓名与战队取自公开信息，**价格与评分均为本项目模拟数据**，与 Valve、HLTV、选手及俱乐部均无关联；仅用于课程学习与演示，不构成投资建议。

## 在线地址

| 内容 | 地址 |
| --- | --- |
| 前端 | <https://playerstock-frontend-mdlk.onrender.com> |
| 后端 API 文档 | <https://playerstock-backend-mdlk.onrender.com/docs> |
| 答辩幻灯片 | <https://july75-bit.github.io/Innovation/> |
| 幻灯片 PDF | <https://july75-bit.github.io/Innovation/playerstock_defense.pdf> |

> Render 免费档约 15 分钟休眠，首次打开可能等 30–60 秒。

## 快速开始

需要 Python 3.12+、Node.js 20+。

```powershell
# 后端
cd code/backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 前端（另开终端）
cd code/frontend
npm install
npm run dev

# 演示数据 / 跑测试（仓库根目录）
python scripts/seed_db.py
python -m pytest
cd code/frontend; npm run test:unit -- --run
```

验收：`/api/health` 返回 200，前端打开能买卖、看持仓、看 AI 建议。

## 技术栈

| 层 | 选型 | 备注 |
| --- | --- | --- |
| 前端 | Vue 3 + Vite + TypeScript + Vitest | 组合式 API，浅/深双模式 |
| 后端 | FastAPI + SQLAlchemy + Pydantic | 自动 Swagger；事务保证交易一致性 |
| 数据 | 本地 SQLite / 线上 Render Postgres | 一套 ORM 双环境 |
| AI | DeepSeek API + 规则兜底 | 20s 超时，失败自动降级 |
| 部署 | Render + GitHub Actions | CI 4 个 job，push 自动部署 |

完整版本号见 `code/frontend/package.json`、`code/backend/requirements.lock.txt`。

## 目录结构

```text
code/
  frontend/      Vue 3 前端
  backend/       FastAPI + ai/ 智能体
  core_engine/   定价与模拟比赛
docs/            课程文档（见下）
tests/           单元 / 集成 / 评测 / 压测
scripts/         初始化数据、模拟比赛、预热
render.yaml      Render 部署蓝图
```

## 文档

| 位置 | 内容 |
| --- | --- |
| `docs/requirements/` | 需求、用户故事、线框图 |
| `docs/software/` | 架构、接口契约、数据库、部署、UI 规范 |
| `docs/algorithm/` | 定价模型、AI 提示词、回测 |
| `docs/acceptance/` | 测试计划/报告、用户手册、证据 |
| `docs/slides/` | Slidev 答辩稿（17 页）+ 讲稿 |
| `docs/mgmt/` | 里程碑、缺陷记录、要求对照 |

## 团队分工

| 成员 | 负责 |
| --- | --- |
| A 倪颢容 | 前端 |
| B 胡德昊 | 后端与交易引擎 |
| C 刘宏 | 定价与数据 |
| D 王泽棠 | AI 智能体 / 测试 / 部署 / 文档 |

## 交易规则

- 注册赠送 5000 信用点；单选手持仓上限 50 股
- 比赛期间对应选手暂停交易，结算后恢复
- 买入需余额充足，卖出需持仓足够；数量必须为正整数
- 交易流水持久化，持仓/流水按时间倒序查询

## 已知限制

- Render 免费实例会休眠，冷启动约 30–60 秒
- 免费 Postgres 有到期时间，到期需换库或续期
- 不接真实赛事数据，不宣称预测准确率
