# -*- coding: utf-8 -*-
"""一次性脚本：抓 8 支战队的队标到 code/frontend/src/assets/teams（本地化，避免线上热链失效）。

三类来源，按可得性回退：
1. `commons`：Wikimedia Commons 上的自由文件，Special:FilePath/<file>?width=512（SVG 自动出 PNG）；
2. `wiki`：英文维基条目 infobox 的 `| logo =` 文件名。先经 api.wikimedia.org 取 wikitext 解析文件名，
   再按 MediaWiki 的 md5 哈希目录规则拼 upload.wikimedia.org/wikipedia/en/… 缩略图
   （缩略图宽度只允许固定档位：500 / 330 / 250），最后回落到原图（SVG 浏览器也能直接渲染）；
3. `direct`：已经确认好的直链（HLTV 的 CDN 签名地址，The MongolZ 在 Commons 没有自由队标）。

脚本幂等：目录里已经有 <slug>.* 就跳过；重抓前先删掉对应文件。
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "code" / "frontend" / "src" / "assets" / "teams"
UA = "PlayerStockDemo/0.1 (student project, local asset fetch)"
WIDTHS = (500, 330, 250)
RASTER = ("png", "jpg", "gif", "webp")

TEAMS: dict[str, list[tuple[str, str]]] = {
    "vitality": [("wiki", "Team Vitality")],
    "spirit": [("commons", "Team_Spirit_new_em.svg")],
    "falcons": [("wiki", "Team Falcons")],
    "faze": [("commons", "Faze_Clan.svg")],
    "g2": [("wiki", "G2 Esports")],
    "navi": [("commons", "NAVI-Logo.svg")],
    "astralis": [("commons", "Astralis_logo.svg")],
    "mongolz": [
        (
            "direct",
            "https://img-cdn.hltv.org/teamlogo/bRk2sh_tSTO6fq1GLhgcal.png"
            "?ixlib=java-2.1.0&w=100&s=1bd99148a19e1e706b543500206901d4",
        )
    ],
}


def fetch(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as err:  # noqa: BLE001
        print(f"            {type(err).__name__}: {err}  <- {url.split('wikimedia.org/')[-1][:70]}")
        return None


def kind(data: bytes) -> str:
    if data[:4] == b"\x89PNG":
        return "png"
    if data[:3] == b"\xff\xd8":
        return "jpg"
    if data[:4] == b"GIF8":
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:5] in (b"<svg ", b"<?xml") or b"<svg" in data[:400]:
        return "svg"
    if data[:1] == b"<":
        return "html-error"
    return "unknown"


def parts(name: str) -> tuple[str, str, str]:
    under = name.strip().replace(" ", "_")
    digest = hashlib.md5(under.encode("utf-8")).hexdigest()
    return under, digest[0], digest[:2]


def wikitext(page_title: str, project: str = "en") -> str:
    url = f"https://api.wikimedia.org/core/v1/wikipedia/{project}/page/" + urllib.parse.quote(
        page_title.replace(" ", "_")
    )
    blob = fetch(url)
    return json.loads(blob.decode("utf-8")).get("source", "") if blob else ""


def logo_names(source: str) -> list[str]:
    out: list[str] = []
    for raw in re.findall(r"^\s*\|\s*logo[a-z_ ]*\s*=\s*([^\n]+)", source, flags=re.M | re.I):
        raw = re.sub(r"\{\{([^{}]*)\}\}", r" \1 ", raw, flags=re.I)
        raw = re.sub(r"\[\[([^\]|]+).*?\]\]", r"\1", raw, flags=re.I)
        raw = raw.split("|")[0].strip()
        if re.search(r"\.(svg|png|jpe?g|gif|webp)$", raw, flags=re.I):
            out.append(raw)
    if not out:
        for cand in re.findall(r"(?:File:|Image:)\s*([^\]|}]+\.(?:svg|png|jpe?g|gif|webp))", source, flags=re.I):
            if re.search(r"logo|mark|emblem", cand, flags=re.I):
                out.append(cand.strip())
    return out


def urls_for(name: str, branch: str) -> list[str]:
    under, h1, h2 = parts(name)
    stem = urllib.parse.quote(under)
    base = f"https://upload.wikimedia.org/{branch}"
    out: list[str] = []
    svg = bool(re.search(r"\.svg$", under, flags=re.I))
    for width in WIDTHS:
        suffix = f"{width}px-{stem}.png" if svg else f"{width}px-{stem}"
        out.append(f"{base}/thumb/{h1}/{h2}/{stem}/{suffix}")
    if svg:
        out.append(f"{base}/thumb/{h1}/{h2}/{stem}/{stem}.png")
    out.append(f"{base}/{h1}/{h2}/{stem}")  # 原图
    return out


def save(slug: str, blob: bytes | None, note: str) -> bool:
    if not blob:
        return False
    got = kind(blob)
    if got not in RASTER + ("svg",) or len(blob) < 1000:
        print(f"{slug:<9}   miss: {got} {len(blob)} B  {note}")
        return False
    for stale in OUT.glob(f"{slug}.*"):
        stale.unlink()
    (OUT / f"{slug}.{got}").write_bytes(blob)
    print(f"{slug:<9} saved {slug}.{got} {len(blob)} B  {note}")
    return True


def candidate_urls(how: str, value: str) -> list[tuple[str, str]]:
    """返回 (说明, url) 列表。"""
    if how == "direct":
        return [("direct", value)]
    if how == "commons":
        return [
            ("commons Special:FilePath", f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(value)}?width=500")
        ] + [("commons hashed", u) for u in urls_for(value, "wikipedia/commons")]
    source = wikitext(value)
    names = logo_names(source)
    print(f"          infobox logo = {names}")
    return [(f"en-wiki {n}", u) for n in names for u in urls_for(n, "wikipedia/en")]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, sources in TEAMS.items():
        if list(OUT.glob(f"{slug}.*")):
            print(f"{slug:<9} already present, skip")
            continue
        done = False
        for how, value in sources:
            try:
                for note, url in candidate_urls(how, value):
                    if save(slug, fetch(url), note):
                        done = True
                        break
            except Exception as err:  # noqa: BLE001
                print(f"{slug:<9} ERROR {type(err).__name__}: {err}")
            if done:
                break
        if not done:
            print(f"{slug:<9} FAILED")


if __name__ == "__main__":
    main()
