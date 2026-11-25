---
theme: default
colorSchema: light
title: PlayerStock 结课审查
info: |
  软件新技术创新实践课程 · 结课项目审查
  产品、设计、测试与演示
class: text-left
highlighter: shiki
lineNumbers: false
drawings: false
transition: slide-left
mdc: true
fonts:
  sans: 'Microsoft YaHei, PingFang SC, Noto Sans SC, sans-serif'
  mono: 'Consolas, Menlo, monospace'
---

<div class="body">

<div class="cover-title">PlayerStock</div>

<div class="text-2xl font-bold mt-3">CS2 虚拟选手股交易系统</div>

<div class="excerpt text-lg mt-2">用信用点买卖 CS2 选手股，价格随模拟比赛表现变化</div>

<div class="mt-8 flex gap-2 flex-wrap">
  <span class="pill pill-accent">纯积分制 · 无充值 / 提现 / 兑换</span>
  <span class="pill">16 名选手 · 8 支战队</span>
  <span class="pill">智能体查行情、给建议</span>
</div>

<div class="mt-10 small muted">
  有请下一组 ｜ 王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）<br>
  软件新技术创新实践课程 · 2026-11 · 结课项目审查
</div>

<div class="mt-4 small">
  <a class="pdf-link" href="./playerstock_defense.pdf">📄 下载完整材料 PDF</a>
</div>

</div>

<!--
【15 秒】老师们好，我们是「有请下一组」。我们做的项目叫 PlayerStock。系统根据模拟比赛给 CS2 选手股定价，用户可以用信用点买卖。详情页也会展示智能体的建议和依据。
-->

---
layout: default
---

<div class="kicker">01 产品设计 · 1.1 定位与分工</div>

# 给 CS 观众的模拟交易工具

<div class="body">

<div class="grid2">
  <div class="card" v-click>
    <div class="accent font-bold text-sm">产品定位</div>
    <div class="text-lg font-bold mt-2 leading-relaxed">看 CS 比赛时觉得某位选手状态好，可以用信用点试试自己的判断。</div>
    <div class="small muted mt-4">纯信用点，不可充值 / 提现 / 兑换</div>
    <div class="border-t border-#e3ded4 mt-3 pt-3">
      <div class="small font-bold">价格和交易都能回查</div>
      <ul class="clean">
        <li><b>涨跌有原因</b>：点开价格曲线就能看</li>
        <li><b>交易有记录</b>：买卖记录随时能查</li>
        <li><b>只用信用点</b>：不能充值、提现或兑换</li>
      </ul>
    </div>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click><div class="accent small font-bold">目标用户</div><div class="small muted">关注 CS 比赛、对选手发挥有个人判断的普通观众。</div></div>
    <div class="card" v-click><div class="accent small font-bold">试用与推广</div><div class="small muted">大赛期间分享涨跌复盘，先在校园电竞社群找人试用。</div></div>
    <div class="card" v-click><div class="accent small font-bold">团队分工</div><div class="small muted">4 人各自负责独立模块：前端交互 / 后端与交易 / 定价与数据 / AI、测试与部署。</div></div>
  </div>
</div>

</div>

<!--
【20 秒】这个项目面向平时看 CS 比赛的观众。比如你看好一位选手，可以用信用点试着买入，再结合价格曲线和自己的交易记录复盘。我们四个人分工完成了前端、后端交易、定价和数据，以及智能体、测试和部署。
-->

---
layout: default
---

<div class="kicker">01 产品设计 · 1.2 核心玩法</div>

# 选手股的模拟买卖

<div class="body">

<div class="dark-band text-base font-bold leading-relaxed" v-click>
系统按模拟比赛表现更新价格。用户看行情、决定买卖，再回头看自己的判断准不准。
</div>

<div class="grid3">
  <div class="card" v-click><div class="accent small font-bold">先看行情</div><div class="font-bold text-sm mt-1">首页简报列出涨跌和停牌选手</div></div>
  <div class="card" v-click><div class="accent small font-bold">再看原因</div><div class="font-bold text-sm mt-1">点开选手详情，对照历史曲线看涨跌原因</div></div>
  <div class="card" v-click><div class="accent small font-bold">模型不可用时</div><div class="font-bold text-sm mt-1">后端仍可用时，按规则给建议，买卖照常</div></div>
</div>

<div class="flex gap-2 flex-wrap" v-click>
  <span class="pill">5000 初始信用点</span><span class="pill">16 名选手 / 8 支战队</span>
  <span class="pill">11 个价格历史点</span><span class="pill">0 充值 / 0 提现 / 0 兑换</span>
</div>

</div>

<!--
【30 秒】进入市场后，可以先看简报，再点开感兴趣的选手。详情页有价格曲线和每次涨跌的原因。成交后，持仓和流水会随之更新。演示包含 16 名选手和 8 支战队，初始余额是 5000 信用点。
-->

---
layout: default
---

<div class="kicker">02 设计取舍</div>

# 五项设计取舍

<div class="body">

<div class="grid2">
  <div class="card" v-click><div class="flex gap-3"><div class="metric">01</div><div><div class="accent small font-bold">先看简报</div><div class="font-bold">打开首页就能看到市场变化</div><div class="small">想看细节再展开。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">02</div><div><div class="accent small font-bold">同页完成</div><div class="font-bold">选手详情页就能看走势和买卖</div><div class="small">价格、建议和买卖按钮放在一起。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">03</div><div><div class="accent small font-bold">先看关键数据</div><div class="font-bold">选手卡突出价格和涨跌</div><div class="small">桌面端一屏能看 6 张卡。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">04</div><div><div class="accent small font-bold">按规则算价</div><div class="font-bold">价格和交易都按代码里的规则处理</div><div class="small">模型服务出问题，买卖照常。</div></div></div></div>
</div>

<div class="card" v-click><div class="flex gap-3"><div class="metric">05</div><div><div class="accent small font-bold">权限隔离</div><div class="font-bold">买卖由用户自己确认</div><div class="small">智能体可以查行情和给建议。账户余额随实际成交更新。</div></div></div></div>

</div>

<!--
【30 秒】首页把市场简报放在前面，详细信息可以按需展开。选手详情页把走势、建议和买卖放在一起。定价和交易都有明确的规则，模型服务暂时不可用时，买卖仍可继续。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.1 界面设计</div>

# 市场页和选手详情页

<div class="body">

<div class="grid2">
  <div class="flex flex-col gap-2">
    <div v-click>
      <img class="shot" src="./assets/market-light.png" alt="市场页" />
      <div class="small muted mt-2">市场页：顶部简报 + 条件筛选 + 3 列选手卡</div>
    </div>
    <ul class="clean" v-click>
      <li>先看市场简报</li>
      <li>一屏 6 张卡片，3 列栅格对齐</li>
      <li>筛选和排序在当前页完成</li>
    </ul>
  </div>
  <div class="flex flex-col gap-2">
    <div v-click>
      <img class="shot" src="./assets/detail-light.png" alt="详情页" />
      <div class="small muted mt-2">详情页：历史曲线 + 智能体建议 + 下单面板</div>
    </div>
    <ul class="clean" v-click>
      <li>左侧看价格走势，右侧直接买入/卖出</li>
      <li>手机底部可切换四个主页面</li>
      <li>支持深色 / 浅色主题切换</li>
    </ul>
  </div>
</div>

</div>

<!--
【30 秒】左边是市场页，可以在这里筛选和排序。右边是选手详情，价格曲线、智能体建议和买卖按钮放在同一页。移动端用底部导航切换主页面。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.2 技术选型</div>

# 技术选型

<div class="body">

<div v-click>

| 层    | 选型与版本（完整版本表见 README）                                         | 选用理由               |
| ---- | ------------------------------------------------------------ | ------------------ |
| 前端   | Vue 3.5 · Vue Router 5.4 · Vite 8.3 · TS 6.0 · Vitest 4.1    | 轻量、构建快、类型检查完善      |
| 后端   | Python 3.12 · FastAPI 0.161 · SQLAlchemy 2.1 · Pydantic 2.14 | 接口文档自动生成、路由组织清晰    |
| 数据   | 本地 SQLite / 线上 Render Postgres（psycopg2）                     | 本地零配置调试，线上持久化存储    |
| AI   | DeepSeek API（OpenAI 兼容）+ rule_fallback                       | 生成自然语言分析，异常时降级本地规则 |
| 部署   | Render：Static Site + Web Service + Cron + Postgres           | 支持免费托管、HTTPS 与复现   |
| 质量工具 | GitHub Actions · ruff · oxlint · eslint · vue-tsc · pytest   | 4 个 CI job 门禁把关    |

</div>

<div class="sage small font-bold" v-click>我们选了团队熟悉、六天内能做完并上线的工具。</div>

</div>

<!--
【25 秒】开发周期是六天，我们选了组里熟悉的技术。前端用 Vue 和 TypeScript，后端用 FastAPI。本地用 SQLite 调试，线上用 PostgreSQL 存数据。智能体接入 DeepSeek，项目部署在 Render。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.3 代码仓库与协作</div>

# 团队分工与开发记录

<div class="body">

<div class="small muted font-bold" v-click>github.com/July75-bit/Innovation ｜ develop ｜ 522 次提交（379 次非合并，统计至 b4674b5）</div>

<div class="grid2">
  <div class="card" v-click>
    <div class="accent small font-bold">提交分布（git shortlog，含合并提交）</div>
    <table class="mt-2">
      <tbody>
      <tr><td>D 王泽棠</td><td>229</td><td>A 倪颢容</td><td>74</td></tr>
      <tr><td>B 胡德昊</td><td>116</td><td>C 刘宏</td><td>103</td></tr>
      </tbody>
    </table>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click><div class="accent small font-bold">任务管理</div><div class="small muted">使用 GitHub Issues + Projects 跟踪进度，14 条缺陷均建有对应 Issue。</div></div>
    <div class="card" v-click><div class="accent small font-bold">CI 检查</div><div class="small muted">包含健康检查、后端、前端及交付物共 4 个 job，每次 push 自动触发。</div></div>
  </div>
</div>

</div>

<!--
【20 秒】代码放在 GitHub，日常开发合入 develop 分支。以页面标注的版本为准，四位成员共有 522 次提交，其中 379 次是非合并提交。我们用 Issues 和 Projects 跟进任务和缺陷。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.4 问题复盘</div>

# 开发和上线时遇到的 6 个问题

<div class="body">

<div v-click>

| 问题                     | 根因                     | 解决方案（已验证）           |
| ---------------------- | ---------------------- | ------------------ |
| 部署后数据重置                | 免费实例使用临时磁盘 + SQLite    | 迁移至 Postgres 并规范连接串 |
| 线上启动报 No module psycopg | SQLAlchemy 2.1 驱动变更    | 补充 psycopg2 依赖及单测  |
| 前端全站接口 CORS 失败         | CORS_ORIGINS 缺失或含尾斜杠   | 精确配置 origin 并线上验证  |
| 简报直接透传模型 JSON          | 未对大模型返回文本做清洗           | 增加后端清洗与前端兜底解析      |
| CI 后端检查报错              | ruff C901 圈复杂度 11 > 10 | 拆分为 6 个独立 helper 函数 |
| 首次访问耗时 33.6 秒          | 免费实例闲置 15 分钟后自动休眠      | 增加 Cron 保活 + 骨架屏 + 重试 |

</div>

<div class="sage small font-bold" v-click>修完后，我们补了测试、监控检查或部署说明。</div>

</div>

<!--
【35 秒】上线时，我们发现 Render 免费实例使用临时磁盘，重启后 SQLite 数据会丢失，所以把线上数据迁到了 PostgreSQL。首页简报也曾显示模型返回的原始 JSON。我们在后端整理文本，并在前端增加了相应的处理。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 缺陷跟踪</div>

# 14 条缺陷的跟踪记录

<div class="body">

<div class="small muted font-bold" v-click>GitHub Issues #22–#35 ｜ P0 3 条 · P1 5 条 · P2 6 条 ｜ 均已关闭</div>

<div class="grid3">
  <div class="card" v-click>
    <div class="accent small font-bold">P0 · 3 条</div>
    <div class="small mt-2">#22 并发超卖、重复入账<br>#29 线上数据库驱动起不来<br>#33 CORS 未配，整站失败</div>
  </div>
  <div class="card" v-click>
    <div class="accent small font-bold">P1 · 5 条</div>
    <div class="small mt-2">#23 买入校验顺序反了<br>#24 清仓触发约束报 500<br>#26 定价文案污染历史<br>#27 停牌选手仍被改价<br>#31 GBK 控制台测试报错</div>
  </div>
  <div class="card" v-click>
    <div class="accent small font-bold">P2 · 6 条</div>
    <div class="small mt-2">#25 得分被拼两遍<br>#28 reason 超长写库失败<br>#30 WAL 文件误入仓库<br>#32 /market 刷新白屏<br>#34 测试日期炸弹<br>#35 脚本写死绝对路径</div>
  </div>
</div>

<div class="sage small font-bold" v-click>可以按编号回查问题和处理过程。#36、#37 另记注册账号的问题。</div>

</div>

<!--
【20 秒】这里列出 GitHub 上编号 22 到 35 的 14 条缺陷。这批记录都已关闭。第 22 条涉及两笔卖单同时处理时可能出现的超卖和重复入账，具体处理过程可以按编号查阅。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5 概要设计</div>

# 系统架构

<div class="body">

<div v-click>

```mermaid
flowchart LR
  B["浏览器<br/>Vue 3 SPA"] --> S["Render Static Site<br/>dist / SPA fallback"]
  S --> A["FastAPI /api<br/>23 个接口 · 11 个路由模块"]
  A --> R["业务规则层<br/>交易事务 / 停牌 / 余额"]
  A --> C["core_engine<br/>模拟比赛 / z-score 定价"]
  A --> I["智能体<br/>模型建议 / 规则建议"]
  R --> D[("Postgres<br/>9 张表")]
  C --> D
  I --> D
  G["GitHub Actions<br/>4 个 job"] -.部署.-> S
  G -.部署.-> A
  H["Cron 巡检<br/>简报新鲜度"] --> A
```

</div>

<div class="grid3">
  <div class="card" v-click><div class="accent small font-bold">部署架构</div><div class="small muted">前端、后端和定时任务部署在 Render</div></div>
  <div class="card" v-click><div class="accent small font-bold">运行状态</div><div class="small muted">查请求日志、健康接口和简报更新时间</div></div>
  <div class="card" v-click><div class="accent small font-bold">价格和建议分开</div><div class="small muted">程序算价格和处理交易，智能体给建议</div></div>
</div>

</div>

<!--
【30 秒】浏览器加载 Vue 页面，前端通过 FastAPI 查询行情或提交订单。定价和交易由后端按规则处理，结果保存在数据库。智能体也会读取相关数据，生成建议并留下分析记录。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.3 算法与 AI</div>

# 选手股的定价规则

<div class="body">

<div class="grid2">
  <div class="card" v-click>
    <div class="accent small font-bold">价格计算规则</div>
    <div class="formula mt-3">P′ = max(1.0, P × (1 + 0.15 · S))</div>
    <div class="small mt-2">新价格 = 原价格 ×（1 + 0.15 × 表现分），底价 1.0</div>
    <ul class="clean mt-2">
      <li>表现分比较选手这一轮和自己过去的表现</li>
      <li>单次涨跌有 ±20% 的上限</li>
      <li>每次调价的原因都能在详情页查到</li>
    </ul>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click>
      <div class="accent small font-bold">智能体的行情分析</div>
      <div class="small mt-2">看价格历史和涨跌原因，给出买入、卖出或观望的建议。</div>
      <div class="small muted mt-2">决策卡会结合账户余额和持仓，估算建议买卖数量。</div>
      <div class="small mt-2">用户可以采纳或忽略建议，下单时再单独确认。</div>
    </div>
    <div class="dark-band small" v-click>
      <b>定价与建议各自独立</b><br>
      同样的输入算出同样的价格。模型服务出问题，定价和交易照常。
    </div>
  </div>
</div>

</div>

<!--
【40 秒】系统先比较选手本轮与以往的表现，再按公式计算新价格。价格最低为 1 个信用点，单次涨跌也有限制。每次变价都附有原因，用户和智能体都可以查到。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.3 智能体设计</div>

# 智能体的分析流程与护栏

<div class="body">

<div class="dark-band text-base font-bold leading-relaxed" v-click>
决策卡先生成建议，再按余额和持仓算计划。多角色分析和工具调用各有自己的入口。
</div>

<div class="grid3" v-click>
  <div class="card"><div class="accent small font-bold">任务编排</div><div class="small mt-1">多角色分析按分析师、风控、交易员的顺序走，后一步会读前一步的结果。</div></div>
  <div class="card"><div class="accent small font-bold">工具调用</div><div class="small mt-1">模型可查最近价格、读演示账户快照、算建议股数，最多跑 3 轮。</div></div>
  <div class="card"><div class="accent small font-bold">护栏</div><div class="small mt-1">基础建议校验 6 个字段。工具只查数据和做计算，采纳只记录选择。</div></div>
</div>

<div class="card" v-click><div class="accent small font-bold">模型没返回可用结果时</div><div class="small mt-1">模型单次调用默认等 20 秒。基础建议遇到缺密钥、超时或格式错误时，会改用规则版。</div></div>

<div class="sage small font-bold" v-click>决策卡和工具演示都有 trace_id，可以回查结果。</div>

</div>

<!--
【30 秒】决策卡先给出建议方向，再根据余额和持仓估算数量。多角色分析依次经过分析师、风控和交易员。工具调用另有演示入口，模型可以在三个工具中选择，最多运行三轮。基础建议会校验字段，模型失败时用规则版。用户点采纳只会留下记录。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.3 智能体设计</div>

# 智能体的数据来源与记忆

<div class="body">

<div class="grid2" v-click>
  <div class="card"><div class="accent small font-bold">记忆</div><div class="small mt-1">本次请求临时整理所需数据。调用、采纳和归因可回查，简报有短时缓存。</div></div>
  <div class="card"><div class="accent small font-bold">领域数据与规则</div><div class="small mt-1">行情和价格历史从关系库取，定价、停牌和仓位规则写在代码里。</div></div>
</div>

<div class="grid2" v-click>
  <div class="card"><div class="accent small font-bold">当前用 SQL 取数</div><div class="small mt-1">数据量小，所需字段明确。当前未接入 RAG、知识图谱或跨会话偏好记忆。</div></div>
  <div class="card"><div class="accent small font-bold">可扩展的方向</div><div class="small mt-1">RAG 找历次复盘，知识图谱核对选手和战队关系，偏好记忆补上用户关注点。</div></div>
</div>

<div class="dark-band small" v-click>当前可以回查建议和采纳记录。用户历史选择暂未用于生成下一次建议。</div>

</div>

<!--
【25 秒】每次请求都会读取当时需要的行情和价格记录，定价、停牌等规则由代码处理。系统保留调用、采纳和价格归因记录，简报也会短时缓存。目前没有接入 RAG、知识图谱或跨会话偏好记忆。以后若扩展，可以分别用它们查阅复盘、核对关系和保留用户的关注点。
-->

---

<div class="kicker">03 产品实现 · 3.5.4 数据库设计</div>

# 数据库中的 9 张表

<div class="body">

<div v-click>

| 分组  | 表名                                              | 关键设计                                     |
| --- | ----------------------------------------------- | ---------------------------------------- |
| 账号  | users / auth_tokens                             | 记录余额与初始本金；Token 有效期 30 天且支持主动撤销          |
| 市场  | players / price_history                         | 价格历史仅追加写入；reason 归因字段非空                  |
| 交易  | positions / trades                              | 流水只追加并记录 balance_after；持仓按(user, player)唯一 |
| 智能体 | agent_traces / decision_logs / price_narratives | 记录每次调用、采纳与归因，业务表只读                       |

</div>

<div class="grid2">
  <div v-click>

```mermaid
erDiagram
  USERS ||--o{ POSITIONS : "持有"
  USERS ||--o{ TRADES : "产生"
  USERS ||--o{ AUTH_TOKENS : "签发"
  PLAYERS ||--o{ POSITIONS : "被持有"
  PLAYERS ||--o{ TRADES : "被交易"
  PLAYERS ||--o{ PRICE_HISTORY : "有历史"
```

</div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click><div class="accent small font-bold">交易的事务处理</div><div class="small muted">余额、持仓和流水在同一个事务里更新。</div></div>
    <div class="card" v-click><div class="accent small font-bold">方便对账</div><div class="small muted">流水记下成交后的余额，可以逐笔核对。</div></div>
  </div>
</div>

</div>

<!--
【25 秒】九张表分别保存账号、市场、交易和智能体记录。一笔交易会在同一个事务里更新余额、持仓和流水。流水还会记下成交后的余额，便于之后对账。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.5 接口设计</div>

# 前后端接口

<div class="body">

<div v-click>

| 分组  | 功能范围            | 接口示例                     |
| --- | --------------- | ------------------------ |
| 行情  | 选手列表、详情查询、历史价格  | GET /api/players         |
| 交易  | 账户资产、买入、卖出、持仓流水 | POST /api/trades/buy     |
| 身份  | 注册、登录、注销、账号删除   | POST /api/auth/login     |
| AI  | 个股建议、市场简报、决策记录  | GET /api/analysis/\{id\} |
| 运维  | 健康检查、数据库自检、日志查询 | GET /api/health          |

</div>

<div class="dark-band small" v-click>常见错误会给中文提示。在线接口文档可直接试用：playerstock-backend-mdlk.onrender.com/docs</div>

</div>

<!--
【20 秒】接口按行情、交易、身份、智能体和运维分组。页面上列了几个常用的例子。各接口的请求和返回格式，都可以在 Swagger 文档里查看。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.6 软件质量</div>

# 代码检查与测试

<div class="body">

<div class="grid4">
  <div class="card" v-click><div class="metric">335</div><div class="small font-bold">后端测试</div><div class="small muted">pytest，默认跳过 live 用例</div></div>
  <div class="card" v-click><div class="metric">186</div><div class="small font-bold">前端测试</div><div class="small muted">Vitest / 23 个测试文件</div></div>
  <div class="card" v-click><div class="metric">98%</div><div class="small font-bold">核心覆盖率</div><div class="small muted">app + core_engine 模块</div></div>
  <div class="card" v-click><div class="metric">4</div><div class="small font-bold">CI 检查</div><div class="small muted">健康、后端、前端、交付物</div></div>
</div>

<div class="grid2">
  <div class="card" v-click><div class="accent small font-bold">运行保障</div>
    <ul class="clean">
      <li>日志记录接口请求和报错，便于排查</li>
      <li>异常：全局统一错误码，前端友好提示</li>
      <li>契约：Pydantic 严格校验入参与出参</li>
      <li>并发：数据库事务 + 条件更新防超卖</li>
      <li>降级：针对 LLM 超时、断网、冷启动做兜底</li>
    </ul>
  </div>
  <div class="card" v-click><div class="accent small font-bold">自动化工具链</div>
    <table>
      <tbody>
      <tr><td>ruff</td><td>代码规范与圈复杂度检查</td></tr>
      <tr><td>oxlint / eslint</td><td>检查前端代码写法</td></tr>
      <tr><td>vue-tsc</td><td>构建阶段强制类型检查</td></tr>
      <tr><td>Vitest / pytest</td><td>覆盖单元、集成、评测与并发场景</td></tr>
      <tr><td>GitHub Actions</td><td>检查仓库、前后端和交付材料</td></tr>
      </tbody>
    </table>
  </div>
</div>

</div>

<!--
【25 秒】后端用 pytest，前端用 Vitest。GitHub Actions 也会执行代码检查和构建。这里以并发卖出为例，同一个数据库事务配合条件更新，可以防止两笔卖单同时扣减时出现超卖。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.7 代码统计</div>

# 代码与文档统计

<div class="body">

<div v-click>

| 语言           | 文件数 | 行数     |
| ------------ | --- | ------ |
| Python       | 111 | 16,790 |
| Vue          | 21  | 8,992  |
| TypeScript   | 49  | 6,410  |
| CSS          | 4   | 969    |
| HTML         | 3   | 1,082  |
| Markdown（文档） | 70  | 8,270  |

</div>

<div class="grid2">
  <div class="card" v-click><div class="accent small font-bold">模块规模</div><div class="small muted">前端包含 8 个视图、12 个组件；后端包含 11 个路由模块、9 个 AI 模块。</div></div>
  <div class="dark-band small" v-click><b>团队协作与 AI 辅助</b><br>按 Git 作者统计，含合并提交。D 229、B 116、C 103、A 74。AI 帮忙写部分测试和文档，核心交易代码由团队编写、互相评审。</div>
</div>

</div>

<!--
【15 秒】表中按文件类型列出了代码和文档行数。成员贡献按 Git 提交作者统计，胡德昊的两个作者身份合并计数。AI 参与了部分测试和文档，核心交易代码由团队编写和评审。
-->

---
layout: default
---

<div class="kicker">验收 · 测试与容量</div>

# 用户测试、智能体评测与压测

<div class="body">

<div class="grid2">
  <div class="card" v-click><div class="metric">33 项</div><div class="small font-bold">用户验收测试</div><div class="sage small font-bold">32 通过 / 1 部分通过</div><div class="small muted">测了日常操作、错误提示和边界情况</div></div>
  <div class="card" v-click><div class="metric">16/16</div><div class="small font-bold">AI 输出契约评测</div><div class="sage small font-bold">source=llm 100% · P95 3.39s</div><div class="small muted">6 个字段完整度与合规校验均通过</div></div>
  <div class="card" v-click><div class="metric">11/11</div><div class="small font-bold">安全红队测试</div><div class="sage small font-bold">提示注入 / 越权 / 伪造来源</div><div class="small muted">全部拦截，并有对应审计记录</div></div>
  <div class="card" v-click><div class="metric">38 req/s</div><div class="small font-bold">只读接口压测</div><div class="sage small font-bold">≈190 人同时在线 · 0 错误</div><div class="small muted">当前瓶颈在于免费托管实例规格</div></div>
</div>

<div class="small muted" v-click>两组互测各 33 题。赛事数据是模拟的，未评估真实比赛预测准确率。</div>

<div class="card" v-click><div class="small">证据索引：docs/acceptance/evidence（147 张截图）· test_report.md · agent_eval_report.md · load_test_report.md</div></div>

</div>

<!--
【20 秒】33 项用户测试中，32 项通过，1 项部分通过。线上评测的 16 次智能体输出都通过了字段校验。只读接口压测达到每秒约 38 次请求，没有报错。这里的比赛数据是模拟的，评测范围限于系统行为。
-->

---
layout: default
---

<div class="kicker">演示</div>

# 现场演示（约 2 分钟）

<div class="body">

<div class="grid3">
  <div class="card" v-click><div class="accent font-bold">01 市场页</div><div class="small muted mt-1">查看顶部简报与 3 列选手行情、停牌状态</div></div>
  <div class="card" v-click><div class="accent font-bold">02 详情页</div><div class="small muted mt-1">查看历史价格曲线、智能体建议与停牌提示</div></div>
  <div class="card" v-click><div class="accent font-bold">03 买入下单</div><div class="small muted mt-1">模拟买入 2 股，验证余额、持仓与流水同步更新</div></div>
  <div class="card" v-click><div class="accent font-bold">04 资产复盘</div><div class="small muted mt-1">进入个人页查看资产曲线与成交统计</div></div>
  <div class="card" v-click><div class="accent font-bold">05 降级演示</div><div class="small muted mt-1">验证停牌拦截与无 Key 时的规则兜底</div></div>
  <div class="card" v-click><div class="accent font-bold">06 回到市场</div><div class="small muted mt-1">回到行情列表，结束演示</div></div>
</div>

<div class="small muted" v-click>演示过程中不切换窗口；若遇网络波动则刷新只读页面或切换备用录屏。</div>

</div>

<!--
【5 秒】接下来从市场页进入一位选手的详情，先看智能体建议，再买入两股，最后查看持仓和流水。
-->

---
layout: default
---

<div class="kicker">结课审查</div>

# 谢谢，请老师指导

<div class="body">

<div class="grid3">
  <div class="card">
    <div class="accent font-bold">在线演示</div>
    <div class="small muted mt-2">playerstock-frontend-mdlk.onrender.com</div>
  </div>
  <div class="card">
    <div class="accent font-bold">源码仓库</div>
    <div class="small muted mt-2">github.com/July75-bit/Innovation</div>
  </div>
  <div class="card">
    <div class="accent font-bold">完整材料</div>
    <div class="small muted mt-2">站点内 /playerstock_defense.pdf</div>
  </div>
</div>

<div class="small muted">有请下一组 · 王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）　｜　2026-11</div>

</div>

<!--
【结束】我们的汇报到这里。最后一页留有在线演示、源码和 PDF 的入口，方便课后查看。谢谢各位老师。
-->
