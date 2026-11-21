---
theme: default
colorSchema: light
title: PlayerStock 结课审查
info: |
  软件新技术创新实践课程 · 结课项目审查
  产品介绍 + 关键设计 + 演示 + 证据链
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

<div class="text-2xl font-bold mt-3">虚拟选手股交易模拟</div>

<div class="excerpt text-lg mt-2">把「眼力」变成一条可交易、可解释的价格曲线</div>

<div class="mt-8 flex gap-2 flex-wrap">
  <span class="pill pill-accent">看懂比赛，从持有起</span>
  <span class="pill">纯信用点 · 不可充值 / 提现 / 兑换</span>
  <span class="pill">16 名选手 · 8 支战队</span>
  <span class="pill">AI 只给建议</span>
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
【15 秒】老师们好，我们是「有请下一组」，作品叫 PlayerStock：用信用点交易 CS2 选手的虚拟股。说白了，就是把你对选手的判断，变成一条看得懂、能验证、不用真钱的价格曲线。先讲产品，再看两分钟演示，最后给证据。
-->

---
layout: default
---

<div class="kicker">01 产品设计 · 1.1 使命 / 口号 / 策略</div>

# 让判断力变成可解释的价格曲线

<div class="body">

<div class="grid2">
  <div class="card" v-click>
    <div class="accent font-bold text-sm">使命 Mission</div>
    <div class="text-lg font-bold mt-2 leading-relaxed">让看比赛的人，把判断变成一条看得懂、能验证、不花钱的价格曲线。</div>
    <div class="small muted mt-4">纯信用点，不可充值 / 提现 / 兑换</div>
    <div class="border-t border-#e3ded4 mt-3 pt-3">
      <div class="small font-bold">三条可验证原则</div>
      <ul class="clean">
        <li><b>可解释</b>：每次涨跌都能说出原因</li>
        <li><b>可验证</b>：判断对错看历史价格</li>
        <li><b>零风险</b>：投入的是判断力与注意力，不是钱</li>
      </ul>
    </div>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click><div class="accent small font-bold">目标用户</div><div class="small muted">看 CS 比赛、对选手有判断、但不想用真钱的人。</div></div>
    <div class="card" v-click><div class="accent small font-bold">如何获得用户</div><div class="small muted">赛事节点（Major/IEM/BLAST）+ 每日涨跌内容 + 校园电竞社群。</div></div>
    <div class="card" v-click><div class="accent small font-bold">团队优势</div><div class="small muted">4 人分工不重叠：前端 / 后端与交易 / 定价与数据 / AI·测试·部署。</div></div>
  </div>
</div>

<div class="small muted" v-click><b class="accent">跟别人比，</b>我们只比三件事：交易的是选手、涨跌能解释、不碰真钱。</div>

</div>

<!--
【20 秒】先说我们是干嘛的：看懂比赛，从持有起。用户是看 CS 比赛、对选手有感觉、但不想花真钱的人。我们没推广预算，靠赛事、日报和校园社群慢慢来。四个人分工不重叠。跟别人比，我们比的是选手本身、能解释、不碰真钱。
-->

---
layout: default
---

<div class="kicker">01 产品设计 · 1.2 产品定义 / 用户故事</div>

# 一个虚拟的选手股市场

<div class="body">

<div class="dark-band text-base font-bold leading-relaxed" v-click>
给看比赛的人一个虚拟选手股市场：选手表现变成价格，每条涨跌都有原因。不做竞猜，不碰真钱。
</div>

<div class="sage small font-bold" v-click>解决三个问题：判断没处验证 · 涨跌看不懂 · 门槛高</div>

<div class="grid3">
  <div class="card" v-click><div class="accent small font-bold">交易新手</div><div class="font-bold text-sm mt-1">打开首页 60 秒，知道该不该买</div></div>
  <div class="card" v-click><div class="accent small font-bold">行情玩家</div><div class="font-bold text-sm mt-1">点开选手，看懂为什么涨、为什么跌</div></div>
  <div class="card" v-click><div class="accent small font-bold">演示者 / 老师</div><div class="font-bold text-sm mt-1">断网、没有 API Key，也能完成交易</div></div>
</div>

<div class="flex gap-2 flex-wrap" v-click>
  <span class="pill">5000 信用点开局</span><span class="pill">16 名选手 / 8 支战队</span>
  <span class="pill">11 个价格历史点</span><span class="pill">0 充值 / 0 提现 / 0 兑换</span>
</div>

</div>

<!--
【35 秒】一句话：给看比赛的人一个虚拟选手股市场，选手表现变成价格，每条涨跌都有原因。三个用户故事对应新手、行情玩家和演示者。规模是 16 名选手、8 支战队，每人 11 个价格点，5000 信用点开局，全是虚拟的。
-->

---
layout: default
---

<div class="kicker">02 产品设计应用的原则</div>

# 五个原则，五个取舍

<div class="body">

<div class="grid2">
  <div class="card" v-click><div class="flex gap-3"><div class="metric">01</div><div><div class="accent small font-bold">需求原则</div><div class="font-bold">先回答该不该买</div><div class="small muted">首屏给结论，证据按需展开。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">02</div><div><div class="accent small font-bold">信息原则</div><div class="font-bold">一屏完成行情 → 建议 → 下单</div><div class="small muted">不来回跳。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">03</div><div><div class="accent small font-bold">简化原则</div><div class="font-bold">纸感、低密度、可读</div><div class="small muted">一屏 6 张卡，去掉玻璃。</div></div></div></div>
  <div class="card" v-click><div class="flex gap-3"><div class="metric">04</div><div><div class="accent small font-bold">系统原则</div><div class="font-bold">交易写死，AI 只建议</div><div class="small muted">AI 挂了，交易照常。</div></div></div></div>
</div>

<div class="card" v-click><div class="flex gap-3"><div class="metric">05</div><div><div class="accent small font-bold">合规原则</div><div class="font-bold">零真实资金，AI 只能看不能动</div><div class="small muted">0 充值 / 提现 / 兑换；每次调用留审计。</div></div></div></div>

</div>

<!--
【35 秒】这一页不讲条文，讲五个取舍：先给结论、一屏做完、纸感低密度、交易写死让 AI 挂了也能用、合规零真钱。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.1 用户体验设计</div>

# 界面：看数据、做判断，一屏够用

<div class="body">

<div class="grid2">
  <div class="flex flex-col gap-2">
    <div v-click>
      <img class="shot" src="./assets/market-light.png" alt="市场页" />
      <div class="small muted mt-2">市场页：一行简报 + 筛选 + 3 列选手卡</div>
    </div>
    <ul class="clean" v-click>
      <li>首屏先给结论</li>
      <li>一屏 6 张卡，3 列对齐</li>
      <li>筛选排序不跳页</li>
    </ul>
  </div>
  <div class="flex flex-col gap-2">
    <div v-click>
      <img class="shot" src="./assets/detail-light.png" alt="详情页" />
      <div class="small muted mt-2">详情页：价格曲线 + AI 建议 + 交易同屏</div>
    </div>
    <ul class="clean" v-click>
      <li>左边看曲线，右边下单</li>
      <li>手机 4 个 Tab，顶栏头像入口</li>
      <li>深浅色一键切</li>
    </ul>
  </div>
</div>

</div>

<!--
【35 秒】界面就这样：桌面市场一屏 6 张卡，简报先给结论；详情页左边曲线，右边 AI 建议和下单；手机上 4 个 Tab。左右都是先看图、再看要点。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.2 技术选型</div>

# 轻量、能复现，我们 hold 得住

<div class="body">

<div v-click>

| 层 | 选型与版本（完整版本表在 README） | 为什么选它 |
| --- | --- | --- |
| 前端 | Vue 3.5 · Vue Router 5.4 · Vite 8.3 · TS 6.0 · Vitest 4.1 | 轻、快、类型安全 |
| 后端 | Python 3.12 · FastAPI 0.161 · SQLAlchemy 2.1 · Pydantic 2.14 | 自动文档、路由清晰 |
| 数据 | 本地 SQLite / 线上 Render Postgres（psycopg2） | 本地零配置、线上持久化 |
| AI | DeepSeek API（OpenAI 兼容）+ rule_fallback | 能说人话，挂了走规则兜底 |
| 部署 | Render：Static Site + Web Service + Cron + Postgres | 免费、HTTPS、可复现 |
| 质量工具 | GitHub Actions · ruff · oxlint · eslint · vue-tsc · pytest | 4 个 job 门禁，CI 同口径 |

</div>

<div class="sage small font-bold" v-click>原则：不选简历上最响的，选 6 天能交付、能测试、能部署、能讲清楚的。</div>

</div>

<!--
【30 秒】选型就一个原则：轻、能复现、我们四个人 hold 得住。前端 Vue + Vite，后端 FastAPI + SQLAlchemy，线上 Postgres；AI 用 DeepSeek，留规则兜底；部署交给 Render 和 GitHub Actions。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.3 代码仓库与协作</div>

# 466 次提交、5 位贡献者、4 道 CI 门禁

<div class="body">

<div class="small muted font-bold" v-click>github.com/July75-bit/Innovation ｜ develop ｜ 466 次提交（334 次非合并）</div>

<div class="grid2">
  <div class="card" v-click>
    <div class="accent small font-bold">提交分布（GitHub Pulse / git shortlog，含合并提交）</div>
    <table class="mt-2">
      <tbody>
      <tr><td>D 王泽棠</td><td>197</td><td>A 倪颢容</td><td>74</td></tr>
      <tr><td>B 胡德昊</td><td>114</td><td>C 刘宏</td><td>81</td></tr>
      </tbody>
    </table>
      </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click><div class="accent small font-bold">协作</div><div class="small muted">Issues + Projects 管任务，14 条缺陷都有 Issue。</div></div>
    <div class="card" v-click><div class="accent small font-bold">CI 4 个 job</div><div class="small muted">卫生、后端、前端、交付物，每次 push 都跑。</div></div>
  </div>
</div>

</div>

<!--
【25 秒】仓库在 GitHub，develop 是部署分支，466 次提交、334 次非合并。四个人都在提交。协作靠 Issues 和 Projects，CI 4 个 job，每次 push 都跑。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.4 生命周期问题复盘</div>

# 踩过的 6 个坑

<div class="body">

<div v-click>

| 问题 | 原因 | 解决办法（都已验证） |
| --- | --- | --- |
| 部署后数据全丢 | 免费实例临时盘 + SQLite | 迁 Postgres，连接串归一化 |
| 线上启动 No module psycopg | SQLAlchemy 2.1 驱动变了 | 补 psycopg2，加单测 |
| 前端全站 CORS 失败 | CORS_ORIGINS 未填 / 带尾斜杠 | 精确 origin，线上验证 |
| 简报把模型 JSON 透传 | 模型输出没清洗 | 后端清洗，前端兜底 |
| CI 后端 14 秒红 | ruff C901 圈复杂度 11 > 10 | 拆成 6 个 helper |
| 首次打开 33.6 秒 | 免费实例 15 分钟休眠 | 保温 cron + 骨架屏 + 重试 |

</div>

<div class="sage small font-bold" v-click>每个问题都补了测试、监控或文档，别再踩同一个坑。</div>

</div>

<!--
【40 秒】挑了 6 个真踩过的坑：数据全丢、psycopg 驱动、CORS、模型输出没洗、CI 圈复杂度、冷启动。每个都说清原因和怎么修的，修完都有测试或线上验证。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5 概要设计</div>

# 系统架构：前后端分开，交易内核写死

<div class="body">

<div v-click>

```mermaid
flowchart LR
  B["浏览器<br/>Vue 3 SPA"] --> S["Render Static Site<br/>dist / SPA fallback"]
  S --> A["FastAPI /api<br/>23 个接口 · 11 个路由模块"]
  A --> R["业务规则层<br/>交易事务 / 停牌 / 余额"]
  A --> C["core_engine<br/>模拟比赛 / z-score 定价"]
  A --> I["ai/<br/>LLM + 规则兜底"]
  R --> D[("Postgres<br/>9 张表")]
  C --> D
  I --> D
  G["GitHub Actions<br/>4 个 job"] -.部署.-> S
  G -.部署.-> A
  H["Cron 巡检<br/>简报新鲜度"] --> A
```

</div>

<div class="grid3">
  <div class="card" v-click><div class="accent small font-bold">部署</div><div class="small muted">Render 四件套，Blueprint 能复现</div></div>
  <div class="card" v-click><div class="accent small font-bold">可观测性</div><div class="small muted">日志、健康检查、简报新鲜度</div></div>
  <div class="card" v-click><div class="accent small font-bold">关键取舍</div><div class="small muted">AI 只读建议，交易和定价是写死的代码</div></div>
</div>

</div>

<!--
【35 秒】架构就四层：前端、FastAPI 接口、写死的交易内核、数据库。AI 是旁路，只读建议，不掺和交易。部署是 Render 四件套。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.3 算法与 AI</div>

# 价格说得清，AI 挂了也能用

<div class="body">

<div class="grid2">
  <div class="card" v-click>
    <div class="accent small font-bold">定价模型：每条涨跌都能拆成一句话</div>
    <div class="formula mt-3">P′ = max(1.0, P × (1 + 0.15 · S))</div>
    <div class="small font-bold muted mt-2">S = clamp(z / 3.0, −1, 1)　｜　单次变动 |Δ| ≤ 20%</div>
    <ul class="clean mt-2">
      <li>用 z-score 标准化，避免强队恒涨</li>
      <li>0.15 权重 + 地板价 + ±20% 熔断</li>
      <li>每条价格都带 reason，现场能拆</li>
    </ul>
  </div>
  <div class="flex flex-col gap-3">
    <div class="card" v-click>
      <div class="accent small font-bold">AI 智能体：只给建议，永不改余额</div>
      <div class="flex gap-1 flex-wrap mt-2">
        <span class="pill">感知行情</span><span class="pill">分析师</span><span class="pill">风控</span><span class="pill">交易员</span><span class="pill">人点采纳</span><span class="pill">审计</span>
      </div>
      <div class="small muted mt-2">DeepSeek API，20 秒超时；没 Key、超时、坏 JSON 都走规则兜底，接口照样 200。</div>
      <div class="small mt-2">固定 6 个字段；L4 评测 <b>16/16、P95 3.39s</b>。</div>
    </div>
    <div class="dark-band small" v-click>
      <b>为什么不让模型定价？</b><br>
      规则稳定、零成本；模型挂了自动回落，交易照常。
    </div>
  </div>
</div>

</div>

<!--
【40 秒】定价用 z-score 加线性映射，一次最多涨跌 20%，每条价格都带原因，现场能拆。AI 这边是分析师、风控、交易员，人在环、留审计；DeepSeek 挂了就走规则兜底。我们不给模型定价权。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.4 数据库设计</div>

# 9 张表：交易有记录，AI 有审计

<div class="body">

<div v-click>

| 分组 | 表 | 关键的不可变 / 一致性设计 |
| --- | --- | --- |
| 账号 | users / auth_tokens | 余额与初始本金；令牌 30 天、可撤销 |
| 市场 | players / price_history | 价格历史只追加；每条 reason 必填 |
| 交易 | positions / trades | 流水只追加、带 balance_after；持仓唯一(user, player) |
| 智能体 | agent_traces / decision_logs / price_narratives | 每次调用/采纳/归因都留审计，只读业务 |

</div>

<div class="grid2">
  <div v-click>

```mermaid {scale: 0.46}
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
    <div class="card" v-click><div class="accent small font-bold">交易一致性</div><div class="small muted">余额、持仓、流水一起写；14 条交易测试。</div></div>
    <div class="card" v-click><div class="accent small font-bold">为什么不用缓存/队列？</div><div class="small muted">这门课的量级不用缓存，先保证数据对得上。</div></div>
  </div>
</div>

</div>

<!--
【25 秒】数据库 9 张表，分账号、市场、交易、智能体。两个关键：流水只追加、记余额；余额、持仓、流水一个事务写完。AI 的调用、采纳、归因都落审计表，业务表只读。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.5.5 接口设计</div>

# 23 个接口，格式统一

<div class="body">

<div v-click>

| 分组 | 接口示例 | 契约要点 |
| --- | --- | --- |
| 行情 | GET /api/players · /api/players/\{id\} · /api/players/\{id\}/prices | 列表 / 详情 / 价格历史（按 ts 升序） |
| 交易 | GET /api/account · /api/account/history · POST /api/trades/buy \| sell | 余额/资产曲线；买卖返回余额与流水 |
| 身份 | POST /api/auth/register \| login \| logout · GET /api/auth/me | PBKDF2 + 不透明令牌；30 天有效 |
| AI | GET /api/analysis/\{id\} · /api/agent/decision \| brief \| panel \| tools | 6 字段契约；只读；失败 200 + rule_fallback |
| 运维 | GET /api/health · /api/debug/db · /api/logs | 健康检查 / 只读自检 / 运行日志 |

</div>

<div class="grid2">
  <div class="dark-band small" v-click><b>在线文档：</b>https://playerstock-backend-mdlk.onrender.com/api/docs<br>FastAPI 自动生成 OpenAPI / Swagger，可直接试调。</div>
  <div class="card" v-click><div class="small muted">GET 失败重试一次，POST 不重试；敏感字段不返回。</div></div>
</div>

</div>

<!--
【20 秒】接口 23 个，分行情、交易、身份、AI、运维。FastAPI 自带 Swagger，老师现场可以打开 /api/docs 试。GET 可以重试，POST 不重试，避免重复下单。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.6 软件质量</div>

# 质量：每次提交都跑测试

<div class="body">

<div class="grid4">
  <div class="card" v-click><div class="metric">335</div><div class="small font-bold">后端测试</div><div class="small muted">pytest，live 默认不跑</div></div>
  <div class="card" v-click><div class="metric">182</div><div class="small font-bold">前端测试</div><div class="small muted">Vitest / 22 个文件</div></div>
  <div class="card" v-click><div class="metric">98%</div><div class="small font-bold">核心覆盖率</div><div class="small muted">app + core_engine</div></div>
  <div class="card" v-click><div class="metric">4</div><div class="small font-bold">CI 门禁 job</div><div class="small muted">卫生、后端、前端、交付物</div></div>
</div>

<div class="grid2">
  <div class="card" v-click><div class="accent small font-bold">质量控制与保证方法</div>
    <ul class="clean">
      <li>日志：/api/logs 记请求和错误</li>
      <li>异常：统一错误码，前端能提示</li>
      <li>契约：Pydantic 校验入参出参</li>
      <li>并发：事务 + 条件更新，有测试</li>
      <li>降级：LLM、网络、冷启动都有兜底</li>
    </ul>
  </div>
  <div class="card" v-click><div class="accent small font-bold">质量工具</div>
    <table>
      <tbody>
      <tr><td>ruff</td><td>规范 + 圈复杂度，CI 同版本</td></tr>
      <tr><td>oxlint / eslint</td><td>前端规范，冲突标记也有守卫</td></tr>
      <tr><td>vue-tsc</td><td>类型检查进 build</td></tr>
      <tr><td>Vitest / pytest</td><td>单元/集成/评测/并发</td></tr>
      <tr><td>GitHub Actions</td><td>4 个 job 全绿才部署</td></tr>
      </tbody>
    </table>
  </div>
</div>

</div>

<!--
【30 秒】质量拿数字说话：后端 335 条、前端 182 条，核心覆盖率 98%；CI 4 个 job 全绿才部署。除了测试，还有日志、统一错误码、契约校验和降级。
-->

---
layout: default
---

<div class="kicker">03 产品实现 · 3.7 代码统计</div>

# 3 万多行代码，重点在结构

<div class="body">

<div v-click>

| 语言 | 文件数 | 行数 |
| --- | --- | --- |
| Python | 109 | 16,391 |
| Vue | 20 | 8,835 |
| TypeScript | 47 | 6,350 |
| CSS | 3 | 782 |
| HTML | 3 | 1,083 |
| Markdown（文档） | 71 | 12,452 |

</div>

<div class="grid2">
  <div class="card" v-click><div class="accent small font-bold">模块数</div><div class="small muted">前端 8 视图 / 9 组件；后端 11 路由 / 9 AI 模块。</div></div>
  <div class="dark-band small" v-click><b>AI 与团队编写的比例</b><br>没做逐行归因，不编百分比。AI 帮忙写测试和文档；核心逻辑人工写、互相审。</div>
</div>

<div class="sage small font-bold" v-click>可执行代码合计约 33,000 行；文档约 12,000 行（65 份 md）。</div>

</div>

<!--
【15 秒】代码大概 3.3 万行，文档 1.2 万行。前端 8 个视图 9 个组件，后端 11 个路由 9 个 AI 模块。AI 帮忙写测试和文档，核心逻辑人工写、互相审。
-->

---
layout: default
---

<div class="kicker">验收 · 测试与容量</div>

# 三类证据：用户测试、AI 评测、压测

<div class="body">

<div class="grid2">
  <div class="card" v-click><div class="metric">33 项</div><div class="small font-bold">用户测试表</div><div class="sage small font-bold">32 通过 / 1 部分通过</div><div class="small muted">对话、状态、错误、边界都测了</div></div>
  <div class="card" v-click><div class="metric">16/16</div><div class="small font-bold">AI 契约评测</div><div class="sage small font-bold">source=llm 100% · P95 3.39s</div><div class="small muted">6 个字段都全，合规也过</div></div>
  <div class="card" v-click><div class="metric">11/11</div><div class="small font-bold">红队用例</div><div class="sage small font-bold">提示注入 / 越权 / 伪造来源</div><div class="small muted">全部守住，有审计日志</div></div>
  <div class="card" v-click><div class="metric">38 req/s</div><div class="small font-bold">只读压测</div><div class="sage small font-bold">≈190 人同时在线 · 0 错误</div><div class="small muted">瓶颈是免费档，不是代码</div></div>
</div>

<div class="small muted" v-click>边界：交叉测试双向各 33 题，样本还小；没有真实赛事数据，不吹准确率。</div>

<div class="card" v-click><div class="small">证据索引：docs/acceptance/evidence（147 张截图）· test_report.md · agent_eval_report.md · load_test_report.md</div></div>

</div>

<!--
【20 秒】三类证据：33 项用户测试（32 过、1 部分过）、AI 契约 16/16、红队 11/11；压测 38 req/s、190 并发、0 错误。也说清楚：交叉测试样本还小，没有真实赛事数据，不吹准确率。
-->

---
layout: default
---

<div class="kicker">演示</div>

# 现场演示：从判断到下单，2 分钟

<div class="body">

<div class="grid3">
  <div class="card" v-click><div class="accent font-bold">01 市场</div><div class="small muted mt-1">简报给结论，3 列卡看涨跌和停牌</div></div>
  <div class="card" v-click><div class="accent font-bold">02 详情</div><div class="small muted mt-1">价格曲线 + AI 建议 + 停牌提示</div></div>
  <div class="card" v-click><div class="accent font-bold">03 下单</div><div class="small muted mt-1">买 2 股：余额、持仓、流水同时变</div></div>
  <div class="card" v-click><div class="accent font-bold">04 复盘</div><div class="small muted mt-1">个人页看资产曲线和交易统计</div></div>
  <div class="card" v-click><div class="accent font-bold">05 兜底</div><div class="small muted mt-1">断网/无 Key 也能交易</div></div>
  <div class="card" v-click><div class="accent font-bold">06 结束</div><div class="small muted mt-1">回到市场，数据干净可重复</div></div>
</div>

<div class="small muted" v-click>演示时不切窗口；卡了就刷新只读页或放录屏。</div>

</div>

<!--
【5 秒】下面用两分钟走一遍：市场、详情、买入、复盘，再补一个停牌拦截和 AI 降级。演示时不切窗口。
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
【结束】最后一页不列问题：这是给老师做结课审查的材料。谢谢老师，页面上留了在线演示、仓库和完整材料三个入口，随时能点开看。
-->
