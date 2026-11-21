# Slidev 结课审查幻灯片

PlayerStock 结课项目审查用的 Slidev 项目：17 页 16:9 幻灯片，覆盖课程 wiki「项目汇报内容」1.1–3.7，
架构/ER 图用 Mermaid，逐页讲稿写在 markdown 注释里（放映时按 `P` 查看演讲者模式）。

> 版式：每页标题先出现，正文按讲解顺序逐块点击出现；两栏版面左右起点对齐、正文垂直居中。

> 构建、导出与发布**全部交给 GitHub Actions**（见 [`.github/workflows/slides.yml`](../../.github/workflows/slides.yml)），
> 本机不装 Node / Slidev / Playwright 也能拿到在线网页和 PDF。

> **放映方式**：空格 / → 逐条展开（v-click 渐进披露），P 开演讲者模式；PDF 导出会一次性显示全部内容。
> **讲稿在哪**：每页的 HTML 注释（按 P 在演讲者模式查看）；纯文本版在 [notes.md](notes.md)。

## 在线访问（push 后自动发布）

| 内容 | 地址 |
| --- | --- |
| 幻灯片网页 | <https://july75-bit.github.io/Innovation/> |
| PDF 直接查看/下载 | <https://july75-bit.github.io/Innovation/playerstock_defense.pdf> |

工作流：修改 `docs/slides/` 并 push → Actions 自动构建 → 部署到 **GitHub Pages**；
封面上的「📄 下载完整材料 PDF」按钮指向站点里的 PDF，浏览器打开后右上角可直接下载。

> **首次需要启用 Pages（仓库 owner 操作一次）**：GitHub 仓库 → **Settings** → **Pages** →
> **Build and deployment** → **Source** 选 **GitHub Actions**。
> 工作流里已带 `actions/configure-pages@v5` 的 `enablement: true`，有仓库管理权限时会自动启用；
> 没有权限时会报错，让 owner 按上面路径手动点一下即可。

## 文件

| 文件 | 用途 |
| --- | --- |
| [`slides.md`](slides.md) | **源稿**：17 页 Markdown（含 frontmatter、Mermaid、讲稿注释） |
| [`style.css`](style.css) | 全局样式（暖纸色、卡片、表格、代码块） |
| [`assets/`](assets/) | 幻灯片引用的产品截图（市场浅/深、详情、移动端） |
| [`package.json`](package.json) | `dev` / `build` / `export` 脚本与依赖版本 |
| [`package-lock.json`](package-lock.json) | 锁定 `@slidev/cli 53.1.0` / `@slidev/theme-default` / `playwright-chromium` |

| [`notes.md`](notes.md) | 逐页讲稿的纯文本版（与 slides.md 注释同步） |

## GitHub Actions 流水线

1. `npm ci` → 安装 Playwright Chromium → 安装中文字体（`fonts-noto-cjk`）
2. `slidev build --base /${repo}/` 生成静态站 `dist/`
3. `slidev export` 导出 `playerstock_defense.pdf`，并复制进 `dist/`
4. `actions/upload-pages-artifact` + `actions/deploy-pages` 发布到 GitHub Pages
5. 另外上传 `playerstock-defense-pdf` artifact（PDF 备份，保留 30 天）

> 如果只想拿 PDF、不等 Pages：Actions → **答辩幻灯片 (Slidev)** → 最新 run → **Artifacts**；
> Pages 发布成功后，run 页面也会显示站点地址。

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
