# PlayerStock —— 数据驱动的虚拟选手股交易与智能体市场模拟系统

> 软件创新工程实践（软件新技术创新实践）课程作品 · 4 人团队 · 6 天冲刺
> 仓库名建议：`playerstock`（本地目录名可为 `innovation`，两者不必一致）

## ⚠️ 合规声明

本项目全程使用**虚拟币**，**不可充值、不可提现、不可兑换**任何实物或货币。选手姓名、战队与位置取自公开可查的 CS2 职业选手信息，但**价格与综合表现评分均为本项目自行设定的模拟数据**，不代表 HLTV 或任何官方统计。本项目与 Valve、HLTV、相关选手及俱乐部**均无关联**，属非官方课程作品，不展示任何官方图片或 Logo。项目仅用于课程学习与演示，不构成任何投资建议或金融产品。

## 一句话介绍

用户用 **5000 初始虚拟币**买卖虚拟选手股，股价随模拟比赛表现与市场供需动态变化；系统同时提供 AI 的 BUY / SELL / HOLD 建议（**仅建议，不自动执行交易**）。

## 技术栈

| 层 | 选型 | 负责人 |
| --- | --- | --- |
| 前端 | Vue 3 + TypeScript + Vite | A |
| 后端 | FastAPI + SQLAlchemy + SQLite | B |
| 定价引擎 | Python 纯函数 + 模拟赛数据发生器 | C |
| 智能体 | Python + LLM API（可降级为规则版） | D |
| 部署 | Render（前端 Static Site / 后端 Web Service） | D |

## 目录结构

```text
.
├── README.md                     # 本文件
├── .gitignore
├── LICENSE
├── pyproject.toml                # pytest 配置（pythonpath 指向 code/）
├── render.yaml                   # Render 部署蓝图
│
├── code/                         # 全部源码
│   ├── frontend/                 # A：Vue 3 + TS + Vite（见 code/frontend/README.md）
│   ├── backend/                  # B：FastAPI + SQLAlchemy + SQLite
│   │   ├── app/
│   │   │   ├── main.py           # 入口（uvicorn app.main:app）
│   │   │   ├── api/              # health / players / account / trades / positions / prices / ai
│   │   │   ├── models/           # SQLAlchemy 模型
│   │   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   │   └── core/             # 配置、数据库会话
│   │   ├── ai/                   # D：LLM 智能体（密钥只在此层读取，绝不下发前端）
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── core_engine/              # C：定价算法 + 模拟比赛数据（供后端 import）
│       ├── pricing.py
│       ├── simulator.py
│       └── pyproject.toml        # 可选：pip install -e 成独立包
│
├── docs/                         # 课程要求的工程文档（见「文档索引」）
├── tests/                        # 独立测试目录：unit/ + integration/
├── data/seed_players.json        # 固定演示数据（现场展示可复现）
├── scripts/                      # dev.ps1 / seed_db.py / simulate_match.py
└── .github/                      # CI 与 PR 模板
```

## 快速开始

### 0. 环境要求

- Python **3.12 / 3.13**
- Node.js **LTS**（建议 20+）
- Git

### 1. 启动后端

```powershell
cd code/backend
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> ⚠️ **注意启动命令是 `app.main:app`，不是 `main:app`**。本项目后端采用 `code/backend/app/` 包结构（见文末「已知偏差」），与 6 天手册里的 `main.py` 直达写法不同。

验收：

- <http://127.0.0.1:8000/> → 返回项目信息
- <http://127.0.0.1:8000/api/health> → `{"status": "ok", "service": "playerstock-backend"}`
- <http://127.0.0.1:8000/docs> → Swagger 交互式文档

### 2. 启动前端（A 同学第 1 天）

> ⚠️ `code/frontend/` 当前只有一份说明文件，而脚手架要求目标目录为空，
> 直接跑 `npm create vue` 会因"目录非空"失败。先把说明移走（对应 `docs/mgmt/milestones.md` 的 T1-04）。

```powershell
Move-Item code/frontend/README.md docs/software/frontend_setup.md
```

```powershell
npm create vue@latest code/frontend
# 选项：TypeScript=Yes / JSX=No / Vue Router=Yes / Pinia=No
#       Vitest=Yes / E2E=No / ESLint=Yes / Prettier=Yes
cd code/frontend
npm install
Copy-Item .env.example .env.local   # 若已有 .env.example
npm run dev                          # http://localhost:5173
```

> `code/frontend/` 目录当前只有一份说明文件，由 A 同学用官方脚手架生成，**不要手工预置文件**，否则 `npm create vue` 会因目录非空而失败。

### 3. 初始化演示数据

```powershell
python scripts/seed_db.py        # 将 data/seed_players.json 写入数据库
python scripts/simulate_match.py # 生成一轮模拟比赛并触发价格更新
```

### 4. 跑测试

```powershell
# 在仓库根目录（pyproject.toml 已配置 pythonpath = ["code/backend", "code/core_engine", "code"]）
pip install -r code/backend/requirements.txt
python -m pytest
```

## 四人分工

| 成员 | 主责 | 关键交付 | 不负责 |
| --- | --- | --- | --- |
| **A** | 前端负责人 | 行情页、选手详情、买卖、持仓、交易记录、折线图、AI 建议展示 | 交易规则、数据库、定价算法 |
| **B** | 后端与交易系统 | 用户虚拟资金、买入卖出、持仓、交易流水、数据库读写、事务一致性 | 页面样式、评分算法、提示词 |
| **C** | 行情与定价 | 模拟赛事数据、表现评分、价格更新算法、价格历史与涨跌原因 | 资金结算、前端、LLM 调用 |
| **D** | AI 智能体 / 测试 / 部署 / 文档 | AI 分析接口、集成测试、线上部署、README 与答辩材料 | 不一个人包办全部测试 |

**文档归属（补充约定）**：`docs/requirements/`、`docs/mgmt/`、`docs/acceptance/` 由 **D 牵头**，A/B/C 各自补齐本模块章节（需求条目、风险条目、测试用例）。否则第 6 天会集中爆炸。

### 联系方式

> 沟通入口统一为**课程项目群（微信群）+ GitHub Issues**；不把私人联系方式写进公开仓库；以下为协作入口与写权限边界，对应 `project_management_plan.md` §8.1。

| 成员 | 负责目录 | 沟通入口 | 升级路径 |
| --- | --- | --- | --- |
| A | `code/frontend/` | 课程项目群 + GitHub Issues | 前端阻塞影响验收时直接找 D 升级 |
| B | `code/backend/app/{api,models,schemas,core}`、`requirements.txt` | 课程项目群 + GitHub Issues | 接口字段有异议 → 契约评审，2 小时内定 |
| C | `code/core_engine/`、`data/seed_players.json` | 课程项目群 + GitHub Issues | 价格口径与 B 冲突时以 `api_contract.md` 为准 |
| D | `code/backend/ai/`、`docs/`、`.github/`、`render.yaml` | 课程项目群 + GitHub Issues | 协调人，负责汇总进度与风险升级 |

> GitHub 协作账号（取自 `git log` 提交记录）：`July75-bit`（仓库所有者）、`wlkaqw`、`weedflame`（A）、`Hu De Hao`（B）、`fusde0`（C）。

## 接口一览

接口契约以 [`docs/software/api_contract.md`](docs/software/api_contract.md) 为准，第 1 天确认后**不再随意改字段**。

| 功能 | 接口 | 对接人 |
| --- | --- | --- |
| 健康检查 | `GET /api/health` | 全员 |
| 查询市场选手 | `GET /api/players` | A + B |
| 查询单个选手 | `GET /api/players/{id}` | A + B |
| 查询账户 | `GET /api/account` | A + B |
| 买入 | `POST /api/trades/buy` | A + B |
| 卖出 | `POST /api/trades/sell` | A + B |
| 查询持仓 | `GET /api/positions` | A + B |
| 查询交易历史 | `GET /api/trades` | A + B |
| 查询价格历史 | `GET /api/players/{id}/prices` | A + B + C |
| 获取 AI 分析 | `GET /api/analysis/{player_id}` | A + B + D |

买入请求统一结构：

```json
{ "player_id": 1, "quantity": 2 }
```

成功响应统一结构（交易是否成功**以后端数据库为准**，不允许前端只改数字）：

```json
{ "success": true, "message": "买入成功", "balance": 4748.00, "player_id": 1, "quantity": 2 }
```

## 交易规则（稳定层）

- 新用户注册赠送 **5000 虚拟币**，每日签到补给固定额度
- 单选手持仓上限 **50 股**
- 比赛进行期间对应选手**暂停交易**，结算后恢复
- 数量必须为正整数；余额充足才能买入；持仓足够才能卖出
- 所有交易记录持久化，持仓与流水按时间倒序查询

## 文档索引

| 目录 | 内容 | 负责人 |
| --- | --- | --- |
| [`docs/requirements/`](docs/requirements/) | 问题定义、功能/非功能需求、用户故事、机制设计、线框图 | D 牵头 |
| [`docs/algorithm/`](docs/algorithm/) | 定价模型、AI 提示词设计、智能体回测报告 | C + D |
| [`docs/software/`](docs/software/) | 系统架构、接口契约、数据库设计、部署说明、交互原型（[`prototype/index.html`](docs/software/prototype/index.html)） | B + D |
| [`docs/mgmt/`](docs/mgmt/) | 沟通计划、风险计划、里程碑与 WBS | D |
| [`docs/acceptance/`](docs/acceptance/) | 测试计划、测试报告、用户手册、合规声明、代码质量报告 | D |
| [`docs/presentation/`](docs/presentation/) | 答辩幻灯片 | 全员 |
| [`docs/retrospection/`](docs/retrospection/) | 每日站会记录与复盘 | 全员 |

> 额外参考：[`docs/software/agent_workflow_design.md`](docs/software/agent_workflow_design.md)（AI Agent 工作流模式选型与完善路线，非课程交付物，供答辩加分参考；由 A 于第 4 天提交，待团队评审）。

## 部署（Render）

仓库根目录的 [`render.yaml`](render.yaml) 已配置两个服务：

- 后端 Web Service：Root Directory `code/backend`，Start Command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 前端 Static Site：Root Directory `code/frontend`，Publish Directory `dist`

> ⚠️ **SQLite 持久化**：Render 默认文件系统是临时的，重启/重新部署会丢数据。必须挂载 Persistent Disk（付费）或改用托管 PostgreSQL，详见 [`docs/software/deployment.md`](docs/software/deployment.md)。验收标准不是"网站能打开"，而是"交易完成后数据能保存"。

## 已知偏差（与原 6 天手册不一致处，四人必须知悉）

1. **后端入口路径**：手册用 `backend/main.py` + `uvicorn main:app`；本项目用 `code/backend/app/main.py` + `uvicorn app.main:app`。理由：路由/模型/schema 分层，避免单文件膨胀。
2. **目录按课程模板组织**：源码统一放在 `code/` 下（`code/backend`、`code/frontend`、`code/core_engine`）。理由：① 课程要求的仓库结构就是 `code/{backend,frontend,core_engine}`；② 定价算法独立成 `code/core_engine`，后端通过 `code/` 加入 `sys.path` 或 `pip install -e code/core_engine` 导入；③ AI 层必须留在 `code/backend/ai/`——手册 D2 要求"避免把 API 密钥暴露到前端"，只有后端进程内才能安全读环境变量。
3. **`code/frontend/` 尚未生成**：由 A 用 `npm create vue@latest` 生成，见 `code/frontend/README.md`。
4. **依赖未锁版本**：`code/backend/requirements.txt` 沿用手册的清单但未固定版本号。第 1 天环境跑通后，请执行 `pip freeze > requirements.lock.txt` 提交，满足课程"可复现"要求。
5. **分支**：`main` 为生产分支、`develop` 为集成分支，均已存在并绑定远程 `origin`；日常开发走 `feat/*` 分支合并回 `develop`。

## 每日验收（对齐 6 天计划）

| 天 | 全队必须有的可见结果 |
| --- | --- |
| 第 1 天 | 四人环境可运行；前端连上后端；接口字段确认 |
| 第 2 天 | 市场数据、交易接口、定价脚本、AI 原型各自跑通 |
| 第 3 天 | 真实跑通「查行情 → 买入 → 看持仓 → 卖出」；数据入库 |
| 第 4 天 | 折线图 + AI 建议展示；异常测试通过 |
| 第 5 天 | 线上地址可访问，线上买卖/查询/AI 各成功一次 |
| 第 6 天 | 回归测试、文档、PPT；演示流程完整演练 ≥2 次 |
