# -*- coding: utf-8 -*-
"""生成 PlayerStock 答辩 HTML（单文件、离线、可键盘放映、可打印为 PDF）。

依据：课程 PDF 第 6 天（8′ 介绍 + 2′ 演示 + 5′ 问答）与课程 wiki「项目汇报内容」1.1–3.7。

用法：
    python docs/presentation/build_defense_html.py
输出：
    docs/presentation/playerstock_defense.html
"""
from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "presentation" / "assets"
OUT = ROOT / "docs" / "presentation" / "playerstock_defense.html"


def b64(name: str) -> str:
    return base64.b64encode((ASSETS / name).read_bytes()).decode("ascii")


IMG = {
    "market_light": b64("market-light.png"),
    "market_dark": b64("market-dark.png"),
    "detail": b64("detail-light.png"),
    "mobile": b64("market-mobile.png"),
}

CSS = r"""
:root {
  --paper: #f6f4ef; --card: #fcfbf8; --ink: #221f1b; --muted: #6b665c;
  --faint: #9a9487; --border: #e3ded4; --accent: #a62b2f; --sage: #2e6b4f;
  --dark: #141310; --paper-on-dark: #f3efe6; --muted-on-dark: #b8b2a4;
}
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; height: 100%; background: #0d0c0a; color: #f3efe6;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif; }
.stage { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.deck { width: 1280px; height: 720px; position: relative; transform-origin: center center; flex: none; }
.slide { position: absolute; inset: 0; padding: 48px 64px 58px; display: flex; flex-direction: column;
  background: var(--paper); color: var(--ink); opacity: 0; pointer-events: none;
  transition: opacity .18s ease; overflow: hidden; }
.slide.active { opacity: 1; pointer-events: auto; z-index: 2; }
.slide.dark { background: var(--dark); color: var(--paper-on-dark); }
.kicker { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 700;
  letter-spacing: .04em; color: var(--accent); }
.kicker::before { content: ""; width: 26px; height: 4px; background: var(--accent); border-radius: 2px; }
.slide.dark .kicker { color: #e08a86; }
.slide.dark .kicker::before { background: #e08a86; }
.title { margin: 10px 0 18px; font-size: 34px; line-height: 1.15; font-weight: 800; letter-spacing: -.01em; }
.page-no { position: absolute; right: 46px; top: 36px; font-size: 12px; color: var(--faint); }
.slide.dark .page-no { color: #8c8678; }
.body { display: flex; flex-direction: column; gap: 14px; flex: 1; min-height: 0; }
.footer { margin-top: auto; display: flex; justify-content: space-between; gap: 20px; padding-top: 10px;
  border-top: 1px solid var(--border); font-size: 11px; color: var(--faint); }
.slide.dark .footer { border-top-color: #35322b; color: #8c8678; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 15px 18px; }
.slide.dark .card { background: #1e1c18; border-color: #35322b; }
.label { font-size: 12px; font-weight: 700; color: var(--accent); margin-bottom: 6px; }
.slide.dark .label { color: #e08a86; }
.muted { color: var(--muted); } .faint { color: var(--faint); } .sage { color: var(--sage); }
p { margin: 0; font-size: 14px; line-height: 1.55; }
.small { font-size: 12px; line-height: 1.5; }
.tiny { font-size: 10.5px; line-height: 1.45; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.grid4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: stretch; }
.quote { background: var(--dark); color: var(--paper-on-dark); border-radius: 10px; padding: 20px 24px; font-size: 17px; font-weight: 600; line-height: 1.6; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px;
  background: #eee8dc; color: var(--ink); font-size: 12px; font-weight: 600; }
.pill.accent { background: var(--accent); color: #fff; }
.slide.dark .pill { background: #2a2722; color: var(--paper-on-dark); }
.cover-brand { display: flex; align-items: center; gap: 14px; }
.brand-mark { width: 46px; height: 46px; border-radius: 12px; background: var(--accent); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; }
.cover-title { font-size: 58px; font-weight: 800; margin: 26px 0 8px; letter-spacing: -.02em; }
.cover-sub { font-size: 24px; font-weight: 700; color: #ddd7c9; margin: 0 0 18px; }
.cover-meta { font-size: 12px; color: var(--muted-on-dark); line-height: 1.8; }
.cover-shot { position: absolute; right: 64px; top: 130px; width: 500px; border: 1px solid #3a362f; border-radius: 8px; }
.cover-cap { position: absolute; right: 64px; top: 470px; width: 500px; text-align: center; color: #8c8678; font-size: 11px; }
table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
th { background: var(--accent); color: #fff; text-align: left; font-weight: 700; padding: 8px 10px; }
td { border-bottom: 1px solid var(--border); padding: 7px 10px; vertical-align: top; color: var(--muted); }
td:first-child { color: var(--ink); font-weight: 600; }
tr:last-child td { border-bottom: 0; }
.tbl { border: 1px solid var(--border); border-radius: 9px; overflow: hidden; background: var(--card); }
.metric { font-size: 30px; font-weight: 800; color: var(--accent); line-height: 1.1; }
.metric-label { font-size: 12px; font-weight: 700; margin-top: 6px; }
.chain { display: flex; gap: 7px; flex-wrap: wrap; }
.shot-box { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; background: #fff; }
.shot-box img { display: block; width: 100%; height: auto; }
.shot-cap { font-size: 10.5px; color: var(--faint); margin-top: 5px; }
.arch { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.arch-box { background: var(--card); border: 1px solid var(--border); border-radius: 9px; padding: 12px; text-align: center; }
.arch-box b { display: block; font-size: 12.5px; color: var(--ink); }
.arch-box span { display: block; font-size: 10.5px; color: var(--muted); margin-top: 5px; line-height: 1.4; }
.arch-arrow { text-align: center; color: var(--faint); font-size: 15px; align-self: center; }
.dark-band { background: var(--dark); color: var(--paper-on-dark); border-radius: 10px; padding: 14px 18px; }
.dark-band b { color: #fff; }
.formula { font-family: Consolas, "Segoe UI", monospace; font-size: 25px; font-weight: 700; letter-spacing: .01em; }
ul.clean { margin: 0; padding-left: 18px; }
ul.clean li { font-size: 12.5px; line-height: 1.55; color: var(--muted); margin: 3px 0; }
.steps { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.step { border: 1px solid var(--border); border-radius: 9px; padding: 11px 12px; background: var(--card); }
.step b { display: block; color: var(--accent); font-size: 18px; }
.step strong { display: block; font-size: 12.5px; margin: 4px 0 5px; }
.step span { font-size: 10.5px; color: var(--muted); line-height: 1.45; }

/* HUD / controls */
.hud { position: fixed; left: 0; right: 0; bottom: 16px; z-index: 20; display: flex; align-items: center;
  justify-content: center; gap: 12px; color: #b8b2a4; font-size: 12px; user-select: none; }
.hud button { border: 1px solid #3a362f; background: rgba(20,19,16,.85); color: #f3efe6;
  border-radius: 7px; padding: 6px 12px; font-size: 12px; cursor: pointer; }
.hud button:hover { border-color: #6b665c; }
.progress { position: fixed; left: 0; right: 0; top: 0; height: 3px; background: transparent; z-index: 20; }
.progress i { display: block; height: 100%; width: 0; background: var(--accent); transition: width .18s ease; }
.notes-panel { position: fixed; left: 0; right: 0; bottom: 0; z-index: 30; max-height: 34vh; overflow: auto;
  background: rgba(15,14,12,.96); border-top: 1px solid #35322b; color: #d8d2c4; padding: 14px 22px;
  font-size: 13px; line-height: 1.6; display: none; white-space: pre-wrap; }
.notes-panel.show { display: block; }
.notes-panel b { color: #fff; }
.hint { position: fixed; right: 16px; top: 14px; z-index: 20; color: #6b665c; font-size: 10.5px; text-align: right; }

@media print {
  html, body { background: #fff; }
  .stage { position: static; display: block; }
  .deck { transform: none !important; width: 1280px; height: auto; }
  .slide { position: relative; display: flex !important; opacity: 1 !important; pointer-events: auto;
    width: 1280px; height: 720px; page-break-after: always; break-after: page; }
  .slide:last-child { page-break-after: auto; break-after: auto; }
  .hud, .progress, .notes-panel, .hint { display: none !important; }
  @page { size: 1280px 720px; margin: 0; }
}
"""

JS = r"""
const slides = [...document.querySelectorAll('.slide')];
const total = slides.length;
let index = 0;
const progress = document.querySelector('.progress i');
const counter = document.querySelector('#counter');
const notesPanel = document.querySelector('#notes');
const stage = document.querySelector('#stage');
const deck = document.querySelector('#deck');

function fit() {
  const scale = Math.min(window.innerWidth / 1280, window.innerHeight / 720) * 0.96;
  deck.style.transform = `scale(${scale})`;
}
window.addEventListener('resize', fit);
fit();

function notesOf(slide) {
  const el = slide.querySelector('.notes');
  if (!el) return '（本页无备注）';
  // <template> 里的文字在 content 文档片段中，直接读 textContent 是空字符串
  return (el.content ? el.content.textContent : el.textContent).trim() || '（本页无备注）';
}
function renderNotes() {
  if (!notesPanel.classList.contains('show')) return;
  notesPanel.textContent = notesOf(slides[index]);
}
function show(n) {
  index = Math.max(0, Math.min(total - 1, n));
  slides.forEach((s, i) => s.classList.toggle('active', i === index));
  progress.style.width = `${((index + 1) / total) * 100}%`;
  counter.textContent = `${index + 1} / ${total}`;
  renderNotes();
  history.replaceState(null, '', `#${index + 1}`);
}
function next() { show(index + 1); }
function prev() { show(index - 1); }

window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); next(); }
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') { e.preventDefault(); prev(); }
  else if (e.key === 'Home') { e.preventDefault(); show(0); }
  else if (e.key === 'End') { e.preventDefault(); show(total - 1); }
  else if (e.key === 'n' || e.key === 'N') { notesPanel.classList.toggle('show'); renderNotes(); }
  else if (e.key === 'f' || e.key === 'F') { if (!document.fullscreenElement) stage.requestFullscreen?.(); else document.exitFullscreen?.(); }
});
document.querySelector('#prev').addEventListener('click', prev);
document.querySelector('#next').addEventListener('click', next);
document.querySelector('#notes-btn').addEventListener('click', () => { notesPanel.classList.toggle('show'); renderNotes(); });
document.querySelector('#full-btn').addEventListener('click', () => {
  if (!document.fullscreenElement) stage.requestFullscreen?.(); else document.exitFullscreen?.();
});
const initial = Number(location.hash.replace('#', ''));
show(Number.isFinite(initial) && initial >= 1 ? initial - 1 : 0);
"""


def slide(content: str, notes: str, dark: bool = False, page: int | None = None) -> str:
    cls = "slide dark" if dark else "slide"
    page_html = f'<div class="page-no">{page:02d}</div>' if page else ""
    return (
        f'<section class="{cls}" data-page="{page or 1}">{page_html}{content}'
        f'<template class="notes">{notes}</template></section>'
    )


def footer() -> str:
    return (
        '<div class="footer"><span>PlayerStock · 软件创新工程实践 · 2026-11</span>'
        '<span>有请下一组 ｜ 8′ 介绍 + 2′ 演示 + 5′ 问答</span></div>'
    )


def head(kicker: str, title: str) -> str:
    return f'<div class="kicker">{kicker}</div><h2 class="title">{title}</h2>'


SLIDES: list[str] = []

# 1 封面
SLIDES.append(slide(
    f"""
    <div class="cover-brand"><div class="brand-mark">P</div>
      <div><div style="font-size:20px;font-weight:800;">PlayerStock</div>
      <div style="font-size:12px;color:#b8b2a4;">虚拟选手股交易模拟</div></div></div>
    <div class="cover-title">PlayerStock</div>
    <div class="cover-sub">把「眼力」变成一条可交易、可解释的价格曲线</div>
    <p class="cover-meta">纯信用点 · 不可充值 / 提现 / 兑换 · 16 名选手 · 8 支战队 · AI 只给建议</p>
    <div style="margin-top:22px;"><span class="pill accent">看懂比赛，从持有起</span></div>
    <div style="position:absolute;left:64px;bottom:44px;font-size:12px;color:#b8b2a4;line-height:1.9;">
      有请下一组 ｜ 王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）<br>
      软件创新工程实践 · 2026-11 · 答辩 15 分钟（8′ + 2′ + 5′）
    </div>
    <img class="cover-shot" src="data:image/png;base64,{IMG['market_dark']}" alt="市场页截图">
    <div class="cover-cap">线上真实界面 · 市场页</div>
    """,
    "【15 秒】各位老师好，我们是「有请下一组」，作品 PlayerStock：用信用点交易 CS2 职业选手虚拟股，"
    "把观众对选手的判断变成可交易、可解释、零风险的价格曲线。接下来 8 分钟讲产品与实现，2 分钟现场演示，5 分钟问答。",
    dark=True,
))

# 2 使命/策略
SLIDES.append(slide(
    head("01 产品设计 · 1.1 使命 / 口号 / 策略", "让判断力变成一条看得懂的价格曲线") +
    """
    <div class="grid2" style="flex:1; align-items:stretch;">
      <div class="card" style="padding:20px 22px;">
        <div class="label">使命 Mission</div>
        <p style="font-size:17px;font-weight:700;line-height:1.6;margin-top:6px;">让每一位电竞观众，都能把自己的判断变成一条看得懂、可验证、零风险的价格曲线。</p>
        <p class="tiny faint" style="margin-top:16px;">边界：纯信用点，不可充值 / 提现 / 兑换；不面向未成年人推广</p>
        <div style="margin-top:18px;border-top:1px solid var(--border);padding-top:12px;">
          <div class="label" style="margin-bottom:6px;">三条可验证原则</div>
          <ul class="clean">
            <li><b>可解释</b>：每次价格变动都能拆出原因，不允许黑箱涨跌</li>
            <li><b>可验证</b>：判断对不对，由价格历史与回测给出证据</li>
            <li><b>零风险</b>：投入的是判断力与注意力，不是钱</li>
          </ul>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div class="card"><div class="label">目标用户（三类 + 一条排除线）</div>
          <p class="small muted">CS2 电竞赛事观众 · 想体验交易但不愿担资金风险的人 · 计算机/数据分析学习者；不做「想靠它赚钱的人」。</p></div>
        <div class="card"><div class="label">如何获得用户（无预算打法）</div>
          <p class="small muted">赛事节点（Major / IEM / BLAST）× 内容化涨跌日报 × 校园电竞社群；现场投屏演示是第一批种子用户。</p></div>
        <div class="card"><div class="label">团队优势（结构对，比人多重要）</div>
          <p class="small muted">4 人能力互补、边界不重叠：前端 / 后端与交易引擎 / 定价与数据 / 智能体·测试·部署；确定性骨架 + 智能体肌肉。</p></div>
      </div>
    </div>
    <div style="margin-top:4px;">
      <p class="tiny muted" style="margin-bottom:6px;"><b>差异化：</b>不跟竞品比「人多」，比「可解释 + 零真实资金」</p>
      <div class="tbl"><table>
        <tr><th style="width:22%">赛事竞猜</th><th style="width:24%">模拟炒股</th><th style="width:26%">预测市场</th><th>PlayerStock（我们）</th></tr>
        <tr><td>猜胜负，无价格曲线</td><td>有交易体验，无电竞标的</td><td>连续价格，但涉真钱/地区限制</td><td>选手价值 + 连续价格 + 每条涨跌可归因 + 零真实资金</td></tr>
      </table></div>
    </div>
    """ + footer(),
    "【40 秒】使命和口号：看懂比赛，从持有起。目标用户是看 CS 比赛、对选手有判断、但不想用真钱的人。"
    "没有推广预算，只靠赛事节点、内容化日报和校园社群。团队 4 人能力互补。与竞品比，差异是标的（选手价值）、可解释、零真实资金。",
    page=2,
))

# 3 产品定义
SLIDES.append(slide(
    head("01 产品设计 · 1.2 产品定义 / 用户故事", "一个纯虚拟、可解释的选手股市场") +
    """
    <div class="quote" style="padding:16px 20px;font-size:14.5px;font-weight:500;line-height:1.65;">
      对于想在观赛时参与「判断」的 CS 观众，PlayerStock 是一个纯信用点、可解释的选手股交易市场；
      它把选手的赛场表现变成可交易、可追溯、可归因的价格曲线；不同于赛事竞猜和模拟炒股，我们不涉及任何真实资金，并且每条涨跌都能拆解原因。
    </div>
    <p class="small sage" style="font-weight:700;">解决的问题：判断无处验证　·　价格变化是黑箱　·　决策门槛高</p>
    <div class="grid3" style="flex:1;">
      <div class="card"><div class="label">交易新手</div>
        <p style="font-size:14px;font-weight:700;line-height:1.4;">打开首页 60 秒内知道「现在该不该买」</p>
        <p class="small muted" style="margin-top:10px;">行情卡 + AI 建议直接给结论，理由可展开</p>
        <p class="tiny faint" style="margin-top:18px;">验收：首笔交易 ≤ 60 秒</p></div>
      <div class="card"><div class="label">行情玩家</div>
        <p style="font-size:14px;font-weight:700;line-height:1.4;">点开选手，看懂价格为什么涨 / 跌</p>
        <p class="small muted" style="margin-top:10px;">价格曲线 + 每条变动的 reason + AI 归因</p>
        <p class="tiny faint" style="margin-top:18px;">验收：每条变动都有 reason</p></div>
      <div class="card"><div class="label">演示者 / 老师</div>
        <p style="font-size:14px;font-weight:700;line-height:1.4;">断网、无 API Key 也能完成交易闭环</p>
        <p class="small muted" style="margin-top:10px;">规则兜底 source=rule_fallback，接口仍 200</p>
        <p class="tiny faint" style="margin-top:18px;">验收：无 Key 仍返回 200</p></div>
    </div>
    <div>
      <p class="tiny muted" style="margin-bottom:6px;">规模与边界（课程 6 天版）</p>
      <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <span class="pill">5000 信用点开局</span><span class="pill">16 名选手 / 8 支战队</span>
        <span class="pill">11 个价格历史点</span><span class="pill">0 充值 / 0 提现 / 0 兑换</span>
      </div>
    </div>
    """ + footer(),
    "【40 秒】一句话定义产品；三个用户故事对应新手、行情玩家、演示者，每个都带验收。"
    "规模是 16 名选手、8 支战队、每人 11 个价格点；5000 信用点开局，全部虚拟不可兑换。",
    page=3,
))

# 4 设计原则
SLIDES.append(slide(
    head("02 产品设计应用的原则", "五条原则，对应五个可被验证的取舍") +
    """
    <div class="grid2" style="flex:1;">
      <div class="card"><div style="display:flex;gap:12px;"><div class="metric" style="font-size:22px;">01</div><div>
        <div class="label">需求原则</div><p style="font-weight:700;">先回答「该不该买」</p>
        <p class="small muted">首屏给结论（BUY/SELL/HOLD + 风险），证据按需展开，不堆术语。</p>
        <p class="tiny faint" style="margin-top:8px;">落地：详情页第一屏是建议卡，工具调用/审计默认收起。</p></div></div></div>
      <div class="card"><div style="display:flex;gap:12px;"><div class="metric" style="font-size:22px;">02</div><div>
        <div class="label">信息原则</div><p style="font-weight:700;">一屏完成行情 → 建议 → 下单</p>
        <p class="small muted">市场页 3 列卡片，详情页左侧图表、右侧交易；不来回跳。</p>
        <p class="tiny faint" style="margin-top:8px;">落地：市场 → 详情 → 交易面板，三步内完成一单。</p></div></div></div>
      <div class="card"><div style="display:flex;gap:12px;"><div class="metric" style="font-size:22px;">03</div><div>
        <div class="label">简化原则</div><p style="font-weight:700;">纸感、低密度、可读</p>
        <p class="small muted">暖纸色 + 1px 细边；正文 16px；一屏 6 张选手卡；去除玻璃和高饱和装饰。</p>
        <p class="tiny faint" style="margin-top:8px;">落地：行高 1.7、深浅色一键切换、移动端下滑隐藏顶栏。</p></div></div></div>
      <div class="card"><div style="display:flex;gap:12px;"><div class="metric" style="font-size:22px;">04</div><div>
        <div class="label">系统原则</div><p style="font-weight:700;">确定性骨架 + 智能体肌肉</p>
        <p class="small muted">交易/定价/结算由确定性代码完成；LLM 只建议，失败自动降级，市场照常运行。</p>
        <p class="tiny faint" style="margin-top:8px;">落地：AI 失败 200 + source=rule_fallback，交易/行情不受影响。</p></div></div></div>
    </div>
    <div class="card"><div style="display:flex;gap:12px;"><div class="metric" style="font-size:22px;">05</div><div>
      <div class="label">审核 / 合规原则</div><p style="font-weight:700;">零真实资金 + 只读 AI</p>
      <p class="small muted">0 充值 / 0 提现 / 0 兑换；AI 不下单、不改余额，每次调用留审计 trace。</p>
      <p class="tiny faint" style="margin-top:8px;">落地：README + 页面双处合规声明；AI 只读红线写进接口契约。</p></div></div></div>
    """ + footer(),
    "【35 秒】设计原则不是背条文，而是每个原则对应一个取舍：先给结论、一屏完成、纸感低密度、"
    "确定性骨架让 LLM 挂了也能交易、合规零真实资金。",
    page=4,
))

# 5 UX
SLIDES.append(slide(
    head("03 产品实现 · 3.1 用户体验设计", "界面：让数据和判断同时可读") +
    f"""
    <div style="display:grid;grid-template-columns:7.05fr 4.9fr;gap:16px;flex:1;min-height:0;">
      <div>
        <div class="shot-box"><img src="data:image/png;base64,{IMG['market_light']}" alt="市场页"></div>
        <div class="shot-cap">市场页：一行简报 + 筛选 + 3 列选手卡（一屏 6 张）</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;min-height:0;">
        <div class="shot-box"><img src="data:image/png;base64,{IMG['detail']}" alt="详情页"></div>
        <div class="shot-cap">详情页：价格曲线 / AI 建议 / 交易同屏</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:start;">
          <div><div class="shot-box"><img src="data:image/png;base64,{IMG['mobile']}" alt="移动端"></div>
            <div class="shot-cap">移动端市场</div></div>
          <div class="card" style="padding:12px 14px;"><div class="label">移动端设计</div>
            <ul class="clean"><li>4 Tab + 顶栏头像</li><li>下滑隐藏顶栏</li><li>深浅色快捷切换</li><li>骨架屏 / 慢加载提示</li></ul>
          </div>
        </div>
      </div>
    </div>
    """ + footer(),
    "【35 秒】桌面市场一屏 6 张卡，简报先给结论；详情页左边价格历史，右边 AI 建议和交易；"
    "移动端底部 4 个导航 + 顶栏头像，下滑隐藏顶栏，深浅色一键切换。全部按可读、低密度做减法。",
    page=5,
))

# 6 技术选型
SLIDES.append(slide(
    head("03 产品实现 · 3.2 技术选型", "轻量、可复现、团队真正 Hold 得住") +
    """
    <div class="tbl" style="flex:1;"><table>
      <tr><th style="width:9%">层</th><th style="width:46%">选型与版本（完整版本表在 README）</th><th>为什么选它</th></tr>
      <tr><td>前端</td><td>Vue 3.5.44 · Vue Router 5.4 · Vite 8.3 · TS 6.0 · Vitest 4.1</td><td>轻量 SPA、类型安全、构建快；4 人里前端同学可独立维护</td></tr>
      <tr><td>后端</td><td>Python 3.12 · FastAPI 0.161 · SQLAlchemy 2.1 · Pydantic 2.14</td><td>自动 OpenAPI 文档、路由清晰、事务可控；与课程/团队技能匹配</td></tr>
      <tr><td>数据</td><td>本地 SQLite / 线上 Render Postgres（psycopg2）</td><td>本地零配置；线上持久化；一套 ORM 双环境复用</td></tr>
      <tr><td>AI</td><td>DeepSeek API（OpenAI 兼容）+ rule_fallback</td><td>自然语言理由 + 规则兜底；无 Key / 超时 / 坏 JSON 都降级为 200</td></tr>
      <tr><td>部署</td><td>Render：Static Site + Web Service + Cron + Postgres</td><td>免费、HTTPS、Blueprint 可复现；CI/CD 与回滚路径清晰</td></tr>
      <tr><td>质量工具</td><td>GitHub Actions · ruff · oxlint · eslint · vue-tsc · pytest</td><td>合并门禁 4 个 job；本地命令与 CI 同口径，避免「本地绿 CI 红」</td></tr>
    </table></div>
    <p class="small sage" style="font-weight:700;">原则：不选「简历上最响」的框架，选团队 6 天内能交付、能测试、能部署、能讲清楚的技术。</p>
    <p class="tiny faint">引用来源：Vue / FastAPI / SQLAlchemy / Vite 官方仓库与文档；DeepSeek 官方 API 文档；版本号与链接见 README / requirements。</p>
    """ + footer(),
    "【30 秒】技术选型一条原则：轻量、可复现、团队 Hold 得住。前端 Vue3+Vite，后端 FastAPI + SQLAlchemy，"
    "线上 Postgres，AI 用 DeepSeek 并保留规则兜底；部署交给 Render + GitHub Actions。",
    page=6,
))

# 7 仓库协作
SLIDES.append(slide(
    head("03 产品实现 · 3.3 代码仓库与协作", "444 次提交、5 位贡献者、4 道 CI 门禁") +
    """
    <p class="small muted" style="font-weight:700;">github.com/July75-bit/Innovation ｜ 部署分支 develop ｜ 共 444 次提交（315 次非合并）</p>
    <div style="display:grid;grid-template-columns:1.1fr 1fr;gap:18px;flex:1;">
      <div class="card" style="display:flex;flex-direction:column;justify-content:center;">
        <div class="label">提交分布（GitHub Pulse / git shortlog，含合并提交）</div>
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:10px;">
          <div style="display:grid;grid-template-columns:78px 1fr 42px;align-items:center;gap:8px;"><span class="small">D 王泽棠</span><div style="height:18px;background:#eee8dc;border-radius:3px;"><div style="width:100%;height:100%;background:var(--accent);border-radius:3px;"></div></div><b class="small">186</b></div>
          <div style="display:grid;grid-template-columns:78px 1fr 42px;align-items:center;gap:8px;"><span class="small">B 胡德昊</span><div style="height:18px;background:#eee8dc;border-radius:3px;"><div style="width:61%;height:100%;background:var(--accent);border-radius:3px;"></div></div><b class="small">114</b></div>
          <div style="display:grid;grid-template-columns:78px 1fr 42px;align-items:center;gap:8px;"><span class="small">A 倪颢容</span><div style="height:18px;background:#eee8dc;border-radius:3px;"><div style="width:40%;height:100%;background:var(--accent);border-radius:3px;"></div></div><b class="small">74</b></div>
          <div style="display:grid;grid-template-columns:78px 1fr 42px;align-items:center;gap:8px;"><span class="small">C 刘宏</span><div style="height:18px;background:#eee8dc;border-radius:3px;"><div style="width:38%;height:100%;background:var(--accent);border-radius:3px;"></div></div><b class="small">70</b></div>
        </div>
        <p class="tiny faint" style="margin-top:12px;">B 的两个本地 GitHub 身份已合并统计（July75-bit / Hu De Hao）。</p>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div class="card"><div class="label">协作与项目管理</div><p class="small muted">GitHub Issues / Projects 做任务与 Kanban；14 条缺陷逐条建 Issue 并关闭；提交信息统一 type(scope): 说明 + 验证；PR/Review 小团队互审。</p></div>
        <div class="card"><div class="label">CI 4 个 job（每次 push 自动跑）</div><p class="small muted">仓库卫生（冲突标记）→ 后端 ruff + pytest → 前端 eslint + vitest + build → 交付物完整性</p></div>
        <div class="card" style="background:#eee8dc;border-color:#ddd6c8;"><p class="small" style="color:var(--ink);">证据：Pulse 提交截图、Issue #22–#35、CI run 记录都在仓库/答辩材料里。</p></div>
      </div>
    </div>
    """ + footer(),
    "【25 秒】仓库在 GitHub 的 July75-bit/Innovation，develop 是部署分支，共 444 次提交、315 次非合并。"
    "四个人都有持续提交；B 的两个本地 GitHub 身份已合并统计。协作靠 Issues/Projects，CI 4 个 job 每次 push 自动跑。",
    page=7,
))

# 8 生命周期问题
SLIDES.append(slide(
    head("03 产品实现 · 3.4 生命周期问题复盘", "6 个真实问题：每个都有原因、修复和验证") +
    """
    <div class="tbl" style="flex:1;"><table>
      <tr><th style="width:25%">问题</th><th style="width:31%">原因</th><th>解决办法（都已验证）</th></tr>
      <tr><td>部署后数据全丢</td><td>免费实例临时盘 + SQLite</td><td>迁 Render Postgres；连接串归一化；启动检测到 SQLite 打警告</td></tr>
      <tr><td>线上启动 No module psycopg</td><td>SQLAlchemy 2.1 默认驱动变更</td><td>统一补 +psycopg2；6 条单测守 URL 归一化</td></tr>
      <tr><td>前端全站 CORS 失败</td><td>CORS_ORIGINS 未填 / 带尾斜杠</td><td>精确 origin + rstrip("/")；线上实测恢复</td></tr>
      <tr><td>简报把模型 JSON 透传</td><td>模型输出未做白名单清洗</td><td>后端清洗 + 前端兜底；新增 4 条测试</td></tr>
      <tr><td>CI 后端 14 秒红</td><td>ruff C901 圈复杂度 11 &gt; 10</td><td>拆成 6 个 helper，复杂度降回阈值内</td></tr>
      <tr><td>首次打开 33.6 秒</td><td>Render 免费实例 15 分钟休眠</td><td>保温 cron + 骨架屏 + GET 重试 + 慢加载提示</td></tr>
    </table></div>
    <p class="small sage" style="font-weight:700;">复盘不是「踩坑列表」：每个问题都补了测试、监控或文档，避免同类问题再发生。</p>
    """ + footer(),
    "【40 秒】挑 6 个真实问题：数据全丢（SQLite 临时盘→Postgres）、psycopg 驱动、CORS、模型输出透传、"
    "CI 圈复杂度、冷启动。每个都说明原因和修复；修复后都有测试或线上验证。",
    page=8,
))

# 9 架构
SLIDES.append(slide(
    head("03 产品实现 · 3.5 概要设计", "系统架构：前后端分离 + 确定性交易内核") +
    """
    <div class="arch" style="margin-top:4px;">
      <div class="arch-box"><b>用户浏览器</b><span>Vue 3 SPA（桌面 / 移动）</span></div>
      <div class="arch-box"><b>Render Static Site</b><span>dist/ + SPA fallback · HTTPS / 全局 CDN</span></div>
      <div class="arch-box"><b>FastAPI /api（23 个接口）</b><span>11 个路由模块：鉴权 / 交易 / AI / 运维</span></div>
      <div class="arch-box"><b>SQLAlchemy 2.1</b><span>ORM / 事务 · 一套模型双库</span></div>
    </div>
    <div style="text-align:center;color:var(--faint);font-size:14px;margin:-2px 0;">← 请求链路 →</div>
    <div class="arch" style="grid-template-columns:repeat(4,1fr);">
      <div class="arch-box"><b>core_engine（纯计算）</b><span>模拟比赛 · z-score<br>定价 P′ = max(1, P×(1+0.15S))</span></div>
      <div class="arch-box"><b>ai/（只读建议）</b><span>上下文 / LLM / 规则兜底<br>6 字段契约 · 20s 超时</span></div>
      <div class="arch-box"><b>业务规则层</b><span>交易事务 · 停牌校验<br>持仓上限 · 余额一致性</span></div>
      <div class="arch-box"><b>数据库</b><span>9 张表<br>Postgres</span></div>
    </div>
    <div class="grid2" style="gap:14px;">
      <div class="dark-band"><b>Render：Static + Web + Cron + Postgres</b><p class="tiny" style="color:#c9c2b2;margin-top:6px;">Blueprint 可复现部署；健康检查 /api/health；GitHub Actions 4 job 门禁 + 自动部署</p></div>
      <div class="card"><div class="label">可观测性</div><p class="small muted">请求日志 / 运行日志 · /api/logs · /api/debug/db（只读自检）· health 探针 · 定时简报新鲜度</p></div>
    </div>
    """ + footer(),
    "【35 秒】架构分四层：前端 SPA、FastAPI 路由、确定性业务内核（core_engine + 规则层）、数据库；"
    "AI 是旁路，只读建议不参与交易。部署是 Render 四件套：静态站、Web Service、Cron、Postgres。",
    page=9,
))

# 10 定价 + AI
SLIDES.append(slide(
    head("03 产品实现 · 3.5.3 算法与 AI", "价格可拆解，建议可回落") +
    """
    <div class="grid2" style="flex:1;">
      <div class="card">
        <div class="label">定价模型：每条涨跌都能拆成一句话</div>
        <div class="formula" style="margin:12px 0 6px;">P′ = max(1.0, P × (1 + 0.15 · S))</div>
        <p class="small muted" style="font-weight:700;">S = clamp(z / 3.0, −1, 1)　｜　单次变动 |Δ| ≤ 20%</p>
        <ul class="clean" style="margin-top:10px;">
          <li>比赛表现用 z-score 标准化，避免强队恒涨、弱队恒跌</li>
          <li>0.15 权重 + 1.0 地板价 + ±20% 熔断，保证可解释、不失控</li>
          <li>每条 price_history 必须带 reason：现场可逐条归因</li>
        </ul>
      </div>
      <div class="card">
        <div class="label">AI 智能体：只给建议，永不改余额</div>
        <div class="chain" style="margin:10px 0 12px;">
          <span class="pill">感知行情</span><span class="pill">分析师</span><span class="pill">风控</span>
          <span class="pill">交易员</span><span class="pill">人点采纳</span><span class="pill">审计</span>
        </div>
        <p class="small muted">DeepSeek API（OpenAI 兼容）+ 20s 超时；无 Key / 超时 / 非法 JSON → source=rule_fallback，接口仍 200。</p>
        <p class="small" style="margin-top:10px;line-height:1.6;">契约固定 6 字段：player_id / action / reason / risk_level / source / disclaimer。<br>
        L4 评测：<b>16/16 走真模型、契约完整率 100%、P95 3.39s</b>（门禁 10s）。</p>
      </div>
    </div>
    <div class="dark-band"><b>为什么不直接让模型定价？—— 确定性优先，智能体做增强</b>
      <p class="tiny" style="color:#c9c2b2;margin-top:6px;">规则版：稳定、零成本、可复现；LLM 版：自然语言理由、多角色视角。两者混合：模型失败自动回落，交易与行情不受影响；
      评测只评「契约 / 可核性 / 合规 / 边界诚实」，不宣称预测准确率。</p></div>
    """ + footer(),
    "【40 秒】定价用 z-score + 线性映射，单次涨跌不超过 20%，每条价格都有 reason，现场能拆。"
    "AI 是旁路：分析师→风控→交易员，人在环、留审计；DeepSeek 挂了走规则兜底，接口仍 200。我们不给模型定价权。",
    page=10,
))

# 11 数据库
SLIDES.append(slide(
    head("03 产品实现 · 3.5.4 数据库设计", "9 张表：交易可追溯，AI 可审计") +
    """
    <div style="display:grid;grid-template-columns:1.4fr 1fr;gap:16px;flex:1;">
      <div class="tbl"><table>
        <tr><th style="width:13%">分组</th><th style="width:37%">表</th><th>关键的不可变 / 一致性设计</th></tr>
        <tr><td>账号</td><td>users / auth_tokens</td><td>余额与初始本金；令牌 30 天、可撤销</td></tr>
        <tr><td>市场</td><td>players / price_history</td><td>价格历史只追加；每条 reason 必填</td></tr>
        <tr><td>交易</td><td>positions / trades</td><td>流水只追加、带 balance_after；持仓唯一(user, player)</td></tr>
        <tr><td>智能体</td><td>agent_traces / decision_logs / price_narratives</td><td>每次调用/采纳/归因都留审计，只读业务</td></tr>
      </table></div>
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div class="card"><div class="label">核心关系</div><p class="small muted">users 1─N positions / trades / auth_tokens<br>players 1─N price_history / positions / trades<br>完整 E-R 图见 database_design.md §1（Mermaid）</p></div>
        <div class="card"><div class="label">交易一致性</div><p class="small muted">余额、持仓、流水在同一事务里写；并发下单用行锁/条件更新；14 条交易规则测试 + 并发测试。</p></div>
        <div class="dark-band"><b>为什么不用缓存/队列？</b><p class="tiny" style="color:#c9c2b2;margin-top:6px;">课程量级不需要；优先保证「数据可追溯 + 事务正确」；ER 图与完整字段见 database_design.md。</p></div>
      </div>
    </div>
    """ + footer(),
    "【25 秒】数据库 9 张表，分账号、市场、交易、智能体四组。两个关键设计：交易流水只追加并记录 balance_after；"
    "持仓唯一约束 + 同一事务写余额/持仓/流水。AI 的调用、采纳、归因都落审计表，业务表只读。",
    page=11,
))

# 12 接口
SLIDES.append(slide(
    head("03 产品实现 · 3.5.5 接口设计", "23 个接口，统一契约与错误码") +
    """
    <div class="tbl" style="flex:1;"><table>
      <tr><th style="width:10%">分组</th><th style="width:61%">接口示例</th><th>契约要点</th></tr>
      <tr><td>行情</td><td>GET /api/players · /api/players/{id} · /api/players/{id}/prices</td><td>列表 / 详情 / 价格历史（按 ts 升序）</td></tr>
      <tr><td>交易</td><td>GET /api/account · /api/account/history · POST /api/trades/buy|sell</td><td>余额/资产曲线；买卖返回余额与流水</td></tr>
      <tr><td>身份</td><td>POST /api/auth/register|login|logout · GET /api/auth/me</td><td>PBKDF2 + 不透明令牌；30 天有效</td></tr>
      <tr><td>AI</td><td>GET /api/analysis/{id} · /api/agent/decision|brief|panel|tools</td><td>6 字段契约；只读；失败 200 + rule_fallback</td></tr>
      <tr><td>运维</td><td>GET /api/health · /api/debug/db · /api/logs</td><td>健康检查 / 只读自检 / 运行日志</td></tr>
    </table></div>
    <div class="grid2">
      <div class="dark-band"><b>在线文档：</b><span class="small" style="color:#c9c2b2;">https://playerstock-backend-mdlk.onrender.com/api/docs</span><p class="tiny" style="color:#c9c2b2;margin-top:5px;">FastAPI 自动生成 OpenAPI / Swagger，可直接试调。</p></div>
      <div class="card"><p class="small muted">工程约定：GET 失败自动重试 1 次（网络/502/503/504）；POST 绝不重试；统一错误码 + 中文 message；敏感字段永不返回。</p></div>
    </div>
    """ + footer(),
    "【20 秒】接口总共 23 个，分行情、交易、身份、AI、运维五组。FastAPI 自动生成 Swagger，老师现场可以打开 /api/docs 试调。"
    "GET 可以安全重试一次，POST 永不重试，避免重复下单。",
    page=12,
))

# 13 质量
SLIDES.append(slide(
    head("03 产品实现 · 3.6 软件质量", "质量不是「跑通过」，是每次都跑、跑得出来") +
    """
    <div class="grid4">
      <div class="card"><div class="metric">330</div><div class="metric-label">后端测试</div><p class="tiny faint">pytest（6 条 live 默认排除）</p></div>
      <div class="card"><div class="metric">182</div><div class="metric-label">前端测试</div><p class="tiny faint">Vitest / 22 个文件</p></div>
      <div class="card"><div class="metric">98%</div><div class="metric-label">核心覆盖率</div><p class="tiny faint">app + core_engine，1956 语句/45 未覆盖</p></div>
      <div class="card"><div class="metric">4</div><div class="metric-label">CI 门禁 job</div><p class="tiny faint">卫生 / 后端 / 前端 / 交付物</p></div>
    </div>
    <div class="grid2" style="flex:1;">
      <div class="card"><div class="label">质量控制与保证方法（3.6.1）</div>
        <ul class="clean">
          <li>日志：/api/logs 保留最近运行日志，关键路径记录请求/错误摘要</li>
          <li>异常：统一 ApiError + 错误码，前端可识别并给出中文提示</li>
          <li>契约：Pydantic schema 校验入参/出参；AI 6 字段固定契约</li>
          <li>并发：下单用事务 + 条件更新；有专门的并发测试</li>
          <li>降级：LLM / 网络 / 冷启动都有兜底路径，不阻塞交易</li>
        </ul></div>
      <div class="card"><div class="label">质量工具（3.6.2）</div>
        <table style="margin-top:2px;">
          <tr><td style="width:34%">ruff（E/F/C901）</td><td>Python 规范 + 圈复杂度，CI 与本地同版本 0.17.4</td></tr>
          <tr><td>oxlint / eslint</td><td>前端规范；diff marker、硬编码色也有守卫</td></tr>
          <tr><td>vue-tsc</td><td>类型检查进 build，类型错误直接挂 CI</td></tr>
          <tr><td>Vitest / pytest</td><td>单元 + 集成 + 评测 + 并发；每次 push 跑</td></tr>
          <tr><td>GitHub Actions</td><td>4 个 job 全绿才部署；44 秒级反馈</td></tr>
        </table></div>
    </div>
    """ + footer(),
    "【30 秒】质量用数字说话：后端 330、前端 182，核心覆盖率 98%；CI 4 个 job 全绿才部署。"
    "除了测试，还有日志、统一异常、契约校验、事务并发和降级路径；工具链和 CI 同口径。",
    page=13,
))

# 14 代码统计
SLIDES.append(slide(
    head("03 产品实现 · 3.7 代码统计", "代码量不是目标，结构清楚才是") +
    """
    <div style="display:grid;grid-template-columns:1.05fr 1fr;gap:16px;flex:1;">
      <div class="tbl"><table>
        <tr><th>语言</th><th>文件数</th><th>行数</th></tr>
        <tr><td>Python</td><td>109</td><td>16,391</td></tr>
        <tr><td>Vue</td><td>20</td><td>8,835</td></tr>
        <tr><td>TypeScript</td><td>47</td><td>6,350</td></tr>
        <tr><td>CSS</td><td>3</td><td>782</td></tr>
        <tr><td>HTML</td><td>3</td><td>1,083</td></tr>
        <tr><td>Markdown（文档）</td><td>71</td><td>12,452</td></tr>
      </table></div>
      <div style="display:flex;flex-direction:column;gap:10px;">
        <div class="card"><div class="label">模块数（3.7）</div><p class="small muted">前端：8 个视图、9 个组件、7 个 composable、22 个测试文件；<br>后端：11 个路由模块、9 个 AI 模块、4 个 core_engine 模块、9 张表。</p></div>
        <div class="dark-band"><b>AI Vibe coding 与团队编写的比例</b><p class="tiny" style="color:#c9c2b2;margin-top:6px;">未做逐行归因，不编造百分比。AI 参与：代码建议、测试生成、文档整理；核心交易/定价/权限逻辑由成员编写并互审；所有提交经 CI 与代码评审，来源可追溯。</p></div>
      </div>
    </div>
    <p class="small sage" style="font-weight:700;">可执行代码合计约 33,000 行；文档约 12,000 行（63 份 md）。</p>
    """ + footer(),
    "【15 秒】可执行代码约 3.3 万行，文档约 1.2 万行；前端 8 视图/9 组件，后端 11 路由模块/9 AI 模块。"
    "AI 参与建议、测试和文档，核心逻辑人工编写并互审，所有提交有 CI 和评审。",
    page=14,
))

# 15 测试与容量
SLIDES.append(slide(
    head("验收 · 测试与容量", "用户测试 + 智能体评测 + 压测，三条证据链") +
    """
    <div class="grid2" style="flex:1;">
      <div class="card"><div class="metric">33 项</div><div class="metric-label">用户测试表</div><p class="small sage" style="font-weight:700;">32 通过 / 1 部分通过</p><p class="tiny faint">对话/状态/错误/边界逐项实测，截图留痕</p></div>
      <div class="card"><div class="metric">16/16</div><div class="metric-label">AI 契约评测</div><p class="small sage" style="font-weight:700;">source=llm 100% · P95 3.39s</p><p class="tiny faint">6 字段完整率 100%，合规/可核性全过</p></div>
      <div class="card"><div class="metric">11/11</div><div class="metric-label">红队用例</div><p class="small sage" style="font-weight:700;">提示注入 / 越权 / 伪造来源</p><p class="tiny faint">全部守住，审计日志可追</p></div>
      <div class="card"><div class="metric">38 req/s</div><div class="metric-label">只读压测</div><p class="small sage" style="font-weight:700;">≈190 人同时在线 · 0 错误</p><p class="tiny faint">瓶颈是免费档 0.1 vCPU，不是代码</p></div>
    </div>
    <p class="small muted">诚实说明：交叉用户测试样本较小；没有真实赛事数据与真实资金，因此不宣称预测准确率或长期留存。这些是课程作品的边界，不是隐藏项。</p>
    <div class="card" style="background:#eee8dc;border-color:#ddd6c8;"><p class="tiny" style="color:var(--ink);">证据索引：docs/acceptance/evidence（146 张截图）· test_report.md · agent_eval_report.md · load_test_report.md</p></div>
    """ + footer(),
    "【20 秒】三条证据链：33 项用户测试（32 通过/1 部分）、AI 契约 16/16、红队 11/11、压测 38 req/s、190 并发 0 错误。"
    "同时诚实说明边界：交叉测试样本小、无真实赛果、不做准确率承诺。",
    page=15,
))

# 16 演示 & Q&A
SLIDES.append(slide(
    head("演示与问答", "2 分钟现场演示：一条完整的判断→交易→复盘") +
    """
    <div class="steps">
      <div class="step"><b>01</b><strong>市场</strong><span>打开市场页：简报先给结论，3 列选手卡看涨跌与停牌</span></div>
      <div class="step"><b>02</b><strong>详情</strong><span>点开选手：价格曲线 + AI 建议（理由/风险/来源）+ 停牌提示</span></div>
      <div class="step"><b>03</b><strong>下单</strong><span>买入 2 股：余额、持仓、流水同屏变化；尝试停牌选手被规则拦住</span></div>
      <div class="step"><b>04</b><strong>复盘</strong><span>持仓/流水核对；个人页看资产曲线、交易统计、深浅色切换</span></div>
      <div class="step"><b>05</b><strong>兜底</strong><span>断网/无 Key 场景：AI 走 rule_fallback，行情和交易仍可用</span></div>
    </div>
    <p class="label" style="margin-top:4px;">5 分钟问答 · 最可能被问到的 4 个问题</p>
    <div class="grid2" style="flex:1;">
      <div class="card"><p style="font-weight:700;">“这不就是赌博 / 竞猜吗？”</p><p class="small muted" style="margin-top:5px;">不接入真钱、无充值提现兑换；定位是观赛判断与工程练习，合规声明在 README 与页面。</p></div>
      <div class="card"><p style="font-weight:700;">“AI 乱说怎么办？”</p><p class="small muted" style="margin-top:5px;">AI 只读建议、6 字段契约 + 规则兜底；每次调用留 trace，不写余额、不下单。</p></div>
      <div class="card"><p style="font-weight:700;">“4 个人 6 天怎么分工？”</p><p class="small muted" style="margin-top:5px;">A 前端 / B 后端与交易引擎 / C 定价与数据 / D AI·测试·部署·文档；接口契约第 1 天锁定。</p></div>
      <div class="card"><p style="font-weight:700;">“系统挂了还能演示吗？”</p><p class="small muted" style="margin-top:5px;">交易/定价是确定性代码；AI 有 rule_fallback，冷启动有保温 + 重试 + 骨架屏。</p></div>
    </div>
    <p style="font-size:19px;font-weight:800;color:var(--accent);margin-top:2px;">谢谢，欢迎提问。</p>
    """ + footer(),
    "【5 秒】下面用 2 分钟演示一条完整链路：市场→详情→买入→复盘，再补停牌拦截和 AI 降级；最后 5 分钟回答问题。谢谢。",
    page=16,
))

HTML = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PlayerStock 答辩 · 有请下一组</title>
<style>{CSS}</style>
</head>
<body>
<div class="progress"><i></i></div>
<div class="hint">← → / 空格 翻页　·　N 讲稿　·　F 全屏　·　Ctrl+P 打印 PDF</div>
<div class="stage" id="stage"><div class="deck" id="deck">
{''.join(SLIDES)}
</div></div>
<div class="hud">
  <button id="prev" type="button">← 上一页</button>
  <span id="counter">1 / {len(SLIDES)}</span>
  <button id="next" type="button">下一页 →</button>
  <button id="notes-btn" type="button">讲稿 N</button>
  <button id="full-btn" type="button">全屏 F</button>
</div>
<div class="notes-panel" id="notes"></div>
<script>{JS}</script>
</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"saved {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {len(SLIDES)} slides)")
