---
theme: default
title: PlayerStock · 虚拟选手股交易模拟
info: 课程作品答辩 · 8 分钟介绍
class: text-center
highlighter: shiki
lineNumbers: false
drawings:
  persist: false
mdc: true
---

# PlayerStock

## 虚拟选手股交易模拟

<div class="pt-8 text-sm opacity-70">

CS2 选手 · 模拟行情 · 规则化定价 · 只给建议不自动交易的 AI

</div>

<div class="abs-br m-6 text-xs opacity-60">

课程作品答辩 ｜ A 倪颢容 · B 胡德昊 · C 刘宏 · D 王泽棠

</div>

<!--
【0:00–0:10｜10 秒｜D】
一句话开场：我们做的是一个用虚拟币"炒股"CS2 职业选手的模拟交易系统。
先声明合规：全程虚拟币，不可充值、不可提现、不可兑换，不构成任何投资建议。
-->

---
layout: default
---

# 01 我们解决的问题

<div class="grid grid-cols-2 gap-8 pt-4">

<div>

**用户痛点**

- 想"体验交易"，但真实金融市场门槛高、风险真实
- 赛事数据分散，**涨跌没有解释**，只能看热闹
- 已有的模拟炒股产品，标的是公司和财报，**不是自己关心的选手**

</div>

<div>

**目标用户**

- CS2 观众 / 校园赛参与者
- 想验证"我对选手状态的判断准不准"

**我们给的答案**

- 8 名真实 CS2 选手（身份公开、价格与评分为**模拟数据**）
- 每一分钱变化都能回答"**为什么**"

</div>

</div>

<div class="pt-6 text-xs opacity-60">

对应需求：`docs/requirements/problem_definition.md`（5W1H）· `user_stories.md`（7 条 INVEST）

</div>

<!--
【0:10–1:00｜50 秒｜D】
痛点三句话：一，想体验交易但没有安全的沙盒；二，赛事数据看着热闹但没人解释涨跌；
三，现有模拟盘标的是公司，不是你在看的这些选手。
目标用户：看 CS2、并且愿意为"我觉得他能打得更好"付判断的人。
注意措辞：选手身份是真的、公开的；价格和评分是我们自己设的模拟数据——这一句必须说清楚。
-->

---
layout: default
---

# 02 产品长什么样

<div class="grid grid-cols-2 gap-6">

<div>

**四条路由 = 一条完整链路**

- `/` 市场：8 名选手，现价 / 涨跌 / 模拟评分 / 状态
- `/players/:id` 详情：折线图 + 涨跌原因 + AI 建议卡 + 交易面板
- `/positions` 持仓：数量 / 均价 / 市值 / 浮盈
- `/trades` 流水：倒序、每笔带交易后余额

</div>

<div>

<img src="/evidence/01-market.png" class="rounded shadow" style="max-height: 300px" />

<div class="text-xs opacity-60 pt-2">市场页（真实浏览器截图）</div>

</div>

</div>

<div class="pt-4 text-xs opacity-60">

截图证据：`docs/acceptance/evidence/01~16`（16 张真实浏览器验收图）

</div>

<!--
【1:00–1:40｜40 秒｜A 或 D】
强调这不是原型图，是真实跑通的页面：后端 uvicorn + 真实 SQLite/Postgres，
截图全部来自 1280×900 的实机验收。
一句话带过链路：看行情 → 详情看走势和 AI 建议 → 买入 → 持仓 → 卖出 → 流水。
-->

---
layout: default
---

# 03 需求与取舍：做了什么 / 不做什么

| 做了 | 刻意不做（及原因） |
| --- | --- |
| 单演示账户 + 5000 虚拟币 | 注册登录 / JWT：不是课程考察重点，会稀释工期 |
| 8 名选手、价格由比赛表现驱动 | 接入真实赛事 API：接口可用性未知，用固定 seed 的模拟数据保证演示稳定 |
| 交易闭环：买入/卖出/持仓/流水 | 充值、提现、兑换：**合规红线**，一律不做 |
| AI 只给建议，不自动交易 | 多用户 / 撮合盘口：6 天工期做不完，且不影响核心机制 |

<div class="pt-4 text-sm">

**可测量的非功能指标（节选）**：行情 P95 ≤ 300ms（实测 **24ms**）· 交易 P95 ≤ 500ms（实测 **36ms**）· AI 超时 20s 必定降级 · 核心逻辑覆盖率 ≥60%（实测 **91%**）

</div>

<!--
【1:40–2:20｜40 秒｜D】
这一页是答辩的"可信度锚点"：不是我们做不完，是**主动砍**，每条都给了理由。
重点讲"AI 只给建议不自动交易"——这是设计边界，不是能力不足；
以及合规红线（不充值不提现）。
-->

---
layout: default
---

# 04 系统架构

```mermaid
flowchart TB
  UI["Vue 3 + TS + Vite<br/>4 视图 5 组件"] -->|"/api/*"| API["FastAPI<br/>8 个路由模块（7 业务 + 1 只读自检）"]
  API --> CORE["app/core<br/>交易事务 · 价格落库 · 规则"]
  API --> AI["ai/<br/>上下文 + LLM + 规则兜底"]
  CORE --> ENGINE["core_engine<br/>模拟比赛 · 3σ 标准化 · 定价"]
  CORE --> DB[("SQLite 本地/CI<br/>Postgres 线上")]
  AI -.失败.-> FALLBACK["rule_fallback<br/>6 字段不变"]
```

<div class="grid grid-cols-3 gap-4 pt-4 text-sm">

| 层 | 技术 | 版本 |
| --- | --- | --- |
| 前端 | Vue + TypeScript + Vite | **3.5 / 6.0 / 8.2** |
| 后端 | FastAPI + Pydantic | **0.161 / 2.14** |
| 数据 | SQLAlchemy + SQLite/Postgres | **2.1 / PG 18** |

</div>

<!--
【2:20–3:20｜60 秒｜B】
讲三层边界：接口层只管路由和错误码；core 管事务；core_engine 是纯计算、不碰数据库；
ai 只读、永不改余额。
两个设计点必说：
1）定价引擎和后端同仓库但可独立 pip 安装 → C 可以单独跑、单独测；
2）本地 SQLite、线上 Postgres，一套 SQLAlchemy 模型双环境复用 → 免费实例没有持久盘，纯 SQLite 重新部署就丢数据。
-->

---
layout: default
---

# 05 交易正确性：不靠"先查后写"

<div class="grid grid-cols-2 gap-8">

<div>

**问题**：先 `SELECT` 判断余额够不够、再 `UPDATE` 扣款，两条并发请求会同时通过判断 → **超卖**

**做法**：把判断写进 SQL 的 `WHERE`

```sql
UPDATE users SET balance = balance - :amount
 WHERE user_id = :uid AND balance >= :amount;
-- rowcount = 0 → 400 INSUFFICIENT_BALANCE
```

- 加仓：`... AND quantity + :n <= 50`
- 减仓：`... AND quantity > :n`
- 清仓：`DELETE ... AND quantity = :n`（写 0 会违反 CHECK）

</div>

<div>

**实测（BUG-01 修复前）**

两条连接各卖 2 股、实际只持 3 股：

- 卖出 **4 股**，余额 5000.00 → **5504.00**，还剩 1 股
- 凭空多卖一股、多入账

修复后：`test_trades_concurrency.py` 3 条用例，
并发两笔"卖 1"→ `[200, 400]`，只入账一次。

<div class="pt-4 text-xs opacity-60">

两次修复记录：`docs/acceptance/test_report.md` §9 · 机制：`database_design.md` §3.1

</div>

</div>

</div>

<!--
【3:20–4:20｜60 秒｜B】
先讲 bug 现场：5000 变 5504，凭空多卖一股——这是我们第 2 天真实跑出来的。
再讲修法：判断交给数据库，条件更新 + rowcount。
关键一句：这个写法 SQLite 和 Postgres 行为一致，不依赖 SELECT FOR UPDATE（SQLite 会静默忽略它）。
-->

---
layout: default
---

# 06 定价：一条价格是怎么来的

<div class="grid grid-cols-2 gap-8">

<div>

**公式**

```
P(t+1) = max( floor , P(t) × (1 + α·S(t) + β·D(t)) )
S(t)   = clamp( z(t) / 3 , -1 , +1 )     z = 得分相对近 5 场均值的 z-score
```

| 参数 | 值 | 含义 |
| --- | --- | --- |
| α | **0.15** | 表现权重：满格 S=±1 → 单次 ±15% |
| β | 0 | 需求项（本期不用） |
| floor | 1.0 | 价格下限 |
| clamp | **±20%** | 单次涨跌对称上限 |
| 3σ 满格 | `Z_FULL_SCALE=3` | 1σ 记 1/3，避免二值跳动 |

</div>

<div>

**真实一次调价（ZywOo 第 3 轮）**

- 本轮得分 **76.6**，近 5 场均分偏高 → S = **−1.00**
- 108.75 × (1 + 0.15 × −1.00) = 92.44 → 触 −20% 上限前按实际算
- 落库 reason：`本场表现下滑（S=-1.00），价格下跌 15.00%（本轮得分 76.6）`

**可解释性**：`price_history.reason` 必须带 S 和得分，**每条历史价格都能追溯到哪一场、什么得分**

</div>

</div>

<!--
【4:20–5:50｜90 秒｜C】
先说公式三项：当前价 × 表现信号 × clamp，floor 兜底。
重点解释"为什么 z/3 而不是 clamp(z)"：直接用 z 时 1σ 就满格，约 32% 的场次顶格，
价格会二值跳动；除以 3 之后只有真爆发/崩盘才满格，α 的语义也固定成"满格 ±15%"。
然后拿一条真实历史念 reason —— 这是"可解释性"最硬的证据。
-->

---
layout: default
---

# 07 定价的诚实部分：它会长期温和下行

<div class="grid grid-cols-2 gap-8">

<div>

**100 个 seed × 30 轮的稳定性**

| 指标 | 结果 |
| --- | --- |
| 区间收益 | 中位数 **−7.40%**，均值 −6.46% |
| 方向一致率 | **99.99%**（涨跌次数接近 1:1，公式无偏） |
| 单次最大变动 | ≤ **15.01%**，clamp 触发 0 次 |
| ≥4 人盈利的 seed | 17% |

**根因**：① 得分在 100 处被截断，高分段右尾削平 → E[S] 略小于 0；② 乘性更新的波动拖累。

**不是 bug，是机制特性** —— α 调小可收敛（报告里有 α=0.15/0.08/0.05 对比）。

</div>

<div>

**智能体回测（seed 42 / 20 轮）**

| 策略 | 收益率 | 最大回撤 |
| --- | ---: | ---: |
| 规则版 AI | −3.52% | **5.90%** |
| 随机 | −0.59% | 2.59% |
| 买入持有 | −10.78% | 14.88% |

**结论只说一条**：规则版 AI **回撤明显低于买入持有**（3 seed 中 2 次跑赢收益），
但 20 轮样本下不能宣称"稳定跑赢"——LLM 版待有密钥后补跑。

</div>

</div>

<!--
【5:50–7:20｜90 秒｜C + D】
这一页是主动交底：我们自己测出"长期下行"，并且能解释根因。
答辩策略：抢在老师问之前说，可信度比藏起来高得多。
回测结论只讲"回撤优势"这一条，不吹收益——因为随机策略在主 seed 上就跑赢我们。
-->

---
layout: default
---

# 08 AI 智能体：只给建议，永不改余额

<div class="grid grid-cols-2 gap-8">

<div>

**固定 6 字段契约**

```json
{
  "player_id": 1,
  "action": "HOLD",
  "reason": "近 5 个价格点累计变动 +25.5%…",
  "risk_level": "LOW",
  "source": "rule_fallback",
  "disclaimer": "仅为分析建议，不构成投资建议…"
}
```

**降级是设计的一部分**：无密钥 / 超时（20s）/ 非 JSON / 枚举非法
→ **一律 HTTP 200 + `source=rule_fallback`**，绝不 4xx/5xx 阻塞交易

</div>

<div>

**四层测试守住它**

- `test_llm_agent.py` 13 条：注入假 client，不碰网络
- `test_ai_fallback.py` 6 条：阈值规则
- `test_api_ai.py` 7 条：接口契约 / 只读 / 降级
- e2e：调用前后余额与持仓**完全不变**

<div class="pt-4 text-sm">

**为什么规则版也够用**：阈值规则（涨 5% 且评分 <60 → SELL）在演示环境与 LLM 同源可解释，
LLM 是"增量"，不是"命门"。

</div>

</div>

</div>

<!--
【7:20–8:00｜40 秒｜D】
两句核心：6 字段冻结成契约（前端只按这 6 个渲染）；AI 任何故障都返回 200 + 兜底，
"AI 挂了也能交易"。
补一句测试方式：我们的测试全部注入假 client，不依赖网络，CI 上稳定绿。
-->

---
layout: default
---

# 09 工程实践与线上验证

<div class="grid grid-cols-3 gap-6 text-sm">

<div>

**测试**

- **137** 条用例（单元 124 / 集成 13），CI + 本机全绿
- 核心逻辑覆盖率 **91%**（课程要求 ≥60%）
- 已修 **13** 条真实缺陷（含 3 个 P0：并发超卖、部署驱动、线上 CORS）

</div>

<div>

**质量与 CI**

- ruff 分档门槛（业务/测试 / 脚本 / 复杂度）
- 13 条缺陷全部带可复跑用例
- 前端 lint + build + 真机 16 张验收图

</div>

<div>

**线上**

- 前端/后端/Postgres 三服务（Render）
- **TC-401~406 全部通过**
- 重新部署后流水仍 3 条、价格点仍 11 个 → **Postgres 真的生效**

</div>

</div>

<div class="pt-6 text-xs opacity-70">

线上：`playerstock-frontend-mdlk.onrender.com` ／ `playerstock-backend-mdlk.onrender.com`

</div>

<!--
【8:00–8:30｜30 秒｜D】
数字只念三个：137 条、91%、13 条缺陷。
然后一句杀手锏：我们故意重新部署了一次后端，交易流水和 11 个价格点一条没丢——
这证明线上用的是 Postgres，不是临时盘。
-->

---
layout: default
---

# 10 分工、复盘与下一步

<div class="grid grid-cols-2 gap-8">

<div>

**四人分工（按边界）**

| 人 | 负责 |
| --- | --- |
| A 倪颢容 | 前端 4 视图 + 组件 + 真机验收 |
| B 胡德昊 | 后端接口 / 交易事务 / 落库 / 部署 |
| C 刘宏 | 模拟器 + 定价引擎 + 回测 |
| D 王泽棠 | AI / 测试 / 代码质量 / CI / 文档 |

</div>

<div>

**踩过的坑（真话）**

- 并发超卖：先查后写 → 条件更新
- SQLAlchemy 2.1 默认 psycopg3，线上起不来 → 显式 `+psycopg2`
- reason"得分"被拼两遍 → 幂等标记
- 外部交叉测试**没约到组**，我们如实标注延期，用内部互测 + 16 张证据替代

**如果重做**：先定契约再写代码；把定价的下行风险在文档里前移（这次是回测才发现）。

</div>

</div>

<!--
【8:30–8:40｜10 秒｜D 收尾】
最后一页留两个记忆点：一是"所有坑都写进了缺陷清单，每条都有用例"，
二是"没做到的（外部交叉测试）我们直说，不伪造"。
然后交棒演示：接下来 2 分钟，A 给大家走一遍真实交易闭环。
-->

---
layout: center
class: text-center
---

# 演示环节

<div class="pt-6 text-lg">

查行情 → 看走势与原因 → 买入 → 持仓 → 卖出 → 流水

</div>

<div class="pt-10 text-sm opacity-60">

线上地址（演示前 10 分钟已预热）

</div>

<!--
【8:40–10:40｜2 分钟｜A】切换到 docs/presentation/demo-script.md 的步骤执行。
-->
