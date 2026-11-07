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

## 汇报证据（3.6 / 3.7 / 3.3）

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `18-quality-pylint-pep8.png` | Pylint 语义分析 + PEP8 + 格式化体检 | Pylint 9.74/10（无 E/F 级）；`ruff check --select E,W` 25 项全为 E501；`ruff format --check` 31 待格式化 / 39 已格式化 |
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
| `pulse-committers.csv` | GitHub Pulse → Top committers 原始导出（2026-11-07） | wlkaqw 49 / July75-bit 41 / fusde0 28 / weedflame 21 = **139**；比 22 号截图时多 1 条（weedflame 20→21），统计窗口滚动，正常 |

## A-9 亲手走查（第 6 天，2026-11-07 14:37–15:06）

> 背景：A-1/A-2/A-3 的代码由 D 代写，`23~29` 归档后 A 逐页做了最终确认。这组是 **A 本人**在
> 线上 `playerstock-frontend-mdlk.onrender.com` 以 iPhone SE（375×667）走查的实拍（`day6.md` §7.1 委派单落地）。

| 文件 | 内容 | 关键断言 |
| --- | --- | --- |
| `30-a9-market-375.png` | `/` 市场页 375px | 顶栏折成「PlayerStock · 余额 · 菜单」一行；表格转**卡片**（ZywOo 108.75 −13.88% 等）；搜索 / 筛选（全部/交易中/暂停）/ 排序收起可用；更新于 14:37:26；容器均在 375 内、无横向溢出 |
| `31-a9-detail-375.png` | `/players/1` 详情 375px | 标题/战队/状态/表现分/价格**上下排**；「最近变动：本场表现下滑（本轮得分 81.3，S=-0.92），价格下跌 13.88%」直出后端 reason；折线图整宽；「查看价格变动明细（11）」与线上 11 点一致 |
| `32-a9-nav-drawer-375.png` | 375px 导航抽屉展开 | 点「菜单」→ 抽屉：市场/持仓/交易记录 + 余额 4149.20 / 总资产 5000.00 / 总收益 +0.00 +「连接成功: playerstock-backend」；底部合规声明完整；「关闭菜单」可退出 |
| `33-a9-positions-375.png` | `/positions` 持仓 375px | 四指标卡两列；持仓行转卡片（m0NESY 10 股 · 均价 85.08 · 现价 85.08 · 市值 850.80 · 盈亏 0.00 · 「交易→」入口）；更新于 15:05:52 |
| `34-a9-trades-375.png` | `/trades` 流水 375px | 表格转卡片，逐笔带时间/方向/数量/成交价/金额/交易后余额；最新一笔 2026/11/7 14:17:11 m0NESY 买入 ×10 @85.08 → 4149.20，与后端 8 条流水一致；更新于 15:06:06 |

> **数字口径**：余额 4149.20 / 持仓 m0NESY ×10 / 流水 8 条 = 7.2 重新部署复验后的线上真实状态（总资产守恒 5000.00），演示时照这个念。
>
> **仍缺一张**（答辩前建议补上）：`document.documentElement.scrollWidth + ' / ' + window.innerWidth` 的
> console 断言未截进 375px 图里——页面肉眼无横向溢出，但委派单要求这条"硬断言"随图入证。
> ~~AI「分析中…」占位态~~ **已补齐**（`29-ai-loading.png`，见上表）。

> 3.3 的复现步骤与口径说明见 `docs/presentation/evidence-3.3-guide.md`。
> 口径提示：pulse 是"近一月 + 全部分支"，本地是"全周期 + develop"，两列数字不必强行对齐；`Insights → Contributors` 只算默认分支 `main`（31 次、3 个账号），**不作为证据使用**。
