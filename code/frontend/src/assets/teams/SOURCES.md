# 队标图片来源（SOURCES）

这些图片是**离线拷贝进仓库**的站队标，不是热链：断网、内网答辩、CI 构建都不会出现破图。
抓取脚本：仓库根目录 `scripts/fetch_team_logos.py`（幂等，删掉对应文件即可重抓）。

| 文件 | 队伍（赛程里的名字） | 来源 | 授权口径 |
| --- | --- | --- | --- |
| `vitality.png` | Vitality | 英文维基百科条目 `Team Vitality` 的 infobox 图 `File:Team Vitality logo.svg`（`upload.wikimedia.org/wikipedia/en/…/500px-…svg.png`） | 非自由作品（fair use），仅作课程演示的标识性引用 |
| `spirit.png` | Spirit | Wikimedia Commons `File:Team_Spirit_new_em.svg` | 自由许可（见 Commons 文件页） |
| `falcons.png` | Falcons | 英文维基百科条目 `Team Falcons` 的 `File:Team Falcons Logo.svg`（500px 渲染图） | 非自由作品（fair use） |
| `faze.png` | FaZe Clan | Wikimedia Commons `File:Faze_Clan.svg` | 自由许可 |
| `g2.png` | G2 | 英文维基百科条目 `G2 Esports` 的 `File:Esports organization G2 Esports logo.svg`（500px 渲染图） | 非自由作品（fair use） |
| `navi.png` | NAVI | Wikimedia Commons `File:NAVI-Logo.svg` | 自由许可 |
| `astralis.png` | Astralis | Wikimedia Commons `File:Astralis_logo.svg` | 自由许可 |
| `mongolz.png` | The MongolZ | HLTV.org 战队页 `team/6248/the-mongolz` 的队标 CDN 地址 `img-cdn.hltv.org/teamlogo/…png` | 站点标识，仅作演示引用；Commons / Wikidata 上暂无自由版本 |

用途限制：仅用于本课程设计项目（`demo-2026` 演示赛季）的界面展示，队标版权归各俱乐部所有，
不构成任何官方合作或背书；对外发布/商用前需替换为自绘标识或取得授权。

界面处理：站队标里有纯黑 / 纯白图形（Vitality、Spirit、G2），深色主题下会糊成一片，
所以 `TeamLogo.vue` 给每块队标垫了浅色底板，并把图片按 `object-fit: contain` 居中缩放。
