---
theme: default
colorSchema: light
title: PlayerStock 结课审查
info: |
  软件新技术创新实践课程 · 结课项目审查
  产品设计、产品实现、验收与演示
class: text-left
highlighter: shiki
lineNumbers: false
drawings: false
transition: fade
mdc: true
fonts:
  sans: Noto Sans SC
  serif: Noto Serif SC
  mono: JetBrains Mono
  weights: '400,500,600,700'
  provider: google
---

<div class="cover">

<div class="kicker">软件新技术创新实践课程 · 结课项目审查 · 2026 年 11 月</div>

<div>
  <div class="cover-title">PlayerStock</div>
  <div class="cover-sub">以 CS2 职业选手为标的的虚拟交易系统，<br>价格随比赛表现变化。</div>
</div>

<dl class="dl rule-top" style="max-width:44rem">
  <dt>小组</dt><dd>有请下一组</dd>
  <dt>成员</dt><dd>王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）</dd>
  <dt>说明</dt><dd>只用信用点，不能充值、提现或兑换；智能体只给建议，下单由用户确认。<a href="./playerstock_defense.pdf">PDF 版</a></dd>
</dl>

</div>

<!--
【10 秒】老师们好，我们是「有请下一组」。我们做的叫 PlayerStock：用信用点买卖 CS2 职业选手，选手比赛打得好，价格就涨。

**【可能被问】**

**问**：信用点能换钱吗？这算不算赌博？

答：不能。信用点不能充值、提现或兑换，没有任何资金通道，也不给赔率，所以不是博彩。首页和每条 AI 建议都写了「不构成投资建议」。

**问**：用真实选手的名字合规吗？

答：只用了公开可查的姓名、战队和位置；价格和评分都是模拟值，页面上写明了与 Valve、HLTV 和俱乐部无关。
-->

---

<div class="kicker"><b>01</b> 产品设计 · 1.1 使命、口号和目标用户</div>

# 使命：用价格验证对选手表现的判断

<div class="body">

<div class="g g-7-5">
  <div v-click>
    <div class="label">使命</div>
    <div class="quote">观众用信用点买入看好的选手，再通过后续几轮的价格变化，检验自己的判断。</div>
    <div class="label" style="margin-top:1.6rem">口号</div>
    <div class="statement" style="font-size:1.7rem">看懂比赛，从持有起。</div>
    <div class="note">口号不使用赚钱、输赢、翻倍等表述。</div>
  </div>
  <div v-click>
    <div class="label">目标用户</div>
    <dl class="dl" style="grid-template-columns:6.4rem 1fr">
      <dt>CS2 观众</dt><dd>对选手有判断，缺少验证途径</dd>
      <dt>交易体验者</dt><dd>体验买卖，不承担资金风险</dd>
      <dt>编程学习者</dt><dd>参考一个完整的工程项目</dd>
    </dl>
    <div class="note rule-top" style="margin-top:1.2rem">不面向：以盈利为目的的用户、未成年人、真钱竞猜用户。</div>
  </div>
</div>

</div>

<!--
【30 秒】看比赛的时候，我们常会觉得「这个选手今天状态真好」，但这种判断没处验证。在我们的网站上，你可以用信用点买一点这个选手，过几轮再看价格，就知道自己看得准不准。口号是「看懂比赛，从持有起」，里面特意没用赚钱、翻倍这种词。用户主要是三类：CS2 观众、想练交易又不想花真钱的人，还有学编程的同学。

**【可能被问】**

**问**：为什么不面向未成年人？

答：涉及「买卖」的玩法容易被误解成投资或竞猜，我们主动把未成年人和想赚钱的人排除在外，口号里也不出现赚钱、输赢。

**问**：三类用户里最核心的是谁？

答：CS2 观众。产品的每个功能都围绕「验证自己对选手的判断」，另外两类是顺带覆盖的。
-->

---

<div class="kicker"><b>01</b> 产品设计 · 1.1 差异化、获客与团队</div>

# 与同类产品的区别：交易对象是选手身价

<div class="body">

<div v-click>

| | 赛事竞猜 | 模拟炒股 | <span class="hl">PlayerStock</span> |
| --- | --- | --- | --- |
| 买的是什么 | 一场比赛的输赢 | 公司股票 | <span class="hl">一位选手的身价</span> |
| 价格从哪来 | 盘口赔率 | 真实行情 | <span class="hl">按每轮比赛表现计算，可以回测</span> |
| 涨跌有没有原因 | 没有 | 部分有 | <span class="hl">每次变价都写明原因</span> |
| 用不用真钱 | 用 | 不用 | <span class="hl">不用，信用点不可兑换</span> |

</div>

<div class="g g-1-1 rule-top" v-click>
  <div class="text"><span class="label">获客　</span>每轮比赛前后发布涨跌复盘，先在校园电竞社群和 B 站试用推广。</div>
  <div class="text"><span class="label">分工　</span>A 前端 · B 交易与部署 · C 定价与回测 · D 智能体与测试</div>
</div>

</div>

<!--
【30 秒】和赛事竞猜比，我们买的不是一场比赛的输赢，而是一位选手的身价。和模拟炒股比，我们的价格来自比赛表现，而且每次涨跌都写了原因。全程只用信用点，没有任何兑换出口。推广方面，打算每轮比赛前后发涨跌复盘，先在校园电竞社群试用。分工是 A 做前端，B 做交易和部署，C 做定价，我做智能体和测试。

**【可能被问】**

**问**：怎么盈利？

答：这是课程作品，不盈利，也不打算接入任何付费或充值。如果继续做，只会考虑和赛事内容结合做观赛互动，不碰真钱。

**问**：已经有用户了吗？

答：还没有真实用户。我们和外组做了双向互测，各 33 题，这是目前的外部验证；获客方案还只是计划。

**问**：「可以回测」是什么意思？

答：价格是按公式算出来的，给定同样的比赛数据和随机种子，结果完全一样，所以可以重复跑、对比不同参数的效果。
-->

---

<div class="kicker"><b>01</b> 产品设计 · 1.2 产品定义</div>

# 产品定义：面向关注 CS2 选手的观众

<div class="body">

<div class="g g-7-5">
  <dl class="dl" v-click style="grid-template-columns:5.2rem 1fr">
    <dt>目标用户</dt><dd>关注 CS2 选手、又想体验虚拟交易的观众，想亲手验证自己的判断。</dd>
    <dt>产品形态</dt><dd>以 CS2 职业选手为标的的虚拟股网站，提供行情、买卖、持仓、走势和智能体建议。</dd>
    <dt>差异</dt><dd>资讯站提供比分，模拟盘交易公司股票；本产品的每次价格变化都对应选手某一轮的表现。</dd>
  </dl>
  <div v-click>
    <div class="label">一条用户故事</div>
    <div class="quote">看完比赛，我想马上买入我觉得被低估的选手，验证自己是不是比解说更早看出来。</div>
    <div class="note" style="margin-top:.7rem">共 7 条用户故事，每条写了验收条件（user_stories.md）</div>
  </div>
</div>

<div class="text rule-top" v-click><span class="label">边界　</span>网页应用，支持桌面和手机；初始 5000 信用点，每位选手最多持有 50 股；未登录时使用公共演示账户，也可注册私人账号。不提供充值、提现、赔率和自动交易。</div>

</div>

<!--
【35 秒】产品定义按课程模板写了三句：给谁用、它是什么、和别的产品有什么不同。最关键的是第三句：每一次价格变化，都能对应到选手某一轮的表现。右边是一条用户故事：看完比赛，我想马上买入我觉得被低估的选手，看看自己是不是比解说更早看出来。下面是边界：初始五千信用点，每位选手最多五十股；不充值、不提现、不给赔率，智能体也不会自动下单。

**【可能被问】**

**问**：为什么单个选手最多 50 股？

答：防止把钱全压在一个人身上，也让持仓分散、演示更有看点。这条规则写在数据库的条件更新里，并发下单也不会超过。

**问**：用户故事有验收条件吗？

答：有，7 条用户故事都写了验收条件，在 docs/requirements/user_stories.md，答辩前逐条核对过。

**问**：不登录也能买卖？

答：能。不登录用的是公共演示账户，大家共用；想保留自己的记录可以注册私人账号。
-->

---

<div class="kicker"><b>02</b> 产品设计应用的原则</div>

# 五条设计原则及对应做法

<div class="body">

<div class="numbered" v-click style="row-gap:.55rem">
  <div><span class="n">01</span><div><div class="t">先解决主要问题</div><div class="d">聚焦行情查看与判断验证，不做充值、撮合盘口和第三方登录。<span class="mono">problem_definition.md</span></div></div></div>
  <div><span class="n">02</span><div><div class="t">让选择收敛</div><div class="d">定价只有一条公式；智能体只输出 6 个固定字段。<span class="mono">pricing_model.md · api_contract.md</span></div></div></div>
  <div><span class="n">03</span><div><div class="t">优先复用成熟方案</div><div class="d">后端采用 FastAPI 和 SQLAlchemy；图表需求简单，使用 SVG 绘制。<span class="mono">architecture.md</span></div></div></div>
  <div><span class="n">04</span><div><div class="t">用数字验收</div><div class="d">测试条数、覆盖率、单次涨跌上限、接口耗时均有具体数值。<span class="mono">test_report.md</span></div></div></div>
  <div><span class="n">05</span><div><div class="t">自动检查优先</div><div class="d">每次提交先通过 CI 的 4 项检查，人工评审侧重设计。<span class="mono">ci.yml · CodeReview.md</span></div></div></div>
</div>

</div>

<!--
【30 秒】我们定了五条设计原则，每条后面的小字是对应的文档。举两个例子：第二条「让选择收敛」，定价只用一条公式，智能体只输出六个固定字段，便于测试和检查；第五条「自动检查优先」，格式、类型和测试交给 CI，组员评审时主要讨论设计。

**【可能被问】**

**问**：「先解决主要问题」具体砍掉了什么？

答：充值、撮合盘口、第三方登录、排行榜都没做。我们先保证「看行情、看原因、买卖」这条主线跑通。

**问**：智能体为什么只输出 6 个字段？

答：字段固定，就能逐个检查：动作只能是买、卖、不动，风险只能是低、中、高。模型乱写任何一项，就自动换成规则版。

**问**：为什么不用图表库？

答：图只有价格曲线和资产曲线两种，自己画 SVG 一百多行就够了，少一个依赖，深浅主题也好控制。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.1 用户体验设计</div>

# 界面：行情集中展示，三步完成下单

<div class="body">

<div class="g g-1-1" style="column-gap:2rem">
  <div v-click>
    <img class="shot" src="./assets/market-light.png" alt="市场页截图" />
    <div class="figcap"><b>图 1</b>市场页：顶部一行简报，下面 3 列选手卡，桌面一屏 6 张</div>
  </div>
  <div v-click>
    <img class="shot" src="./assets/detail-light.png" alt="详情页截图" />
    <div class="figcap"><b>图 2</b>详情页：走势、智能体建议和下单面板在同一页</div>
  </div>
</div>

<div class="note" v-click>选手卡 → 详情页 → 下单面板，三步完成买入。手机端通过底部 4 个标签切换；浅色、深色主题均检查过文字对比度；从详情页返回后，筛选和排序保持不变。</div>

</div>

<!--
【30 秒】左边是市场页：最上面一行简报告诉你今天谁涨得最多、谁停牌，下面是选手卡，桌面一屏能看到六张。右边是详情页：走势、智能体建议和下单面板放在同一页，不用来回跳。从选手卡点进去，在下单面板点一下，三步就买好了。手机上用底部四个标签切换，深浅两套主题都查过对比度。

**【可能被问】**

**问**：「检查过对比度」怎么检查的？

答：用脚本把每个页面在深色、浅色、桌面、手机下都打开，逐个算文字和背景的对比度，按 WCAG 标准，最后违规数是 0。

**问**：界面改过几版？

答：改过好几轮，最后定成现在这种低密度的「纸感」风格：去掉玻璃效果和多余说明，让一屏只放最重要的信息。截图证据在 docs/acceptance/evidence。

**问**：为什么详情页要把建议和下单放一起？

答：用户看完建议马上就要决定买不买，放一页能少一次跳转；但下单仍必须本人点，建议不会替你操作。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.2 技术选型</div>

# 技术选型：优先采用组员熟悉的技术

<div class="body">

<div v-click>

| 层 | 选型 | 原因 |
| --- | --- | --- |
| 前端 | Vue 3 · Vite · TypeScript · Vitest | 组员熟悉，构建快，有类型检查 |
| 后端 | Python · FastAPI · SQLAlchemy · Pydantic | 开发效率高，自动生成接口文档 |
| 数据 | 本地 SQLite，线上 Postgres | 本地无需安装数据库；线上需要持久保存 |
| 智能体 | DeepSeek 接口 + 规则版备用 | 成本低；模型不可用时切换规则版 |
| 部署 | Render：静态站 + 后端 + 定时任务 + 数据库 | 有免费额度，自带 HTTPS |
| 检查 | GitHub Actions · ruff · oxlint · eslint · pytest | 每次提交自动执行 |

</div>

<div class="note" v-click>具体版本号见仓库 README。线上使用 Postgres，因为免费服务器的磁盘在重新部署时会清空。</div>

</div>

<!--
【20 秒】只有六个开发日，所以我们只选组员用过的东西：前端 Vue 和 TypeScript，后端 FastAPI。本地用 SQLite，不用装数据库；线上必须用 Postgres，因为免费服务器每次重新部署硬盘都会清空。智能体接的是 DeepSeek，出问题就换规则版。全部部署在 Render 上。

**【可能被问】**

**问**：为什么选 DeepSeek，不用别的模型？

答：一开始试过免费的模型网关，被拦截、额度也不够；换成 DeepSeek 官方接口后稳定，价格低，线上中位响应两秒多。换别的模型只需改三个环境变量，代码不动。

**问**：本地 SQLite、线上 Postgres，会不会两边行为不一样？

答：会有坑，比如 SQLite 不支持 SELECT FOR UPDATE。所以我们用两边都支持的「条件更新」防并发，金额全程用 Decimal 算，CI 和本地都跑同一套测试。

**问**：为什么不自己买服务器？

答：Render 免费、自带 HTTPS、从 GitHub 自动部署，对课程项目够用；代价是 15 分钟没人访问会休眠，我们用定时任务保活。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.3 代码仓库与协作</div>

# 代码仓库与协作：540 次提交

<div class="body">

<div class="g g-1-1">
  <div v-click>
    <div class="label">每人提交次数（git shortlog，含合并提交）</div>
    <div class="bars" style="margin-top:.6rem">
      <div><span class="who">D 王泽棠</span><span class="bar accent" style="width:100%"></span><span class="v">247</span></div>
      <div><span class="who">B 胡德昊</span><span class="bar" style="width:47%"></span><span class="v">116</span></div>
      <div><span class="who">C 刘宏</span><span class="bar" style="width:41.7%"></span><span class="v">103</span></div>
      <div><span class="who">A 倪颢容</span><span class="bar" style="width:30%"></span><span class="v">74</span></div>
    </div>
    <div class="note" style="margin-top:.9rem">B 有两个提交身份（July75-bit 60 + Hu De Hao 56），合并计算。<br>统计至 2026-11-28：共 540 次提交，其中非合并提交 397 次。</div>
  </div>
  <dl class="dl" v-click style="grid-template-columns:4.5rem 1fr">
    <dt>仓库</dt><dd><span class="mono">github.com/July75-bit/Innovation</span><br>日常提交合入 develop 分支</dd>
    <dt>任务</dt><dd>Issues 和看板管理，15 条缺陷均已关闭</dd>
    <dt>检查</dt><dd>每次 push 执行 4 项：冲突标记、后端、前端、交付物</dd>
  </dl>
</div>

</div>

<!--
【20 秒】代码在 GitHub 上，日常提交进 develop 分支，到现在一共五百四十次提交。左边是每个人的次数，B 有两个提交账号，这里合在一起算。任务和缺陷用 Issues 和看板管，十五条缺陷都已经关了。每次推送会自动跑四项检查。

**【可能被问】**

**问**：D 的提交比别人多很多，是不是一个人在干？

答：提交次数和工作量不完全对等：D 负责智能体、测试和文档，改动零碎、提交就多；C 的定价引擎和 B 的交易事务提交次数少，但都是核心代码。分工在第 3 页。

**问**：为什么只有 develop 分支，main 落后很多？

答：为了 6 天里少折腾，大家都在 develop 上小步提交，线上也从 develop 部署；main 只合过早期的一次。这是我们流程上的一个不足。

**问**：数字怎么来的？

答：用 git shortlog 按提交人统计，包含合并提交，统计到 11 月 28 日。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.4 生命周期中遇到的问题</div>

# 开发与上线中的六个问题及处理

<div class="body">

<div v-click>

| 问题 | 原因 | 怎么解决 |
| --- | --- | --- |
| 重新部署后数据丢失 | 免费服务器使用临时磁盘，SQLite 文件随之清空 | 线上改用 Postgres，启动时检查并告警 |
| 线上启动报找不到 psycopg | SQLAlchemy 2.1 更换了默认数据库驱动 | 连接串统一改为 psycopg2，并补充测试 |
| 前端请求被跨域策略拦截 | 后端未配置前端地址，或地址带尾斜杠 | 自动去除尾斜杠，漏配时告警 |
| 首页简报显示原始 JSON | 模型输出未经清洗直接展示 | 后端清洗输出，前端二次校验，补充回归测试 |
| 首次访问等待 33.6 秒 | 免费服务器闲置 15 分钟后休眠 | 定时任务保活，增加骨架屏和自动重试 |
| 赛后结算接口缺少口令校验 | 最初按内部接口设计 | 改为必须携带运维口令，补充 4 条测试 |

</div>

</div>

<!--
【30 秒】这是开发和上线中遇到的六个问题。第一个是数据丢失：Render 免费服务器使用临时磁盘，重新部署后 SQLite 文件会被清空，所以线上改用 Postgres。第五个是首次访问要等三十多秒，原因是服务器闲置十五分钟会休眠，我们用定时任务保活。最后一个是结课前自查发现的赛后结算接口缺少口令校验，已改为必须携带口令。每个问题修复后都补充了测试。

**【可能被问】**

**问**：哪个坑最严重？

答：并发卖出，两笔同时到会重复入账，余额从 5000 变成 5504。它记在缺陷清单 BUG-01，没列在这页；修好后加了并发测试。

**问**：保活会不会把免费额度用完？

答：定时任务只在北京时间早 8 点到午夜之间每 10 分钟打一次，算下来每月约 496 小时，在免费额度内。

**问**：还有别的自查发现吗？

答：有。最近复查还修了几处：AI 看到的持仓没按用户区分、换账号后页面缓存没清、登录不限次数。都已修好并补了测试。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.1 系统架构与基础设施</div>

# 系统架构：价格由程序计算，智能体只读

<div class="body center">

<div v-click>

```mermaid {scale: 0.78}
flowchart LR
  B["浏览器 · Vue 3"] --> S["Render 静态站"]
  S --> A["FastAPI · 30 个接口"]
  A --> R["交易规则"]
  A --> C["定价引擎"]
  A --> I["智能体（只读）"]
  R --> D[("Postgres · 9 张表")]
  C --> D
  I -.只写审计记录.-> D
  H["定时任务 · 保活"] --> A
```

</div>

<div class="note" v-click>三个服务部署在 Render 新加坡区：静态站、后端服务、定时任务。智能体与数据库之间为虚线：只读取业务数据，仅写入自身的审计记录。</div>

</div>

<!--
【30 秒】浏览器打开 Vue 页面，请求发到 FastAPI 后端。后端分三块：交易规则、定价引擎和智能体，数据都存在 Postgres 的九张表里。请注意智能体到数据库那条线是虚线：价格和交易都由程序按规则算，智能体只能读数据、给建议，唯一会写的是它自己的调用记录。

**【可能被问】**

**问**：定时任务做什么？

答：两件事：每 10 分钟访问一次，防止服务器休眠；顺便刷新首页的今日简报。它只调只读接口。

**问**：价格是谁触发更新的？

答：模拟比赛结算后，由带运维口令的结算接口触发定价引擎，按公式更新价格并写一条原因。普通用户和智能体都改不了价格。

**问**：前后端怎么通信，有没有跨域问题？

答：前端和后端是两个域名，后端只放行前端的地址；上线时踩过跨域被拦的坑，第 9 页第三行。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.3 算法</div>

# 定价算法：按选手相对自身近期水平的表现调价

<div class="body">

<div v-click>
  <div class="formula">P′ = max(P<sub>floor</sub>, P × (1 + α<span class="s">S</span> + β<span class="s">D</span>))</div>
  <div class="note" style="margin-top:.4rem">新价格 = max（价格下限，原价格 ×（1 + 表现权重 × 表现信号 + 需求权重 × 需求信号））<span class="mono" style="margin-left:.6rem">core_engine/pricing.py · update_price()</span></div>
</div>

<div class="g g-7-5 rule-top" style="margin-top:.2rem">
  <dl class="dl pricing-dl" v-click>
    <dt><span class="accent">S</span> 表现信号</dt><dd>（本轮得分 − 近 5 场均值）÷ 标准差 ÷ 3，截断到 ±1</dd>
    <dt><span class="accent">D</span> 需求信号</dt><dd>净买入量 ÷ 总成交量，范围 −1～1</dd>
    <dt>α 表现权重</dt><dd>默认 0.15：S 满格时单次涨跌 15%</dd>
    <dt>β 需求权重</dt><dd>默认 0：本期不启用需求信号，D 不影响价格</dd>
    <dt>P<sub>floor</sub> 下限</dt><dd>默认 1.0 信用点</dd>
    <dt>单次上限</dt><dd>αS + βD 截断到 ±20% 后再计算新价格</dd>
  </dl>
  <div v-click class="pricing-side">
    <div class="label">与自身比较的原因</div>
    <div class="text">与全体选手比较，高水平选手会持续上涨；与自身近期比较，只有表现高于平时才上涨。</div>
    <div class="label" style="margin-top:.9rem">β 设为 0 的原因</div>
    <div class="text">没有真实成交数据，用户买卖产生的需求信号容易被刷高，因此先关闭，公式和接口保留。</div>
    <div class="note" style="margin-top:.6rem">每个价格点记录原因；已用 100 个随机种子回测。</div>
  </div>
</div>

</div>

<!--
【30 秒】定价公式写在 core_engine/pricing.py 的 update_price 里：新价格等于原价格乘以一加 α 乘表现信号 S、再加 β 乘需求信号 D，最低不低于价格下限。S 是选手本轮得分和他自己近五场相比的标准分，除以三后截断到正负一；D 是净买入量占总成交量的比例。参数默认 α 为 0.15、β 为 0，也就是本期只用表现信号，需求信号保留但不生效。α 乘 S 加 β 乘 D 还会先截断到正负百分之二十，单次涨跌不会超过这个范围。

**【可能被问】**

**问**：β 为什么是 0？需求信号 D 有什么用？

答：D 是净买入量除以总成交量，反映大家在买还是在卖。本项目没有真实成交和盘口，用户自己买卖就能把需求信号刷高，所以本期把 β 设为 0，D 不影响价格。公式里的 β·D 和计算 D 的函数 to_demand_signal 都已保留并有测试，接入真实成交数据后再设置 β，同时要加流动性限制。

**问**：参数在哪里改？

答：α、β 和价格下限可以通过环境变量 PRICING_ALPHA、PRICING_BETA、PRICING_FLOOR 设置，优先级是显式传参、后端配置、环境变量、代码默认值；单次 ±20% 上限写死在代码里，不对外开放。

**问**：表现分具体怎么算？

答：先算本轮得分比近 5 场平均高出几个标准差，再除以 3、压到 −1 到 1 之间。也就是高出 3 个标准差才算「满格」，避免价格稍有波动就大涨大跌。

**问**：0.15 这个系数怎么定的？

答：满格时单次涨跌 15%，看着有起伏又不至于乱跳。我们用 100 个随机种子各跑 28 轮比过：调到 0.08，单次平均幅度从 5.75% 降到 3.07%。

**问**：长期看价格是不是一直跌？

答：有轻微下行，我们在报告里如实写了：100 个种子下，单人区间收益中位数约 −5.7%。原因是高分被截断在 100、加上乘法更新的波动拖累；把系数调小会明显收敛。

**问**：价格变化能追溯吗？

答：能。每个价格点都记一句原因，写明本轮得分和表现分，在详情页能逐条看。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.3 智能体</div>

# 智能体流程：只提供建议，不执行交易

<div class="body">

<div class="flow" v-click>
  <div><div class="n">01</div><div class="t">准备资料</div><div class="d">读取行情、最近价格和当前用户的持仓</div></div>
  <div><div class="n">02</div><div class="t">分析</div><div class="d">三个角色依次分析，或由模型调用 3 个只读工具</div></div>
  <div><div class="n">03</div><div class="t">检查</div><div class="d">只接受 6 个固定字段和规定取值</div></div>
  <div><div class="n">04</div><div class="t">算股数</div><div class="d">按余额和风险等级计算建议股数与止损线</div></div>
  <div class="hl"><div class="n">05</div><div class="t">记录</div><div class="d">调用写入审计并串成哈希链，采纳也记录</div></div>
</div>

<div class="g g-7-5 rule-top" v-click>
  <dl class="dl" style="grid-template-columns:6rem 1fr">
    <dt>不执行交易</dt><dd>工具均为只读，买卖须由用户确认</dd>
    <dt>故障回退</dt><dd>无密钥、超时、格式错误或超出额度时改用规则版</dd>
  </dl>
  <div class="note">说明：三个角色由同一个模型担任，每次使用不同的角色提示；后一位可读取前面的发言，结论取自交易员。</div>
</div>

</div>

<!--
【30 秒】智能体的处理分五步：从数据库准备资料；由分析师、风控、交易员依次分析，或由模型调用三个只读工具；检查回答是否符合六个固定字段；按余额和风险计算建议股数和止损线；最后写入记录。三个角色由同一个模型担任，每次使用不同的角色提示。任何一步出错都会改用规则版。智能体只提供建议，买卖须由用户确认。

**【可能被问】**

**问**：同一个模型换三个身份，算多智能体吗？

答：我们如实说：是同一个模型扮演三个角色，不是三个独立程序。价值在于分工后能看到分歧，比如风控不同意多买，比直接给一句「买」更可信。

**问**：规则版是什么规则？

答：看近 5 个价格点的涨跌和表现分：涨超 5% 但表现分低于 60 建议卖，跌超 5% 但表现分 75 以上建议买，其余不动；没持仓时不会建议卖。

**问**：建议买几股怎么算的？

答：纯算术：目标持仓 =（余额 + 已持仓市值）× 风险比例（低 10%、中 6%、高 3%），建议买入 = 目标 − 已持股数，再受余额和 50 股上限约束；止损线分别比现价低 12%、9%、6%。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.3 智能体的五个组成</div>

# 智能体的五个组成

<div class="body">

<div v-click>

<table class="tight agent5">
<thead><tr><th>组成</th><th>位置</th><th>实现</th></tr></thead>
<tbody>
<tr><td>任务拆解</td><td class="mono">app/api/agent.py<br>ai/panel.py</td><td>固定五步：准备资料 → 分析 → 检查 → 算股数 → 记录；分析按分析师、风控、交易员顺序进行</td></tr>
<tr><td>工具调用</td><td class="mono">ai/tools.py</td><td>3 个只读工具：查价格历史、查当前用户账户、计算建议股数；由模型决定调用哪个，最多 3 轮，每次调用的参数和结果写入审计</td></tr>
<tr><td>记忆</td><td class="mono">ai/context.py<br>app/core/trace_hash.py</td><td>每次请求从数据库读取最新行情和当前用户持仓；调用记录和采纳记录存表，调用记录用 SHA-256 哈希链防篡改；不做跨会话的对话记忆</td></tr>
<tr><td>护栏</td><td class="mono">ai/llm_agent.py<br>app/core/rate_limit.py</td><td>输入：只接收选手编号，提示词按白名单取 12 个字段；输出：6 个字段与取值校验、理由截断到 200 字、清洗 JSON；运行：20 秒超时、每分钟 60 次额度、失败改用规则版</td></tr>
<tr><td>专业知识</td><td class="mono">ai/prompts.py<br>ai/fallback.py</td><td>提示词要求只依据给定数据作答并引用具体数值；规则版的涨跌与表现分阈值；数据库中带原因的价格历史</td></tr>
</tbody>
</table>

</div>

<div class="note rule-top" v-click>数据规模较小（16 名选手），直接用 SQL 查询，未建立向量检索和知识图谱。</div>

</div>

<!--
【25 秒】这一页按智能体的五个基本组成来对照我们的实现。任务拆解是固定的五步流程，加上三个角色的顺序分工；工具调用有三个只读工具，由模型决定调用哪个，最多三轮；记忆方面，每次请求从数据库读取最新数据，调用和采纳都有记录，调用记录用哈希链串起来防篡改，不做跨会话的对话记忆；护栏覆盖输入、输出和运行三个环节；专业知识来自提示词、规则版阈值和带原因的价格历史。数据量小，没有建立向量检索和知识图谱。

**【可能被问】**

**问**：任务拆解是模型自己规划的吗？

答：主流程是固定的五步，由代码决定，便于测试和兜底；在工具调用这一步，查哪些数据由模型自己决定，只能用白名单里的三个工具，最多三轮，超出就改用规则版。

**问**：为什么没有长期记忆？

答：每次建议只需要这位选手的当前行情和当前用户的持仓，这些每次都从数据库实时读取，比记忆更准确。历史上的每次调用和用户的采纳、忽略都存在审计表里，可以回查，但不会再喂给模型。

**问**：审计记录怎么防篡改？

答：每条调用记录写入时，把它的内容和上一条记录的哈希一起做 SHA-256，存成本条的哈希，记录一条接一条串成链。改动任何一条内容，它的哈希就对不上；删掉中间一条，下一条就接不上。GET /api/agent/traces/verify 会从头重算，报告第一处断开的位置。它能发现篡改，但不能阻止能直接改库的人整条重算，这需要把最新哈希另存到库外，我们没有做。

**问**：为什么不做 RAG 或知识图谱？

答：只有 16 名选手，结构化数据用 SQL 直接查就够了；做 RAG 需要真实赛事语料，涉及版权和合规，所以没有做。

**问**：护栏怎么防止提示词注入？

答：接口只接收选手编号，没有可以写字的入口；提示词按白名单只取 12 个字段，不含口令和其他用户的数据；模型输出必须通过 6 个字段和取值校验，否则改用规则版。红队测试 11 条都通过了。

**问**：模型被人反复调用怎么办？

答：全站每分钟最多调用 60 次模型，超出后直接用规则版，不报错、不联网。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.4 数据库设计</div>

# 数据库：9 张表分别存什么

<div class="body">

<div v-click>

<table class="tight db9">
<thead><tr><th>用途</th><th>表</th><th>存什么</th></tr></thead>
<tbody>
<tr><td rowspan="2">账号</td><td class="mono">users</td><td>每个用户一行：用户名、当前余额、初始余额、加密后的密码</td></tr>
<tr><td class="mono">auth_tokens</td><td>登录凭证：登录后发放，30 天有效，退出即作废</td></tr>
<tr><td rowspan="2">市场</td><td class="mono">players</td><td>每位选手一行：名字、战队、位置、现价、上一次价格、表现评分</td></tr>
<tr><td class="mono">price_history</td><td>每次价格变化一行：选手、新价格、时间、变化原因</td></tr>
<tr><td rowspan="2">交易</td><td class="mono">positions</td><td>持仓：哪个用户持有哪位选手、几股、买入均价</td></tr>
<tr><td class="mono">trades</td><td>交易流水：每笔买卖的方向、数量、成交价、金额、成交后余额</td></tr>
<tr><td rowspan="3">智能体</td><td class="mono">agent_traces</td><td>每次调用智能体的记录：用途、模型还是规则版、耗时、输出内容</td></tr>
<tr><td class="mono">decision_logs</td><td>用户对建议点了采纳还是忽略</td></tr>
<tr><td class="mono">price_narratives</td><td>价格变化的文字解读，按价格点保存，避免重复调用模型</td></tr>
</tbody>
</table>

</div>

<div class="text" v-click>买入一次同时改 3 张表：<span class="mono">users</span> 扣余额、<span class="mono">positions</span> 加股数、<span class="mono">trades</span> 记流水；三步在同一个事务里，要么全部成功，要么全部撤回。</div>

</div>

<!--
【25 秒】数据库一共九张表，按用途分四组：账号、市场、交易和智能体。表格右边写了每张表存什么，比如 players 每位选手一行，trades 每笔买卖一行。下面是一个例子：买入一次会同时修改三张表，扣余额、加股数、记流水。这三步放在同一个事务里，要么全部成功，要么全部撤回，扣款时还会先确认余额充足，所以两笔订单同时提交也不会超卖。

**【可能被问】**

**问**：什么是事务？

答：把几步数据库操作打包成一个整体，要么全部完成，要么一步都不生效。比如买入时余额扣了、但写流水失败，整笔会撤回，余额恢复原样。

**问**：表和表之间怎么关联？

答：通过编号关联。positions 和 trades 里都记着用户编号和选手编号，分别指向 users 和 players；price_history 记着选手编号。

**问**：为什么不用 SELECT FOR UPDATE 加锁？

答：本地的 SQLite 会忽略这种加锁写法，本地测试全通过、线上才生效，风险最大。我们用「余额充足才扣」的条件更新，SQLite 和 Postgres 行为一致。

**问**：金额精度怎么保证？

答：数据库用定点小数，保留两位；程序里全程用 Decimal 计算，不用浮点数。

**问**：密码怎么存？

答：不存明文。密码加盐后做 10 万次哈希，只存结果；登录凭证也只存哈希值。

**问**：用户删号后数据怎么处理？

答：删号要再输一次密码，会一起删除他的持仓、流水和登录凭证。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.5.5 接口与 3.5.6 前端设计</div>

# 接口：网页向后端取数据、提交操作的入口

<div class="body">

<div v-click>

<table class="tight api5">
<thead><tr><th>页面上的操作</th><th>网页调用的接口</th><th>后端做什么</th></tr></thead>
<tbody>
<tr><td>打开市场页</td><td class="mono">GET /api/players</td><td>返回 16 名选手的现价和涨跌</td></tr>
<tr><td>点「买入」</td><td class="mono">POST /api/trades/buy</td><td>检查余额和持仓上限，扣款、加股数、记流水</td></tr>
<tr><td>登录</td><td class="mono">POST /api/auth/login</td><td>核对密码，返回登录凭证</td></tr>
<tr><td>打开 1 号选手详情</td><td class="mono">GET /api/analysis/1</td><td>返回智能体对这位选手的建议（6 个字段）</td></tr>
<tr><td>上线检查</td><td class="mono">GET /api/health</td><td>返回服务是否正常运行</td></tr>
</tbody>
</table>

</div>

<div class="g g-1-1 rule-top" v-click>
  <div class="text"><span class="label">怎么看　</span>GET 表示读取数据，POST 表示提交操作；路径最后的数字是选手编号。共 30 个接口：行情 3、交易与账户 7、账号 5、智能体 10、运维 5。</div>
  <div class="text"><span class="label">前端　</span>8 个页面；价格曲线用 SVG 绘制；颜色和间距统一定义，深色、浅色主题共用一份代码。</div>
</div>

</div>

<!--
【25 秒】接口是网页和后端之间的入口：页面上每做一个操作，网页就调用一个接口，后端处理后把结果返回。表格按「页面操作、调用的接口、后端做什么」列了五个例子，比如点「买入」，网页调用 POST /api/trades/buy，后端检查余额和持仓上限后完成扣款。GET 表示读取数据，POST 表示提交操作。一共二十九个接口，分五组。前端有八个页面，深色和浅色主题共用一份代码。

**【可能被问】**

**问**：接口和页面是什么关系？

答：页面负责显示，接口负责提供数据和执行操作。一个页面通常会调用几个接口，比如详情页同时调用选手信息、价格历史和智能体建议三个接口。

**问**：30 个接口分别有哪些？

答：行情 3 个（选手列表、选手详情、价格历史），交易与账户 7 个（买入、卖出、持仓、流水、账户、资产曲线、重建余额），账号 5 个（注册、登录、当前身份、退出、删号），智能体 10 个，运维 5 个（健康检查、数据库自检、日志、重灌数据、赛后结算）。完整列表可在在线接口文档 playerstock-backend-mdlk.onrender.com/docs 查看并直接试用。

**问**：出错时接口返回什么？

答：统一返回中文提示和错误码，比如余额不足返回错误码 INSUFFICIENT_BALANCE，并提示最多还能买几股。AI 接口出错不会报错，直接返回规则版建议。

**问**：登录怎么做的，用 JWT 吗？

答：没用 JWT。登录后发一个随机凭证，库里只存它的哈希，30 天有效，退出即作废；同一用户名 10 分钟内输错 5 次会先锁住。

**问**：为什么不用状态库？

答：页面状态不复杂，用组合函数共享就够了，少一层概念，组员上手快。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.6 软件质量</div>

# 软件质量：384 条后端测试，覆盖率 97%

<div class="body">

<div class="stats" v-click>
  <div><div class="num">384</div><div class="what">后端测试</div><div class="how">单元 329 · 集成 22 · 评测 33</div></div>
  <div><div class="num">191</div><div class="what">前端测试</div><div class="how">Vitest，23 个测试文件</div></div>
  <div><div class="num accent">97<small>%</small></div><div class="what">核心代码覆盖率</div><div class="how">app + core_engine<br>含智能体模块为 95%</div></div>
  <div><div class="num">4</div><div class="what">CI 检查</div><div class="how">冲突标记 · 后端<br>前端 · 交付物</div></div>
</div>

<div class="g g-1-1 rule-top" v-click>
  <div>
    <div class="label">3.6.1 运行时</div>
    <div class="text">出错时统一返回错误码和中文提示，不向用户暴露报错细节；请求和返回均做格式校验；交易通过条件更新防止并发问题，并有同时卖出的测试。</div>
  </div>
  <div>
    <div class="label">3.6.2 代码规范</div>
    <div class="text">Python 使用 ruff，函数复杂度上限 10；前端使用 oxlint 和 eslint，要求零警告，并做类型检查。CI 只做检查，不自动修改代码。</div>
  </div>
</div>

</div>

<!--
【30 秒】后端三百六十六条测试，前端一百八十七条，每次提交都自动跑。核心代码，也就是交易和定价部分，覆盖率百分之九十八；把智能体模块也算进去是百分之九十五。测试看的是结果对不对，比如余额对不对、会不会超卖，而不是页面有没有显示。代码规范由 ruff、oxlint 和 eslint 检查，零警告才算通过。

**【可能被问】**

**问**：97% 为什么不算智能体？

答：97% 统计的是交易和定价的代码；智能体有一部分要真的联网调用模型，离线测不到，单独算。全部算上是 95%，两个数字我们都公开。

**问**：剩下没覆盖的是什么？

答：主要是数据库初始化失败、并发竞争的兜底分支，属于防御性代码，覆盖成本高，在测试报告里逐条列了。

**问**：能现场跑一下吗？

答：可以，仓库根目录运行 pytest，大约一分钟跑完。

**问**：CI 的 4 项检查是什么？

答：冲突标记检查；后端，先 ruff 再 pytest；前端，代码规范、单元测试和构建；交付物，检查必需文档是否齐全、有没有误提交的文件。
-->

---

<div class="kicker"><b>03</b> 产品实现 · 3.7 代码统计</div>

# 代码统计：约 3.5 万行，AI 初稿约占 39%

<div class="body">

<div class="g g-5-7">
  <div v-click>

<table class="tight">
<thead><tr><th>类型</th><th style="text-align:right">文件</th><th style="text-align:right">行数</th></tr></thead>
<tbody>
<tr><td>Python</td><td style="text-align:right">116</td><td style="text-align:right">17,617</td></tr>
<tr><td>Vue</td><td style="text-align:right">21</td><td style="text-align:right">8,993</td></tr>
<tr><td>TypeScript</td><td style="text-align:right">49</td><td style="text-align:right">6,448</td></tr>
<tr><td>CSS / HTML</td><td style="text-align:right">7</td><td style="text-align:right">2,051</td></tr>
<tr><td>代码合计</td><td style="text-align:right">193</td><td style="text-align:right" class="hl">35,109</td></tr>
<tr><td>Markdown 文档</td><td style="text-align:right">76</td><td style="text-align:right">9,365</td></tr>
</tbody>
</table>

  </div>
  <div class="body" style="gap:1.1rem">
    <div v-click>
      <div class="label">AI 辅助情况</div>
      <div class="quote" style="font-size:1.12rem">前端业务代码和原型由 AI 生成初稿，约占全部代码的 39%，经组员逐行审阅修改。交易、定价和接口约定由组员编写并互相评审。</div>
    </div>
    <div class="note" v-click>模块：前端 8 个页面、12 个组件；后端 11 个路由模块、8 个智能体模块、1 个定价引擎。按 git 跟踪的文件统计，2026-11-28。</div>
  </div>
</div>

</div>

<!--
【15 秒】代码一共三万五千行左右，文档九千多行。我们如实说：前端业务代码和原型是 AI 先出初稿的，大约占全部代码的百分之三十九，组员一行行看过、改过。交易、定价和接口约定这些核心部分是我们自己写的，并且互相评审过。

**【可能被问】**

**问**：39% 是怎么算出来的？

答：按文件统计：前端业务代码 13025 行加原型 591 行，约 13616 行，除以当时全部代码 34575 行，约 39%。测试和文档里也有 AI 参与，但和人工修改混在一起，没有计入。

**问**：怎么证明你们看懂了 AI 写的代码？

答：每一行都经过负责人阅读、本地运行和测试；老师可以任选一段代码，我们现场讲清楚它在做什么。

**问**：行数是怎么统计的？

答：按 git 跟踪的文件，分扩展名数行数，不含依赖目录和构建产物。
-->

---

<div class="kicker"><b>04</b> 验收 · 测试与容量</div>

# 验收：线上评测 16/16，红队测试 11/11

<div class="body center">

<div class="stats" v-click>
  <div><div class="num">32<small>/33</small></div><div class="what">用户测试检查表</div><div class="how">1 项部分通过<br>另与外组互测，各 33 题</div></div>
  <div><div class="num accent">16<small>/16</small></div><div class="what">线上真模型评测</div><div class="how">输出全部合规<br>95% 请求在 3.39 秒内返回</div></div>
  <div><div class="num">11<small>/11</small></div><div class="what">红队测试</div><div class="how">提示注入、越权<br>伪造来源</div></div>
  <div><div class="num">38<small>次/秒</small></div><div class="what">只读压测</div><div class="how">约 190 人同时在线<br>全程 0 错误</div></div>
</div>

<div class="note rule-top" v-click>说明：比赛数据为模拟数据，因此未评估真实比赛的预测准确率；外部用户测试样本较少。证据见 docs/acceptance/，共 147 张截图。</div>

</div>

<!--
【25 秒】验收看四个数：用户测试检查表三十三项，三十二项通过，一项部分通过；线上用真模型测了十六个用例，全部合规，百分之九十五的请求三秒多返回；红队测试十一条全拦下；压测每秒三十八个请求，大约够一百九十人同时在线，瓶颈在免费服务器。没做的我们也说清楚：比赛数据是模拟的，所以没有评估预测准不准。

**【可能被问】**

**问**：哪一项部分通过？

答：推荐意愿那一项：要真实外部用户打 0 到 10 分，我们只有组内的 7 分和外组评审，样本不够，就如实记成部分通过。

**问**：红队测了什么？

答：试图往提问里注入指令、让模型改写动作、伪造来源、夹带别人的持仓、输出乱码或超长内容等 11 种，结果都被固定字段检查或规则版兜住。

**问**：190 人是怎么估的？

答：压测时并发从 40 加到 80，吞吐稳定在每秒约 38 个请求、零错误。按浏览型用户每 10 秒操作一次、每次 2 个请求，即每人每秒 0.2 个请求，38 除以 0.2 约等于 190。只压了只读接口，交易和 AI 接口没压，免得弄脏数据、耗模型额度。

**问**：外组互测结果？

答：我们测了 Tome 组 33 题；对方测我们 33 题，28 通过、4 部分、1 未覆盖，原件都在 docs/acceptance。
-->

---

<div class="kicker"><b>05</b> 现场演示</div>

# 现场演示：从查看行情到完成买入

<div class="body center">

<div class="g g-1-1">
  <div class="numbered" v-click>
    <div><span class="n">01</span><div><div class="t">市场页</div><div class="d">看简报、选手卡和停牌状态</div></div></div>
    <div><span class="n">02</span><div><div class="t">详情页</div><div class="d">看走势、每次涨跌的原因和智能体建议</div></div></div>
    <div><span class="n">03</span><div><div class="t">买入 2 股</div><div class="d">余额、持仓和流水跟着变</div></div></div>
  </div>
  <div class="numbered" v-click>
    <div><span class="n">04</span><div><div class="t">个人页</div><div class="d">看资产曲线和交易统计</div></div></div>
    <div><span class="n">05</span><div><div class="t">异常情况</div><div class="d">停牌选手无法买入；模型不可用时显示规则版建议</div></div></div>
    <div><span class="n">06</span><div><div class="t">回到市场</div><div class="d">结束演示</div></div></div>
  </div>
</div>

<div class="note" v-click>网络不稳定时先刷新页面，仍无法访问则播放备用录屏。</div>

</div>

<!--
【5 秒】下面现场演示：从市场页点进一位选手，看建议，买两股，再看持仓和流水怎么变。

**【演示提醒】**

上台前 10 分钟打开 /api/health 预热；先重置演示数据。

停牌演示：找本轮正在比赛的战队选手，买入按钮是灰的。

模型不可用演示：如果现场网络慢，建议卡会标「规则版」，正好可以讲兜底。

卡住时先刷新；还不行就切到备用录屏，不要现场排查。
-->

---

<div class="end cover">

<div class="kicker">结课项目审查</div>

<div class="cover-title" style="font-size:3.4rem">谢谢，请老师指导。</div>

<dl class="dl rule-top" style="max-width:46rem">
  <dt>在线演示</dt><dd class="mono">playerstock-frontend-mdlk.onrender.com</dd>
  <dt>源码</dt><dd class="mono">github.com/July75-bit/Innovation</dd>
  <dt>材料</dt><dd class="mono">july75-bit.github.io/Innovation/playerstock_defense.pdf</dd>
  <dt>小组</dt><dd>有请下一组 · 王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）</dd>
</dl>

</div>

<!--
【结束】我们的汇报就到这里。在线地址、源码和这份材料的 PDF 都在这一页。谢谢各位老师，请老师指导。

**【问答时的答法】**

先给结论，再给一个数字或例子，30 秒内说完；没做到的直接说没做到和原因，不要编。

最容易被追问的三点：多智能体是同一个模型三个身份；97% 覆盖率不含智能体，全算是 95%；AI 初稿约占 39%，每行都看过。
-->
