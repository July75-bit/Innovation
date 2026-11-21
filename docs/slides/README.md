# Slidev 答辩幻灯片

PlayerStock 答辩用的 Slidev 项目：17 页 16:9 幻灯片，覆盖课程 wiki「项目汇报内容」1.1–3.7，
架构/ER 图用 Mermaid，逐页讲稿写在 markdown 注释里（放映时按 `P` 查看演讲者模式）。

> 构建与导出**全部交给 GitHub Actions**（见 [`.github/workflows/slides.yml`](../../.github/workflows/slides.yml)），
> 本机只需要能打开网页；不装 Node / Slidev / Playwright 也能拿到 PDF。

## 文件

| 文件 | 用途 |
| --- | --- |
| [`slides.md`](slides.md) | **源稿**：17 页 Markdown（含 frontmatter、Mermaid、讲稿注释） |
| [`style.css`](style.css) | 全局样式（暖纸色、卡片、表格、代码块） |
| [`assets/`](assets/) | 幻灯片引用的产品截图（市场浅/深、详情、移动端） |
| [`package.json`](package.json) | `dev` / `build` / `export` 脚本与依赖版本 |
| [`package-lock.json`](package-lock.json) | 锁定 `@slidev/cli 53.1.0` / `@slidev/theme-default` / `playwright-chromium` |

## GitHub Actions（推荐，零本机依赖）

1. 修改 `docs/slides/` 下的文件并 push（或 GitHub Actions 页面点 **Run workflow** 手动触发）
2. 打开仓库 **Actions** → 左侧 **答辩幻灯片 (Slidev)** → 最近一次绿色 run
3. 页面底部 **Artifacts** → 下载 **`playerstock-defense-slides`**（保留 30 天）
4. 解压得到：
   - `playerstock_defense.pdf` —— 投屏 / 提交用（17 页）
   - `dist/` —— 静态站，双击 `index.html` 可离线放映（← → 翻页，`P` 演讲者模式）

流水线做的事：`npm ci` → 安装 Playwright Chromium → `slidev build` → `slidev export` → 校验产物 → 上传 artifact。

## 本地预览（可选）

需要 Node.js ≥ 22.22 与网络：

```bash
cd docs/slides
npm ci                                  # 首次
npm run dev                             # 浏览器放映（改 markdown 热更新）
npm run build                           # 生成静态站 dist/
npm run export                          # 导出 playerstock_defense.pdf
```

> 本地生成的 `node_modules/`、`dist/`、`playerstock_defense.pdf` 已被 `.gitignore` 忽略，不要提交。
