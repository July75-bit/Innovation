# 答辩幻灯片

> **负责人**：全员（D 汇总） ｜ **截止**：第 6 天 ｜ **状态**：✅ 材料齐（Slidev 答辩稿已迁到 [docs/slides](../slides/)，20 页、Mermaid 架构/ER 图、逐页讲稿，GitHub Actions 自动构建 PDF；本目录保留演示脚本/问答/彩排手册与旧版 PDF）；待**全员彩排**
> **评分占比**：答辩评分表 —— 介绍幻灯片 **40%** + 功能演示 **40%** + 回答问题 **20%**

## 文件清单（已产出）

| 文件 | 内容 | 负责人 | 状态 |
| --- | --- | --- | --- |
| [`../slides/`](../slides/) | **Slidev 答辩稿（20 页源稿 slides.md + style.css + assets + package.json）**；GitHub Actions 自动构建 PDF/静态站 | D | ✅ |
| [`defense.pdf`](defense.pdf) | 旧版 PDF（16 页，上一版 HTML 流程产物；新版请用 Slidev 导出） | D | 历史 |
| [`defense.html`](defense.html) | 旧版 HTML 源文件（历史；本次答辩主材料为 Slidev） | D | 历史 |
| [`build_deck.py`](build_deck.py) | 旧版 `defense.html` 的生成脚本（历史） | D | 历史 |
| [`demo-script.md`](demo-script.md) | 2 分钟现场演示脚本（逐秒操作 + 话术 + 失败预案） | D / A 执行 | ✅ |
| [`qa.md`](qa.md) | 5 分钟问答：按幻灯片逐页准备（P01–P19，72 问）+ 详答版（28 问，七类，含 Q11.b） | D 汇总 / 全员认领 | ✅ |
| [`code_map.md`](code_map.md) | 代码对照表：功能 → 文件 → 函数 → 行号 → 对应测试（被问代码时查） | D | ✅ |
| [`pricing_slides.pptx`](pricing_slides.pptx) | 定价模块 **3 页素材**（公式推导 / 参数理由 / 100 seed 稳定性与下行风险），每页含口播备注，可直接拷进主稿；文字数据与 `docs/algorithm/pricing_model.md` §2/§3/§7/§8 一致 | C | ✅ |

**放映 / 导出**：Slidev 源稿与构建说明见 [../slides/README.md](../slides/README.md)；本机放映需要 Node.js 22.22+，或直接用 GitHub Actions 的 artifact。

> 课程允许直接用 Slidev 写幻灯片、用 Mermaid 画图；本稿架构图与 ER 图都是 Mermaid 代码块，改数据直接改 markdown。
> 旧的 defense.pdf / defense.html 是上一版 HTML 流程产物，不作为本次答辩主材料。

## GitHub Actions 自动构建 + 在线发布（推荐）

推送 [docs/slides](../slides/) 的改动会自动触发 [.github/workflows/slides.yml](../../.github/workflows/slides.yml)，
构建后发布到 GitHub Pages：**幻灯片在线看 <https://july75-bit.github.io/Innovation/>**，
**PDF 直接查看/下载 <https://july75-bit.github.io/Innovation/playerstock_defense.pdf>**。

流水线：
npm ci → Playwright Chromium + 中文字体 → slidev build → slidev export → 发布 GitHub Pages（在线放映 + PDF），另上传 PDF 备份 artifact **playerstock-defense-pdf**（保留 30 天）。

**下载**：GitHub 仓库 → Actions → 左侧「答辩幻灯片 (Slidev)」→ 最近一次绿色 run → 底部 Artifacts → 下载 `playerstock-defense-pdf`，解压得到 20 页 PDF；在线放映直接用上面的 Pages 地址。
也可在 Actions 页面点 **Run workflow** 手动触发。

## 彩排记录（待填）

> 两次彩排后把实际时长与改动填在这里（M6 关闭条件）；每页讲稿时长预估见 [`rehearsal-plan.md`](rehearsal-plan.md) §二·补。

| 彩排 | 日期 / 时间 | 总时长 | 超时页 / 问题 | 改了什么 |
| --- | --- | ---: | --- | --- |
| 第 1 次 | （待填） | | | |
| 第 2 次 | （待填） | | | |
