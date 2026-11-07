# 重新部署后数据仍在（7.2 · 人证 + 对账）

> 执行人：项目负责人在 Render 控制台 Manual Deploy ｜ 对账与记录：B ｜ 日期：2026-11-07
> 服务：`https://playerstock-backend-mdlk.onrender.com`（Render Postgres 18）
> 结论一句话：**部署前那 7 条流水逐行原样保留、11 个价格点逐点一致；期间新增 1 笔成交，余额变化与它完全吻合 → 数据没丢，而且部署后还能写。**

## 1. 时间线

| 时刻（本机 UTC+8） | 事件 | 证据 |
| --- | --- | --- |
| 14:15:01 / 14:15:20 / 14:15:43 | 部署前快照：account / trades / prices | `online-persistence-before-{1,2,3}-*.png` |
| 14:17 左右 | Manual Deploy（Deploy latest commit），服务转 Live | Render 控制台 |
| 之间 | **新增 1 笔成交**：m0NESY BUY ×10 @ 85.08 = 850.80（A 走查/彩排触发，属正常） | 见下面「新增成交明细」 |
| 14:19:57 / 14:20:12 / 14:20:32 | 部署后快照：account / trades / prices | `online-persistence-after-{1,2,3}-*.png` |
| 14:22:46 | 脚本二次采集用于逐项对账 | `.tmp/persist-after.json`（本机，不提交） |

## 2. 六张截图

| 阶段 | account | trades | prices |
| --- | --- | --- | --- |
| 部署前 | [before-1](../online/online-persistence-before-1-account.png) 余额 5000.0 / 总资产 5000.0 | [before-2](../online/online-persistence-before-2-trades.png) **7 条** | [before-3](../online/online-persistence-before-3-prices.png) **11 点**，末点 108.75 |
| 部署后 | [after-1](../online/online-persistence-after-1-account.png) 余额 4149.2 / 持仓市值 850.8 / 总资产 5000.0 | [after-2](../online/online-persistence-after-2-trades.png) **8 条**（新增 #8） | [after-3](../online/online-persistence-after-3-prices.png) **11 点**，末点 108.75 |

## 3. 逐项对账（`scripts/persistence_check.py --diff` 原样输出）

```text
| 检查点 | 部署前 | 部署后 | 结论 |
| --- | --- | --- | --- |
| 价格历史（逐点 ts+price） | 11 点 | 11 点 | ✅ 逐点一致 |
| 部署前已有的流水是否原样保留 | 7 条 | 缺失 0 条 / 被改 0 条 | ✅ 逐行一致 |
| 部署后新增成交 | — | 1 笔（id [8]） | ✅ 服务可写 |
| 余额变化能否被新增成交解释 | 5000.0 | 4149.2（Δ -850.80） | ✅ 与新增净额 -850.80 吻合 |
| 总资产（价格未变时应守恒） | 5000.0 | 5000.0 | ✅ 守恒 |
| 选手数 | 8 | 8 | ✅ 一致 |
```

**新增成交明细**

| id | 选手 | 方向 | 数量 | 价格 | 金额 | 事后余额 |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | m0NESY | BUY | 10 | 85.08 | 850.80 | 4149.2 |

## 4. 为什么"余额变了"不等于"数据丢了"

不少人看到前后余额不同会以为数据没保住，这里做个算术闭合：

```
部署前余额 5000.00
  − 新增买入 850.80（m0NESY ×10 @85.08）
  = 4149.20  ← 与部署后余额完全一致
持仓市值 0.00 → 850.80（就是这 10 股按 85.08 计价）
总资产   5000.00 → 5000.00（守恒，没多也没少）
价格历史 11 点，逐点 (ts, price) 完全相同（历史没被重建）
部署前 7 条流水：一条不少、一条没改（id 1–7 逐行相同）
```

所以这次验证比"数字完全不变"**更强**：既证明旧数据活着，也证明部署后仍能正常写入。

## 5. 复跑方法（任何人可验证）

```powershell
# 部署前
python scripts/persistence_check.py --label before --out .tmp/persist-before.json
# Render → Manual Deploy → 等 Live
# 部署后
python scripts/persistence_check.py --label after  --out .tmp/persist-after.json
# 对账（不一致时退出码 1）
python scripts/persistence_check.py --diff .tmp/persist-before.json .tmp/persist-after.json
```

> ⚠️ 两个快照之间**不要**跑 `bootstrap_demo_data.py --reset`，那会把数据重置、证明不了"数据还在"；
> 部署那几十秒里接口 5xx 属正常，脚本自带 5 次重试，不会把冷启动误判成丢数据。

## 6. 与其它证据的关系

| 证据 | 证明什么 |
| --- | --- |
| 本文（截图 + 对账脚本） | **部署前后数据一致 + 部署后仍可写**（人证） |
| `backend-debug-db.md` §1（`/api/debug/db`） | 线上方言是 `postgresql`、`是否 SQLite: false`、5 张表与行数（机证） |
| `test_report.md` §6 TC-404 | 验收条目与结论 |
| `deployment.md` §5 / §9 | 检查单与 TODO 的勾选状态 |
