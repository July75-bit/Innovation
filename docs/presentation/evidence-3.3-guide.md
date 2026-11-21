# 3.3 提交次数截图：怎么做（已跑通，照这份点）

> **要求原文**：3.3「代码仓库链接及代码提交历史截图，**包括每个人提交的次数截图**，参考 `https://github.com/[accountname]/[reponame]/pulse`」
> **状态**：2026-11-07 已实际截图并入库（`21-pulse-overview.png`、`22-pulse-top-committers.png`），本文是复现步骤与口径说明。

## 0. 结论先行（并更正一处误判）

实际截图后确认：**pulse 的 `Top committers` 是「全部分支」统计，4 个人都在**，不存在"某人消失"的问题。

| 来源 | 看到的东西 |
| --- | --- |
| `Pulse → Top committers`（全部分支，近 1 月） | wlkaqw 49 · July75-bit 41 · fusde0 28 · weedflame 20 = **138** |
| `Insights → Contributors`（图表，只算默认分支 main） | 只有 3 个账号、合计 31 —— **这张不要用** |
| 本地 git（develop，全周期，排除合并） | D 50 · B 38 · C 26 · A 20 + 仓库账号 3 = **137** |

> 早期判断"B 的 38 次提交在 pulse 上会消失"来自 `Contributors` 接口（默认分支口径），**与 pulse 实际表现不符，已更正**。答辩只用 `Pulse`。

## 1. 截图步骤（两张就够）

### 1.1 总览图

1. 打开 `https://github.com/July75-bit/Innovation/pulse`
2. 右上角 `Period` 选 **`1 month`**（默认 1 week 太短）
3. 确认 `Summary` 出现「**4 authors** have pushed … **138 commits to all branches**」
4. 连地址栏一起截 → 存 `docs/acceptance/evidence/21-pulse-overview.png`

### 1.2 每人提交次数（关键的一张）

1. 在同一个页面，看 `Top committers` 卡片（右上角有三个点 / 展开按钮）
2. 点开后是一个弹窗，**每人一行、带具体数字**，还带 `Download CSV`
3. 把弹窗整块截进去 → 存 `docs/acceptance/evidence/22-pulse-top-committers.png`
4. 顺手点 **`Download CSV`**，把 CSV 也存到 `docs/acceptance/evidence/pulse-committers.csv`（比截图更硬的证据）

> 截图规范：窗口 ≥1280 宽、**不要裁掉地址栏**、日期区间（October 6 – November 6）要入镜。

## 2. 必须补一张对照表：pulse 显示的是账号名，不是真名

pulse 的 `July75-bit` 会让评委以为是"仓库所有者单独提交了 41 次"，其实是 **B 的提交**（该账号绑定的是 B 的邮箱 1975473007@qq.com，41 = B 的 38 条 + 该账号自身 3 条）。**账号归属已由 B 本人（胡德昊）于 2026-11-07 确认。**

| git 提交里的名字 | GitHub 账号（pulse 显示） | 真人 | 全周期提交 |
| --- | --- | --- | ---: |
| `wlkaqw` | wlkaqw | D 王泽棠 | 50 |
| `Hu De Hao` | **July75-bit**（含该账号自身 3 条） | B 胡德昊 | 38（+3） |
| `fusde0` | fusde0 | C 刘宏 | 26 |
| `weedflame` | weedflame | A 倪颢容 | 20 |

> 这张表已经画进 `20-commit-stats.png`，回答"账号 → 真人"的问题时直接放这张图。

## 3. 口径差异怎么说（评委一定会问）

| 对比项 | pulse 近 1 月 | 本地全周期 |
| --- | --- | --- |
| 时间窗 | 2026-10-06 → 11-06（当月） | 2026-10-17 → 11-07（项目全周期） |
| 分支 | 全部分支 | develop |
| 合并提交 | 排除 | 排除 |
| 数字 | 138 | 137 |

**一句话答法**：「pulse 是 GitHub 按月给的口径，我们是 6 天冲刺、全周期在 develop 上；两张图口径不同所以数字不完全一样，差 1 条是 11-07 当天的提交还没进 pulse 的窗口。」

另外 pulse 里写着 `On main, 0 files have changed / 0 additions / 0 deletions` —— 别慌，这是**对的**：
我们 `main` 是发布分支，只接受从 `develop` 合并（PR #3），没有直接提交；所有开发都在 `develop`。

## 4. 让归因以后更清楚（可选，2 分钟/人）

```powershell
cd D:\projects\innovation\Innovation
git config user.name  "你的名字"
git config user.email "你的GitHub邮箱"   # 用 https://github.com/settings/emails 里已验证的那个
git config --get user.email            # 回显确认
```

- 只影响**以后**的提交；历史提交的作者邮箱写死在 commit 里，改不了（也不该为它重写历史）。
- 我们现在的实际情况并不难看：4 个人在 pulse 上都有数字，只是账号名需要一次对照。

## 5. 交付清单

- [x] `21-pulse-overview.png`：pulse 总览，1 month，含 `4 authors / 138 commits to all branches`
- [x] `22-pulse-top-committers.png`：Top committers 弹窗，每人具体次数
- [x] `20-commit-stats.png`：本地准数 + 账号对照 + 双口径说明
- [x] `pulse-committers.csv`：已导出入库（2026-11-07：49 / 41 / 28 / 21 = 139，比截图时多 1 条属窗口滚动，正常）
- [x] `docs/acceptance/evidence/README.md` 索引补这 4 行
- [x] 确认 §2 对照表里"账号 → 真人"的映射无误：**July75-bit = B 胡德昊（本人已确认，2026-11-07）**
