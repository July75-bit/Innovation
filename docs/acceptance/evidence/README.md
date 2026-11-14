# 验收证据截图（M3 / T3-04 + T4 前端项）

> 采集时间：2026-10-24（第 4 天）｜ 采集方式：真实后端（uvicorn :8000，seed 重置 + 8 轮模拟价格）
> + 真实浏览器（Chromium headless，1280×900 全页截图）｜ 环境：`VITE_USE_MOCK=false` 真实接口模式

## T3-04 全链路（查行情 → 买 2 股 → 持仓 → 卖 1 股 → 流水）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `01-market.png` | 市场页 | 8 名选手、涨跌幅、"模拟数据"标注、sh1ro 暂停置灰、徽标"连接成功：playerstock-backend"、余额 5000.00 |
| `02-detail-chart-ai.png` | ZywOo 详情页 | **T4-01** 折线图 10 个价格点；**T4-02** 涨跌原因 latest_reason；**T4-04** AI 建议卡（action/reason/risk/source/disclaimer） |
| `03-buy2-success.png` | 买入 2 股 | 后端返回"买入成功"，余额 5000→4747.46 |
| `04-positions.png` | 持仓页 | 2 股、均价/现价/市值/盈亏（后端算好值直显） |
| `05-sell1-success.png` | 卖出 1 股 | 后端返回"卖出成功"，余额→4873.73 |
| `06-trades.png` | 交易流水 | 时间倒序、方向/数量/成交价/金额/交易后余额 |

## 5 条错误分支（后端中文 message 原样展示，不重试）

| 文件 | 分支 | 实测消息 |
| --- | --- | --- |
| `07-err-insufficient-balance.png` | 余额不足 | 余额不足，当前余额 4873.73，需要 6313.50 |
| `08-err-position-limit.png` | 超 50 股上限 | 超过单选手持仓上限 50 股，当前持有 49 股，本次买入 2 股 |
| `09-err-insufficient-position.png` | 持仓不足 | 持仓不足，当前持有 1 股，本次卖出 10 股 |
| `10-err-invalid-qty.png` | 非法数量 | 前端拦截"数量必须是正整数"，按钮禁用（不发请求） |
| `11-suspended.png` | 暂停交易 | sh1ro 面板黄字提示 + 买卖按钮禁用 |

## T4-05 三态

| 文件 | 状态 | 触发方式 |
| --- | --- | --- |
| `12-state-loading.png` | 加载中 | 延迟 `/api/players` 响应 2s |
| `13-state-empty.png` | 空数据 | `/api/players` 返回 `[]` |
| `14-state-offline-error.png` | 失败（拔网线） | 真实停止后端进程：错误条"无法连接后端服务…"+ 重试按钮 + 顶栏徽标"后端未连接" |

## T4-02 每点 reason 展示（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `15-t4-02-point-reason.png` | ZywOo 详情页折线图：悬停 #3 数据点 + 展开「价格变动明细（10）」 | tooltip 显示 `2026-11-01 08:00:00 · 107.10 币` + "本场表现下滑（S=-1.00），价格下跌 15.00%（本轮模拟得分 76.6）"，与 `GET /api/players/1/prices` 第 3 点逐字一致；明细列表 10 行逐点带 时间/价格/reason |

## TC-307 刷新持久化（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `16-tc307-refresh-persist.png` | 深链 `/players/1` 直接打开后 F5 刷新全页 | 余额 / 价格历史（10 点）/ AI 卡 / 持仓提示全部由后端重建，无丢数据、控制台零报错 |

## 代码质量扫描报告（第 4 天补）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `17-code-quality-scan.png` | 代码质量报告截图（实际命令输出渲染） | `pytest` 120 passed；`ruff check --statistics .` 第 3 次扫描 72 项（D 负责文件 0）；CI 三门槛全绿；含重构前后对比 |

## 线上验收（第 5 天，Render）

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| `online/online-account-5000.png` | `GET /api/account` | 线上余额 5000.00 / 总资产 5000.00 |
| `online/online-positions-empty.png` | `GET /api/positions` | 交易测试后清仓为空 |
| `online/online-trades-before-tc403.png` | `GET /api/trades` | **TC-403 之前的历史状态（空）**，仅作对照，不作为验收证据；当前线上为 8 条流水（见 test_report TC-404） |
| `online/online-prices-11points.png` | `GET /api/players/1/prices` | 11 个点、升序、末点 108.75 = current_price、reason 含「本轮得分 + S」 |

## 线上重新部署复验（第 6 天 7.2，2026-11-07）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `online/online-persistence-before-{1,2,3}-*.png` | Manual Deploy **之前**的 account / trades / prices | 余额 5000.00、流水 **7 条**、价格 **11 点**（末点 108.75） |
| `online/online-persistence-after-{1,2,3}-*.png` | Deploy 变 Live **之后**的同三个接口 | 部署前那 7 条流水一条不少；期间新增 1 笔（m0NESY BUY ×10 @85.08）→ 余额 4149.20、流水 8 条、持仓市值 850.80，总资产仍 5000.00；价格仍 11 点逐点一致 |
| `online/persistence-redeploy.md` | 逐项对账记录 + 复跑命令 | `scripts/persistence_check.py --diff` 退出码 0；含"余额变了为何不等于丢数据"的算术闭合 |

> 复现方式见 `code/frontend/README.md`（启动步骤）与 `docs/software/database_design.md` §4.1（价格点配方）。
  > **现状（2026-11-14 重灌后）**：16 名选手 / 8 队；每人 11 价格点（ropz 10，种子仅 1 条）/ 余额 5000.00 / 持仓 0 / 流水 0；暂停交易改为**队伍级派生**——每轮 2 队（4 人）停牌，第 12 轮为 Vitality vs Spirit。
  > **待补三张整队停牌证据**（A/B 截）：① 市场页第 12 轮 Vitality/Spirit 四人置灰；② 任一停牌选手详情页「比赛中，暂停交易」；③ 同轮可交易选手（如 huNter-）可买作对照。
> 上面 `online-*` 截图是重置前后的历史留档，数字以本行为准。

## 汇报证据（3.6 / 3.7 / 3.3）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `18-quality-pylint-pep8.png` | Pylint 语义分析 + PEP8 + 格式化体检 | Pylint 9.74/10（无 E/F 级）；`ruff check --select E,W` 25 项全为 E501；`ruff format --check` 31 待格式化 / 39 已格式化 |
| `37-pytest-coverage.png` | 3.6 质量工具：回归 + 覆盖率（2026-11-07 本机复跑） | `pytest -q` → **320 passed / 0 skipped**；`--cov=app --cov=core_engine` → **TOTAL 1823 语句 / 45 未覆盖 / 98%**（要求 ≥60%）；pricing / simulator / database / price_update / rules 与 5 张表模型均 100%，仅 trades 的 3 处 rowcount 竞态兜底与少量平台分支未覆盖 |
| `19-complexity-stats.png` | 认知复杂度 + 代码统计（3.7） | complexipy 48 文件 / 149 函数，最大 27、均值 3.31；Python 70 文件 8342 行、Vue 10 / 1737、TS 12 / 852、MD 41 / 6489，合计 133 文件 / 17420 行 |
| `20-commit-stats.png` | 3.3 提交统计：本地准数 × pulse 按账号数 | 全周期（develop，排除合并）137 次：D 50 / B 41 / C 26 / A 20，合计 +36072 / −4257；pulse 近一月 49 / 41 / 28 / 20。B 的 41 = 以 `Hu De Hao` 提交 38 条 + 以账号名 `July75-bit` 提交 3 条（B 本人确认） |
| `21-pulse-overview.png` | GitHub Pulse 总览（2026-10-06 → 11-06，1 month） | `4 authors have pushed … 138 commits to all branches`；`On main, 0 files changed`（main 只走 PR 合并，非异常） |
| `22-pulse-top-committers.png` | Pulse → Top committers 弹窗 | wlkaqw 49 · July75-bit 41 · fusde0 28 · weedflame 20 = 138；`July75-bit` 为 B 的账号（41 = B 的 38 + 账号自身 3） |
| `23-responsive-375-market.png` | 375px 市场页（A4） | 表格转**卡片**；搜索/筛选/排序全部收起；无横向溢出。余额 4149.20 是验收操作后的状态 |
| `24-responsive-375-detail.png` | 375px 选手详情（A4） | 标题与价格上下排、折线图整宽、AI 卡单列 |
| `25-responsive-375-positions.png` | 375px 持仓（A4） | 四个指标卡两列排布；持仓行转卡片（持仓/均价/现价/市值/盈亏/操作） |
| `26-responsive-375-trades.png` | 375px 交易记录（A4） | 表格转卡片：时间/方向/选手/数量/成交价/金额/交易后余额 |
| `27-responsive-375-nav-drawer.png` | 375px 导航抽屉（A4） | 侧栏以抽屉展开：市场/持仓/交易记录 + 余额/总资产/总收益 + 连接状态；点「菜单」开关 |
| `28-keyboard-focus.png` | 键盘可达（A6） | 折线图首点获得焦点（`:focus-visible` 描边）+ tooltip「2026/10/24 18:18:21 · 120.00 币 · 初始价格」 |

| `29-ai-loading.png` | AI「分析中…」占位态（A5） | 375px 详情页：AI 卡片处显示「**AI 分析中…（行情与交易不受影响）**」+ 三点动画，同时下方交易面板已可用（说明行情/交易不被 AI 阻塞） |
| `35-projects-list.png` | 仓库 Projects 页：协作三件套已建（2026-11-07，当时为 Private） | PlayerStock_Kanban(#1) / Team planning(#2) / Bug tracker(#3) |
| `38-projects-public-incognito.png` | **协作三件套已 Public（2026-11-14 无痕窗口实测）** | 未登录状态（右上角 Sign in / Sign up）仍能看到三个项目：Bug tracker(#3) / Team planning(#2) / Kanban(#1)，Open 3 / Closed 0 → 证明匿名可见 |
| `39-ui-redesign-before-detail.png` | **界面改版前 · 详情页**（2026-11-14 14:44） | AI 卡一张里堆 9 块内容：来源行、理由、红框归因、四格数字（仓位/止损/置信度 48%/余额）、两条依据、说明、采纳按钮、免责；工具调用直接显示英文函数名与 JSON 参数 |
| `40-ui-redesign-after-detail.png` | **界面改版后 · 详情页**（2026-11-14 15:01） | 结论优先：[买入] + 一句人话理由 + 风险/把握 chip；第二层只留「可买 N 股 / 参考止损」；「为什么这么建议 / 三个角色怎么看 / 它查了哪些数据」三块默认折叠 |
| `41-ui-redesign-after-market.png` | **界面改版后 · 市场页**（2026-11-14 15:01） | 今日简报改两列对齐（标题列 96px）；技术标签「规则兜底」隐藏；侧栏徽章改「服务正常」 |
| `42-ui-redesign-after-375.png` | **界面改版后 · 375px 移动端**（2026-11-14 15:01） | 结论/风险/数字/折叠自上而下堆叠；`scrollWidth/innerWidth = 375/375` 无横向滚动 |
| `43-ui-redesign-panel.png` | **改版后 · 协作纪要展开态**（2026-11-14 15:01） | 模型不可用时不显示 `LLMOutputError` 等技术信息，改为「三个角色本次未能给出纪要（不影响行情与交易）」 |
| `44-brief-before-json-leak.png` | **简报 bug 现场**（用户 2026-11-14 截图） | 首页「今日简报」摘要直接显示 `{"action": "HOLD", "reason": "sh1ro 现价 136.43…`——模型返回 JSON，后端只截断就透传 |
| `45-brief-after-clean.png` | **修复后 · 首页简报**（2026-11-14 15:30） | 标题「今日简报」+ 大号一句话总述 + 三列要点卡（今日最该看一眼 / 低价区标的 / 停牌提醒），无花括号与字段名 |
| `46-ui-v2-before.png` | **UI v2 改版前**（2026-11-14 15:40 前） | 背景带径向渐变 + 40px 网格纹理；状态点发光；圆角 8/12/16/999 混用；正文 14px、辅助 11–12px；导航选中整块主色红 |
| `47-ui-v2-after-market.png` | **UI v2 · 市场页**（2026-11-14 15:42） | 纯扁平：无渐变/发光；圆角 4/6/8；正文 16px；导航选中改中性高亮 + 主色竖条（红色只留给 CTA 与涨跌） |
| `48-ui-v2-after-detail.png` | **UI v2 · 详情页** | 结论卡三层结构 + 交易面板常驻；主按钮 44px；AI 卡无红框、无四格数字噪音 |
| `49-ui-v2-after-375.png` | **UI v2 · 375px** | 无横向滚动（375/375），点击区 ≥44px |
| `50-ui-v2-after-login.png` | **UI v2 · 登录页** | 渐变背景与发光全部清除，改为扁平底色 + 1px 边框 |
| `51-design-tokens-after-detail.png` | **设计 Token 接入后 · 详情页**（2026-11-14 15:58） | 买入/卖出改用 AA 合规底色（`#c23438` 白字 5.47:1、`#1a7f4b` 白字 5.02:1）；间距/圆角/字号全部走 `tokens.css`，组件零改动（兼容层映射） |
| `52-design-tokens-after-market.png` | **设计 Token 接入后 · 市场页** | 简报与卡片沿用统一样式令牌；4/6/8 圆角、1px 边框、无阴影 |
| `53-ui-kit-full.png` | **UI 组件库预览页**（`/ui-kit`，2026-11-14 16:10） | 按钮 4 变体 × 3 尺寸 × loading/disabled；输入框含 hint/error/后缀/禁用；下拉；5 种标签；卡片 3 态；表格（排序）；分页 96 条；导航选中态 |
| `54-ui-kit-modal.png` | **危险确认弹窗** | 无 ✕（dismissible=false）、取消在左、红色确认在右、遮罩 72% |
| `55-ui-kit-375.png` | **组件库 375px** | 无横向滚动（375/375），按钮/输入框/表格均可用 |
| `56-liquid-glass-desktop-market.png` | **液态玻璃 · 桌面市场页**（2026-11-14 16:40，1280×900） | 唯一玻璃 = 侧栏壳（232×900，**可见玻璃 18.13%** ≤30%）；内容层卡片/简报/筛选全实色扁平；侧栏内账户卡与合规声明仍为实色（玻璃+实色两层） |
| `57-liquid-glass-detail-tooltip.png` | **液态玻璃 · 图表 tooltip** | 悬停折线数据点 → 玻璃浮层（tint 0.74 / blur 22 / 圆角 20 / 极轻投影）；同屏玻璃 18.13%+tooltip=**19.97%** |
| `58-liquid-glass-mobile-topbar-blur.png` | **液态玻璃 · 移动顶栏（滚动中）** | 375×667 滚动 460px：内容从玻璃顶栏下方穿过并**真实模糊**（简报卡文字在玻璃后可见但柔和）；玻璃仅顶栏 375×55 = **8.25%** |
| `59-liquid-glass-mobile-drawer-solid.png` | **移动抽屉 = 实色 sheet** | 抽屉 293×667 若做玻璃会到 78% 配额，且是导航+账户+合规文字密集区 → 实色 + 圆角 24 + 轻投影 |
| `60-liquid-glass-modal-desktop.png` | **液态玻璃 · 模态框** | 玻璃面板 400×263（圆角 20，内高光+极轻投影）；遮罩 0.66 **无 blur**（模糊只由玻璃层承担，避免玻璃叠玻璃）；弹窗单独占屏 **9.10%** |
| `61-liquid-glass-kit-gallery.png` | **/ui-kit 材质展厅** | 导航壳 / 悬浮工具条 / Popover / 浅色玻璃 / 配额读数 / 降级开关 / 主题切换；展厅同屏多块属演示性质（38–44%），业务页见 56–58 |
| `62-liquid-glass-fallback.png` | **降级实测（不支持 backdrop-filter）** | 点「模拟降级」→ `<html class="no-backdrop-filter">`：全部玻璃变不透明实色（`blur=none`、底 `rgb(23,26,33)`），可见玻璃面积 **0%**，圆角/描边/内高光保留 |
| `63-liquid-glass-mobile-modal-solid.png` | **移动端弹窗 = 实色底部 sheet** | ≤600px 弹窗接近全屏 → 实色、上沿圆角 24、无模糊（玻璃配额与表单可读性双重要求） |
| `64-liquid-glass-focus-ring.png` | **玻璃上的键盘焦点环** | 工具条按钮 `:focus-visible` → `solid 2px rgb(239,115,119)`，圆角保持控件值；玻璃面板圆角 20 不再被全局焦点样式打成 6（本轮修掉的 bug） |
| `65-liquid-glass-reduced-transparency.png` | **prefers-reduced-transparency: reduce** | Edge 157 模拟该偏好：`backdrop-filter: none` + 实色底 `rgb(23,26,33)`，hover 半透明高光同时关闭（对比度反而更高） |
| `66-tokens-light-market.png` | **设计令牌 v2 · 浅色模式市场页**（2026-11-14 17:08） | `[data-theme="light"]` 全量令牌生效：画布 `#f4f6f9`、表面 `#fff`、正文 `#1a1d23`；侧栏玻璃 `rgba(255,255,255,.62)` + 描边 `.72`；同屏玻璃 18.13%（≤30%） |
| `67-tokens-light-mobile.png` | **设计令牌 v2 · 浅色模式移动顶栏** | 375px 滚动中：浅色玻璃顶栏（`--glass-bg` `.62`）压在内容上；玻璃面积 8.25%，无横向溢出 |
| `68-tokens-dark-market-v2.png` | **设计令牌 v2 · 深色模式市场页** | 深色玻璃按规范示例值 `rgba(20,20,20,.60)` + scrim `.72`：玻璃上文字实测最低 8.55:1；玻璃面积 18.13% |
| `69-theme-light-market.png` | **浅色模式 · 市场页**（2026-11-14 17:26，主题切换实测） | `[data-theme="light"]` 全量令牌：画布 `#f4f6f9`、卡片 `#fff`、正文 `#1a1d23`；涨跌文字改用 `--up-text`（#c23539，5.1:1）；侧栏玻璃 `rgba(255,255,255,.62)`；侧栏新增「浅色/深色」切换按钮 |
| `70-theme-dark-market.png` | **深色模式 · 市场页** | 同一套令牌的深色分支；切换后无闪烁（index.html 内联脚本先定主题） |
| `71-theme-light-detail.png` | **浅色模式 · 选手详情** | AI 卡/折线图/交易面板全部保持实色内容层；只有侧栏壳是玻璃；买入 CTA 实色 `#b02a2e` 白字 |
| `72-theme-light-schedule.png` | **浅色模式 · 赛程** | 停牌/轮次徽章：警告文字 `#7a4d0a` on `#e1d4c1` = 4.9:1（修掉了 4.05:1 的原值） |
| `73-theme-mobile-bottomtab-light.png` | **移动端 · 玻璃底部 Tab（浅色）** | 375×667：悬浮玻璃 Tab 栏（圆角 20、scrim .72），4 个 Tab 各 83×48（点击区 ≥44）；内容区留 96px 底距 |
| `74-theme-mobile-bottomtab-dark.png` | **移动端 · 玻璃底部 Tab（深色）** | 同结构深色玻璃；选中态 = 中性高亮 + 2px 主色指示条 |
| `75-select-popover-dark.png` | **玻璃下拉（深色）** | 触发框=内容层实色输入框；弹层=玻璃 panel（实测 radius 20 / blur 22 / bg `.72`），选中项带 ✓ |
| `76-select-popover-light.png` | **玻璃下拉（浅色）** | 同一弹层浅色分支：`rgba(255,255,255,.72)` + 1px 内高光，文字 `#1a1d23` |
| `77-modal-open-light.png` | **玻璃弹窗（浅色）** | 圆角 20 / 极轻阴影 / 遮罩 0.32 纯压暗；`aria-labelledby` 指向标题（可访问性核对） |
| `78-toolbar-light.png` | **悬浮工具栏（浅色）** | 圆角 12；内部按钮全部实色（禁止玻璃叠玻璃） |
| `79-desktop-topbar-dark.png` | **桌面玻璃顶栏 · 深色**（2026-11-14 17:50） | 新增 fixed 玻璃顶栏（56px，内容从它下面滚过）：页面标题/服务状态/余额/主题切换；实测 blur 贡献 2.55 均值、9.2% 像素明显变化 |
| `80-desktop-topbar-light.png` | **桌面玻璃顶栏 · 浅色** | 同一顶栏浅色分支；blur 贡献 1.69、7.2% 像素变化；标题/余额/主题按钮 AA 合规 |
| `81-desktop-modal-dark.png` | **玻璃弹窗 · 深色（A 项调整后）** | 遮罩 .72→.58、面板 scrim .72→.66：blur 贡献由 **0 → 2.03（12.6% 像素）**，背后内容开始"透出来" |
| `82-desktop-modal-light.png` | **玻璃弹窗 · 浅色** | 遮罩 .32→.26、面板 .72→.66：blur 贡献 **2.41 → 4.42（25.4% 像素）** |
| `83-select-popover-light-v2.png` | **下拉弹层 · 浅色（popover 档 .56）** | 弹层比面板更浅（`--glass-bg-popover`），blur 贡献 0.01→1.26（3.2%）；文字仍 AA |
| `84-pointer-glow.png` | **指针跟随高光（B 项）** | 鼠标移动到工具条 30%→70% 处，`--glow-x` 同步变化、`::after` 高光淡入；reduced-motion 下变量不写入、高光 opacity 恒 0 |
| `85-p1-light-market.png` | **P1 审美对齐 · 浅色市场页**（2026-11-14 18:25） | 参考 KPL 小助手：卡片留白 16→24、网格 4 列、边框更轻（#e5e8ee）、标题降噪（H1 28→24 / 区块 22→20 / 卡片 16）；侧栏选中 = 淡主色底 pill + 主色文字 |
| `86-p1-dark-market.png` | **P1 审美对齐 · 深色市场页** | 同一套改动在深色模式生效；内容卡 hover 只提亮边框（去掉位移 + 阴影） |
| `87-p1-light-positions.png` | **P1 · 持仓页** | 总览卡 padding 12/16→16、卡片间距 12→16、表格行高 44→56+ |
| `88-p1-light-kit-table.png` | **P1 · 表格实测** | `UiTable` 实测：行高 **59px**（原 ~44）、表头 **49px**、浅色表头 `#fafafa`、深色 `#262b34` |
| `89-p1-light-detail.png` | **P1 · 选手详情** | 列间距 24→32、卡片留白 24；可点文字统一 `--accent-text`（不再用纯红填充色当文字） |
| `90-p1-mobile-light-positions.png` | **P1 · 移动端持仓 375px** | 移动端同步生效，无横向溢出；标题/表格在 375 下仍按卡片降级 |
| `91-auth-light-desktop.png` | **登录页 · 浅色（修复后）**（2026-11-14 18:55） | 原浅色下"白底白字不可读"已修：页面改纯色画布 + 白色面板 + 深色文字；表单面板去掉玻璃/发光阴影；顶部/底部文案全部 token 化（对比度实测 0 违规） |
| `92-auth-dark-desktop.png` | **登录页 · 深色（同版新实现）** | 深色分支同样走语义令牌：深色画布 + 深色面板 + 浅色文字；与浅色共用一套结构，不再有硬编码的"只在深色下成立"的颜色 |
| `93-auth-light-375.png` | **登录页 · 浅色 375px** | 单列堆叠：品牌区在上、表单在下；输入框/按钮 44px 高；无横向溢出 |
| `94-auth-dark-375.png` | **登录页 · 深色 375px** | 同结构深色分支；标题与表单文字均可读 |
| `36-kanban-board.png` | Kanban 看板 Backlog 视图 | 五列 Ready 1 / In progress 1 / In review 1 / **Done 15**（day1~day3 检查类 Issue 均已归档），协作痕迹可视 |
| `pulse-committers.csv` | GitHub Pulse → Top committers 原始导出（2026-11-07） | wlkaqw 49 / July75-bit 41 / fusde0 28 / weedflame 21 = **139**；比 22 号截图时多 1 条（weedflame 20→21），统计窗口滚动，正常 |

## A-9 亲手走查（第 6 天，2026-11-07 14:37–15:06）

> 背景：A-1/A-2/A-3 的代码由 D 代写，`23~29` 归档后 A 逐页做了最终确认。这组是 **A 本人**在
> 线上 `playerstock-frontend-mdlk.onrender.com` 以 iPhone SE（375×667）走查的实拍（`day6.md` §7.1 委派单落地）。
> **时点说明**：拍摄于 2026-11-07 14:37–17:09，**此时线上仍是 8 名选手**；当晚种子扩至 16 名 / 8 队并重灌，
> 图中的"8 人市场与余额 4149.20"为当时真实状态，扩容后以线上实测为准（不影响 A-1/A-2/A-3 的布局/无障碍结论）。

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `30-a9-market-375.png` | `/` 市场页 375px | 顶栏折成「PlayerStock · 余额 · 菜单」一行；表格转**卡片**（ZywOo 108.75 −13.88% 等）；搜索 / 筛选（全部/交易中/暂停）/ 排序收起可用；更新于 14:37:26；容器均在 375 内、无横向溢出 |
| `31-a9-detail-375.png` | `/players/1` 详情 375px | 标题/战队/状态/表现分/价格**上下排**；「最近变动：本场表现下滑（本轮得分 81.3，S=-0.92），价格下跌 13.88%」直出后端 reason；折线图整宽；「查看价格变动明细（11）」与线上 11 点一致 |
| `32-a9-nav-drawer-375.png` | 375px 导航抽屉展开 | 点「菜单」→ 抽屉：市场/持仓/交易记录 + 余额 4149.20 / 总资产 5000.00 / 总收益 +0.00 +「连接成功: playerstock-backend」；底部合规声明完整；「关闭菜单」可退出 |
| `33-a9-positions-375.png` | `/positions` 持仓 375px | 四指标卡两列；持仓行转卡片（m0NESY 10 股 · 均价 85.08 · 现价 85.08 · 市值 850.80 · 盈亏 0.00 · 「交易→」入口）；更新于 15:05:52 |
| `34-a9-trades-375.png` | `/trades` 流水 375px | 表格转卡片，逐笔带时间/方向/数量/成交价/金额/交易后余额；最新一笔 2026/11/7 14:17:11 m0NESY 买入 ×10 @85.08 → 4149.20，与后端 8 条流水一致；更新于 15:06:06 |
| `35-a9-scrollwidth-375.png` | 375px 横向溢出**硬断言** | DevTools（iPhone SE 375×667）Console 执行 `document.documentElement.scrollWidth + ' / ' + window.innerWidth` → **`'375 / 375'`**：两数相等 ⇒ 文档宽度未超出视口，**无横向滚动**（2026-11-07 17:09 实测，页面同屏可见） |

> **数字口径**：余额 4149.20 / 持仓 m0NESY ×10 / 流水 8 条 = 7.2 重新部署复验后的线上真实状态（总资产守恒 5000.00），演示时照这个念。
>
> **A-9 证据已闭合**：375px 五页实拍（30~34）+ **横向溢出硬断言（35，`375 / 375`）** + 键盘焦点（28）+ AI 占位态（29）。
> 原「仍缺一张」已划掉。

> 3.3 的复现步骤与口径说明见 `docs/presentation/evidence-3.3-guide.md`。
> 口径提示：pulse 是"近一月 + 全部分支"，本地是"全周期 + develop"，两列数字不必强行对齐；`Insights → Contributors` 只算默认分支 `main`（31 次、3 个账号），**不作为证据使用**。
