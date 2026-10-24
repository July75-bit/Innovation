# 交互原型（AI 生成草稿）

> **负责人**：D（用 AI 生成草稿） → A（确认视觉/交互，作为前端实现基线） ｜ **日期**：2026-10-24
> **对应课程要求**：第 2 天工作任务第 2 项 —— 原型展示（`docs/software/prototype`）：提交利用 AI 生成的交互式原型页面。

## 1. 这是什么

`index.html` 是一个**可直接双击打开的单页交互原型**（纯 HTML/CSS/JS，无依赖、无需构建），
把 PlayerStock 的 5 个核心界面与关键交互串起来，用于课程检查点"教师评估原型可行性"和前端实现前评审：

| 界面 | 交互 | 对应真实接口（后续接入） |
| --- | --- | --- |
| 市场行情 | 8 名选手列表、涨跌幅、模拟评分、可交易状态 | `GET /api/players` |
| 选手详情 | 价格大字、涨跌幅、走势折线图（内联 SVG）、最近变化原因 | `GET /api/players/{player_id}`、`GET /api/players/{player_id}/prices` |
| AI 建议卡 | action 徽标 + 风险等级 + 理由 + 免责声明 + `source` | `GET /api/analysis/{player_id}`（固定 6 字段） |
| 交易区 | 数量校验（正整数/余额/持仓/50 股上限/暂停交易）+ 买入/卖出 | `POST /api/trades/buy`、`sell` |
| 持仓 / 流水 | 市值与浮盈、空状态；流水倒序 | `GET /api/positions`、`GET /api/trades` |

数据取自 `data/seed_players.json`（8 名 CS2 选手，身份公开、**价格与评分为项目模拟值**，UI 已标注"模拟"）。
AI 建议复用 `code/backend/ai/fallback.py` 的阈值规则（+5% / -5% / 评分 60、75），所以展示结果与真实接口的规则版一致。

## 2. 怎么打开

- 直接双击 `index.html`（或浏览器打开 `file:///.../docs/software/prototype/index.html`）；
- 想用本地服务器：仓库根执行 `python -m http.server 8080`，访问 `http://127.0.0.1:8080/docs/software/prototype/`。

**重置演示数据**：点页面顶部提示条右侧的「重置演示数据」（刷新即恢复 5000 虚拟币）。

## 3. 生成方式与边界（如实标注）

- 生成方式：2026-10-24 由 D 用 AI 生成（自然语言描述"CS2 选手股交易 + AI 建议、5 个页面、深色金融风、模拟数据标注"后产出），
  再做人工核对：字段名、规则阈值、错误提示文案与 `docs/software/api_contract.md` 一致。
- **这是草稿级资产**：只验证信息架构与交互，不连接后端、不做持久化、刷新即重置；真实实现见 `code/frontend/`（A）。
- 与 `docs/requirements/wireframes/README.md` 的关系：wireframes 是页面要素清单；本原型是同一套要素的**可点击版本**，两者以本原型为视觉基线。

## 4. 已知限制 / 后续

| 项 | 现状 | 后续 |
| --- | --- | --- |
| 数据 | 硬编码 mock | 第 3–4 天 A 接真实接口（`VITE_API_BASE_URL` 不写死） |
| 价格曲线 | 5 个点示意 | 接 `/prices` 后 ≥10 个真实历史点 |
| AI 建议 | 规则版 mock | 接 `/api/analysis/{player_id}`，保留"加载/失败"三态 |
| 错误提示 | 前端校验文案 | 真实实现直接展示后端 `message`（中文直出） |
| 响应式 | 桌面优先，窄屏降级单列 | A 按组件库统一断点 |

> 原型文件不参与 pytest 与 CI 前端构建；仅在 CI「交付物完整性检查」中校验文件存在性（课程第 2 天要求），其余作为文档交付物与评审材料存放。
