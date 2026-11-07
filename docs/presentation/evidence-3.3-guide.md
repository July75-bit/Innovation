# 3.3 提交次数截图：怎么做（照这份点）

> **要求原文**：3.3「代码仓库链接及代码提交历史截图，**包括每个人提交的次数截图**，参考 `https://github.com/[accountname]/[reponame]/pulse`」
> **负责**：D（截图与说明）· A/B/C（各自确认自己的 GitHub 账号邮箱，见 §4）
> **已有产物**：`docs/acceptance/evidence/20-commit-stats.png`（真实提交统计，本地 git 可复跑）

## 0. 先说一个必须知道的坑

我们仓库的**默认分支是 `main`，只有 31 次提交**；真正的开发全在 `develop`（**137 次**）。而 GitHub 的 pulse / contributors 只统计**默认分支**，并且只按**已绑定到 GitHub 账号的邮箱**归因。

实测结果（2026-11-07）：

```
GitHub contributors API（只看 main）：wlkaqw 18 · weedflame 8 · July75-bit 5   = 31
本地 git（develop，非合并提交）：   D 50 · B 38 · C 26 · A 20 · 仓库账号 3      = 137
```

也就是说：**只截 pulse 会漏掉 B 和 C，而且数字是全仓的 1/4**。答辩时被问「B 怎么只有 0 次提交」会很尴尬。

所以证据要**三层**：pulse 原始记录 + 每人 commits 页 + 一张准数统计图。

## 1. 截图一：pulse（平台原始脉搏图）

1. 浏览器打开 `https://github.com/July75-bit/Innovation/pulse`
2. 页面右上角有期间选择，选 **`1 month`**（默认可能是 1 week，会太短）
3. 往下滚到 **`Authors`** 区块——这里就是"每个人提交次数"的原始图
4. 截图要求：
   - **连地址栏一起截**（证明是本仓库），窗口宽度 ≥ 1280
   - 让 `Authors` 那一整块完整入镜，不要截半个
   - 存为 `docs/acceptance/evidence/21-pulse.png`

> 如果页面上有 **Branch 下拉**，切到 `develop` 再截；切不了就按原样截，并在 PPT 里注明"pulse 统计默认分支 main"。

## 2. 截图二：每个人的提交列表（补上 pulse 漏掉的人）

按账号过滤 `develop` 的提交，URL 模板：

```
https://github.com/July75-bit/Innovation/commits/develop?author=<GitHub 登录名>
```

已知能用的两个：

| 人 | URL | 预期看到 |
| --- | --- | --- |
| A 倪颢容 | `.../commits/develop?author=weedflame` | 20 条 |
| D 王泽棠 | `.../commits/develop?author=wlkaqw` | 50 条 |

B（Hu De Hao）和 C（fusde0）**现在没有绑定账号**，过滤不出来。他们的提交在
`https://github.com/July75-bit/Innovation/commits/develop` 里作者显示为**灰色默认头像 + 名字**
——这一张反而要截下来，它是"归因缺失"的客观证据。

截图命名：`22-commits-A.png` / `22-commits-D.png` / `22-commits-unlinked.png`，同样连地址栏。

## 3. 截图三：准数统计图（已生成）

`docs/acceptance/evidence/20-commit-stats.png` —— 直接从 `develop` 算的准数：

| 成员 | git 身份 | 提交 | + 行 | − 行 | 占比 |
| --- | --- | ---: | ---: | ---: | ---: |
| D 王泽棠 | `wlkaqw` | 50 | +17,357 | −1,824 | 36.5% |
| B 胡德昊 | `Hu De Hao` | 38 | +5,989 | −892 | 27.7% |
| C 刘宏 | `fusde0` | 26 | +1,927 | −333 | 19.0% |
| A 倪颢容 | `weedflame` | 20 | +10,797 | −1,207 | 14.6% |
| 仓库账号 | `July75-bit` | 3 | +2 | −1 | 2.2% |
| **合计** | — | **137** | **+36,072** | **−4,257** | 100% |

复跑命令（任何人可验）：

```powershell
cd D:\projects\innovation\Innovation
git shortlog -sn --no-merges develop
git log --numstat --no-merges --author="Hu De Hao" develop
```

> 这张图的价值：pulse 是"平台怎么看我们的仓库"，这张是"仓库真实发生了什么"。两者一起交，才既满足要求又不失实。

## 4. 让以后的提交被正确归因（每人 2 分钟，只影响新提交）

**为什么要改**：提交里记的是 `user.email`，GitHub 用它把提交算到某个账号头上。没绑定的邮箱 → 这个人在 pulse / contributors 上直接消失（我们已经有 2 个人属于这种情况）。

每人在**自己电脑的仓库目录**执行（把邮箱换成自己 GitHub 账号的主邮箱）：

```powershell
cd D:\projects\innovation\Innovation
git config user.name  "你的名字"
git config user.email "你的GitHub邮箱"
git config --get user.email        # 回显确认
```

不知道用哪个邮箱：打开 `https://github.com/settings/emails`，用里面**已验证（Verified）**的那个。
不想暴露真实邮箱，用 GitHub 提供的 noreply 地址也行（在同一个页面能看到，形如 `12345678+login@users.noreply.github.com`）。

**注意**：

- 这个改动**不会**追溯修改历史提交（历史提交的作者邮箱是写死在 commit 里的，改不了，除非重写历史——我们不做）；
- 所以"旧提交归因缺失"是既定事实，答辩时按 §3 的方式说明即可，不要试图掩盖；
- 改完之后每个人的**新**提交才会被 pulse 正确统计。

## 5. 交付清单（做完打勾）

- [ ] `21-pulse.png`：pulse 页，期间 1 month，含 Authors 区块与地址栏
- [ ] `22-commits-A.png` / `22-commits-D.png`：按账号过滤的 develop 提交列表
- [ ] `22-commits-unlinked.png`：develop 提交列表里 B/C 的灰色头像（归因缺失证据）
- [ ] `20-commit-stats.png`：已生成，无需再截
- [ ] `docs/acceptance/evidence/README.md` 索引补这 4 行
- [ ] 每人执行完 §4 并把 `git config --get user.email` 的回显发群里
