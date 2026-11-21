# -*- coding: utf-8 -*-
"""生成 PlayerStock 答辩 PPT（16:9，16 页，8 分钟讲稿 + 2 分钟演示衔接 + Q&A）。

内容依据：
- 《软件创新工程实践》第 6 天答辩要求（8′ 幻灯片 40% / 2′ 演示 40% / 5′ 问答 20%）
- 课程 wiki「创新工程实践营项目汇报内容」的 1.1–3.7 检查点
- 仓库当前真实数据（2026-11-21）：444 提交 / 315 非合并、330 后端测试、182 前端测试、98% 覆盖率等

用法：
    python docs/presentation/build_defense_deck.py
输出：
    docs/presentation/playerstock_defense.pptx
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "presentation" / "assets"
OUT = ROOT / "docs" / "presentation" / "playerstock_defense.pptx"

# ---------- 视觉主题：沿用产品「暖纸 + 品牌红」 ----------
BG = RGBColor(0xF6, 0xF4, 0xEF)
CARD = RGBColor(0xFC, 0xFB, 0xF8)
INK = RGBColor(0x22, 0x20, 0x1B)
MUTED = RGBColor(0x6B, 0x66, 0x5C)
FAINT = RGBColor(0x9A, 0x94, 0x87)
BORDER = RGBColor(0xE3, 0xDE, 0xD4)
ACCENT = RGBColor(0xA6, 0x2B, 0x2F)
SAGE = RGBColor(0x2E, 0x6B, 0x4F)
DARK = RGBColor(0x14, 0x13, 0x10)
DARK_CARD = RGBColor(0x22, 0x20, 0x1B)
PAPER = RGBColor(0xF3, 0xEF, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Microsoft YaHei"

SW, SH = 13.333, 7.5
MARGIN = 0.72


def _rpr_font(run, name=FONT):
    rpr = run._r.get_or_add_rPr()
    latin = rpr.find(qn("a:latin"))
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = OxmlElement("a:ea")
        if latin is not None:
            latin.addnext(ea)
        else:
            rpr.append(ea)
    ea.set("typeface", name)


def _style_run(run, size, color, bold=False, italic=False, font=FONT):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    _rpr_font(run, font)


def rich(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, margin=0.0):
    """paras: [{"runs":[(text,size,color,bold)], "align":..., "space_after":..., "line":...}]"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = para.get("align", PP_ALIGN.LEFT)
        p.line_spacing = para.get("line", 1.12)
        p.space_after = Pt(para.get("space_after", 0))
        for text, size, color, bold in para["runs"]:
            run = p.add_run()
            run.text = text
            _style_run(run, size, color, bold)
    return box


def text(slide, x, y, w, h, content, size, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, line=1.12):
    return rich(slide, x, y, w, h,
                [{"runs": [(content, size, color, bold)], "align": align, "line": line}], anchor)


def rect(slide, x, y, w, h, fill=CARD, line=None, lw=0.75, radius=0.06):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = radius
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(lw)
    shape.shadow.inherit = False
    shape.text_frame.margin_left = shape.text_frame.margin_right = Inches(0.12)
    shape.text_frame.margin_top = shape.text_frame.margin_bottom = Inches(0.08)
    return shape


def pill(slide, x, y, w, h, label, fill=ACCENT, color=WHITE, size=11, bold=True):
    shape = rect(slide, x, y, w, h, fill=fill, radius=0.5)
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    _style_run(run, size, color, bold)
    return shape


def pic_contain(slide, path, x, y, w, h, border=BORDER):
    from PIL import Image
    image = Image.open(path)
    iw, ih = image.size
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    px, py = x + (w - dw) / 2, y + (h - dh) / 2
    picture = slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(dw), Inches(dh))
    picture.line.color.rgb = border
    picture.line.width = Pt(0.75)
    return picture


def arrow(slide, x1, y1, x2, y2, color=FAINT, width=1.25):
    from pptx.enum.shapes import MSO_CONNECTOR
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    ln = connector.line._get_or_add_ln()
    tail = OxmlElement("a:tailEnd")
    tail.set("type", "triangle")
    tail.set("w", "med")
    tail.set("len", "med")
    ln.append(tail)
    return connector


def table(slide, x, y, w, h, headers, rows, widths, font_size=9.6, header_size=10,
          header_fill=ACCENT, zebra=True):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    for i, width in enumerate(widths):
        tbl.columns[i].width = Inches(width)
    for c, header in enumerate(headers):
        cell = tbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        cell.margin_left = cell.margin_right = Inches(0.08)
        cell.margin_top = cell.margin_bottom = Inches(0.045)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = header
        _style_run(run, header_size, PAPER, True)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD if (not zebra or r % 2 == 1) else BG
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.035)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = str(value)
            _style_run(run, font_size, INK if c == 0 else MUTED, c == 0)
    return tbl


def canvas(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def header(slide, kicker, title, page, dark=False):
    ink = PAPER if dark else INK
    muted = RGBColor(0xB8, 0xB2, 0xA4) if dark else MUTED
    accent = RGBColor(0xE0, 0x8A, 0x86) if dark else ACCENT
    rect(slide, MARGIN, 0.46, 0.26, 0.06, fill=accent, radius=0.0)
    text(slide, MARGIN + 0.36, 0.36, 8.2, 0.26, kicker, 10.5, accent, True)
    text(slide, MARGIN, 0.72, SW - 2 * MARGIN, 0.56, title, 27, ink, True, line=1.05)
    if page:
        text(slide, SW - MARGIN - 1.2, 0.36, 1.2, 0.26, f"{page:02d}", 11, muted, False, PP_ALIGN.RIGHT)


def footer(slide, dark=False):
    color = RGBColor(0x8C, 0x86, 0x78) if dark else FAINT
    line = RGBColor(0x35, 0x32, 0x2B) if dark else BORDER
    rect(slide, MARGIN, SH - 0.62, SW - 2 * MARGIN, 0.012, fill=line, radius=0)
    text(slide, MARGIN, SH - 0.52, 8.0, 0.22, "PlayerStock · 软件创新工程实践 · 2026-11", 9, color)
    text(slide, SW - MARGIN - 4.2, SH - 0.52, 4.2, 0.22, "有请下一组 ｜ 8′ 介绍 + 2′ 演示 + 5′ 问答", 9, color, False, PP_ALIGN.RIGHT)


def notes(slide, content):
    slide.notes_slide.notes_text_frame.text = content


def new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# ============================================================
# 01 封面
# ============================================================
prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)

s = new_slide(prs)
canvas(s)
s.background.fill.fore_color.rgb = DARK
rect(s, 0, 0, SW, SH, fill=DARK, radius=0)
rect(s, 0, 0, 0.16, SH, fill=ACCENT, radius=0)
# 品牌块
rect(s, MARGIN, 0.92, 0.56, 0.56, fill=ACCENT, radius=0.18)
text(s, MARGIN, 1.02, 0.56, 0.36, "P", 20, PAPER, True, PP_ALIGN.CENTER)
text(s, MARGIN + 0.78, 0.98, 6.0, 0.44, "PlayerStock", 20, PAPER, True)
text(s, MARGIN + 0.78, 1.38, 6.0, 0.28, "虚拟选手股交易模拟", 12, RGBColor(0xB8, 0xB2, 0xA4))
text(s, MARGIN, 2.25, 7.0, 1.5, "PlayerStock", 54, PAPER, True, line=1.0)
text(s, MARGIN, 3.32, 6.6, 0.5, "把「眼力」变成一条可交易、可解释的价格曲线", 19, RGBColor(0xD8, 0xD2, 0xC4), True)
text(s, MARGIN, 4.02, 6.4, 0.9,
     "纯信用点 · 不可充值 / 提现 / 兑换 · 16 名选手 · 8 支战队 · AI 只给建议",
     12.5, RGBColor(0xB8, 0xB2, 0xA4), line=1.35)
pill(s, MARGIN, 5.18, 2.85, 0.4, "看懂比赛，从持有起", fill=ACCENT, size=12)
text(s, MARGIN, 6.55, 7.2, 0.28, "有请下一组 ｜ 王泽棠（D）· 倪颢容（A）· 胡德昊（B）· 刘宏（C）", 10.5, RGBColor(0xB8, 0xB2, 0xA4))
text(s, MARGIN, 6.86, 7.2, 0.26, "软件创新工程实践 · 2026-11 · 答辩 15 分钟（8′ + 2′ + 5′）", 9.5, RGBColor(0x8C, 0x86, 0x78))
pic_contain(s, ASSETS / "market-dark.png", 7.65, 1.55, 5.0, 4.05, border=RGBColor(0x3A, 0x36, 0x2F))
text(s, 7.65, 5.72, 5.0, 0.24, "线上真实界面 · 市场页", 9, RGBColor(0x8C, 0x86, 0x78), False, PP_ALIGN.CENTER)
notes(s, "【开场 20 秒】各位老师好，我们是「有请下一组」，作品是 PlayerStock——一个用信用点交易 CS2 职业选手虚拟股的市场。"
         "一句话：把观众对选手的判断，变成一条看得懂、可验证、零风险的价格曲线。"
         "接下来 8 分钟讲产品与实现，2 分钟现场演示，5 分钟回答提问。")

# ============================================================
# 02 使命 / 口号 / 策略
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "01 产品设计 · 1.1 使命 / 口号 / 策略", "让判断力变成一条看得懂的价格曲线", 2)
rect(s, MARGIN, 1.62, 5.55, 2.05, fill=CARD, line=BORDER)
text(s, MARGIN + 0.25, 1.78, 5.05, 0.3, "使命 Mission", 10.5, ACCENT, True)
text(s, MARGIN + 0.25, 2.08, 5.05, 1.1,
     "让每一位电竞观众，都能把自己的判断变成一条看得懂、可验证、零风险的价格曲线。",
     15.5, INK, True, line=1.35)
text(s, MARGIN + 0.25, 3.24, 5.05, 0.28, "边界：纯信用点，不可充值 / 提现 / 兑换；不面向未成年人推广", 9.5, MUTED)

# 右侧 3 张策略卡
rect(s, 6.62, 1.62, 6.0, 1.3, fill=CARD, line=BORDER)
text(s, 6.84, 1.72, 5.6, 0.26, "目标用户（三类 + 一条排除线）", 10.5, ACCENT, True)
text(s, 6.84, 2.02, 5.55, 0.8,
     "CS2 电竞赛事观众 · 想体验交易但不愿担资金风险的人 · 计算机/数据分析学习者；不做「想靠它赚钱的人」。",
     9.8, MUTED, line=1.32)
rect(s, 6.62, 3.02, 6.0, 1.3, fill=CARD, line=BORDER)
text(s, 6.84, 3.12, 5.6, 0.26, "如何获得用户（无预算打法）", 10.5, ACCENT, True)
text(s, 6.84, 3.42, 5.55, 0.8,
     "赛事节点（Major / IEM / BLAST）× 内容化涨跌日报 × 校园电竞社群；现场投屏演示是第一批种子用户。",
     9.8, MUTED, line=1.32)
rect(s, 6.62, 4.42, 6.0, 1.3, fill=CARD, line=BORDER)
text(s, 6.84, 4.52, 5.6, 0.26, "团队优势（结构对，比人多重要）", 10.5, ACCENT, True)
text(s, 6.84, 4.82, 5.55, 0.8,
     "4 人能力互补、边界不重叠：前端 / 后端与交易引擎 / 定价与数据 / 智能体·测试·部署；确定性骨架 + 智能体肌肉。",
     9.8, MUTED, line=1.32)

# 底部差异化对比
text(s, MARGIN, 5.72, 6.2, 0.26, "差异化：不跟竞品比「人多」，比「可解释 + 零真实资金」", 10, MUTED, True)
table(s, MARGIN, 5.98, SW - 2 * MARGIN, 0.68,
      ["赛事竞猜", "模拟炒股", "预测市场", "PlayerStock（我们）"],
      [["猜胜负，无价格曲线", "有交易体验，无电竞标的", "连续价格，但涉真钱/地区限制", "选手价值 + 连续价格 + 每条涨跌可归因 + 零真实资金"]],
      [2.4, 2.6, 2.9, 3.9], font_size=8.4, header_size=9.0)
footer(s)
notes(s, "【15 秒】先给使命和口号：看懂比赛，从持有起。目标用户是看 CS 比赛、对选手有判断、但不想用真钱的人。"
         "我们没有推广预算，只靠赛事节点、内容化日报和校园社群。团队 4 人能力互补。"
         "和竞品比，我们不在「人多」上竞争，而是三点差异：标的是选手价值、价格可解释、零真实资金。")

# ============================================================
# 03 产品定义 / 用户故事
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "01 产品设计 · 1.2 产品定义 / 用户故事", "一个纯虚拟、可解释的选手股市场", 3)
rect(s, MARGIN, 1.6, SW - 2 * MARGIN, 1.12, fill=DARK, line=None, radius=0.04)
text(s, MARGIN + 0.3, 1.72, SW - 2 * MARGIN - 0.6, 0.88,
     "对于想在观赛时参与「判断」的 CS 观众，PlayerStock 是一个纯信用点、可解释的选手股交易市场；"
     "它把选手的赛场表现变成可交易、可追溯、可归因的价格曲线；不同于赛事竞猜和模拟炒股，"
     "我们不涉及任何真实资金，并且每条涨跌都能拆解原因。",
     12.2, PAPER, line=1.45)

text(s, MARGIN, 2.84, SW - 2 * MARGIN, 0.28,
     "解决的问题：判断无处验证　·　价格变化是黑箱　·　决策门槛高", 10, SAGE, True)
cards = [
    ("交易新手", "打开首页 60 秒内知道「现在该不该买」", "行情卡 + AI 建议直接给结论，理由可展开"),
    ("行情玩家", "点开选手，看懂价格为什么涨/跌", "价格曲线 + 每条变动的 reason + AI 归因"),
    ("演示者 / 老师", "断网、无 API Key 也能完成交易闭环", "规则兜底 source=rule_fallback，接口仍 200"),
]
for i, (who, want, how) in enumerate(cards):
    x = MARGIN + i * 4.02
    rect(s, x, 3.22, 3.78, 1.98, fill=CARD, line=BORDER)
    text(s, x + 0.2, 3.34, 3.4, 0.28, who, 10.5, ACCENT, True)
    text(s, x + 0.2, 3.64, 3.4, 0.62, want, 11.8, INK, True, line=1.25)
    text(s, x + 0.2, 4.36, 3.4, 0.78, how, 9.4, MUTED, line=1.35)
    text(s, x + 0.2, 4.96, 3.4, 0.22, ["验收：首笔交易 ≤ 60 秒", "验收：每条变动都有 reason", "验收：无 Key 仍返回 200"][i], 8.0, FAINT)

text(s, MARGIN, 5.38, 4.0, 0.26, "规模与边界（课程 6 天版）", 10, MUTED, True)
pills = ["5000 信用点开局", "16 名选手 / 8 支战队", "11 个价格历史点", "0 充值 / 0 提现 / 0 兑换"]
for i, label in enumerate(pills):
    pill(s, MARGIN + i * 3.02, 5.68, 2.82, 0.36, label, fill=RGBColor(0xEE, 0xE8, 0xDC), color=INK, size=9.2)
footer(s)
notes(s, "【40 秒】用一句话定义产品；三个用户故事分别对应新手、行情玩家、演示者。"
         "规模是课程 6 天版：16 名选手、8 支战队、每人 11 个价格点；5000 信用点开局，全部虚拟，不可兑换。")

# ============================================================
# 04 设计原则
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "02 产品设计应用的原则", "五条原则，对应五个可被验证的取舍", 4)
principles = [
    ("需求原则", "先回答「该不该买」", "首屏给结论（BUY/SELL/HOLD + 风险），证据按需展开，不堆术语。"),
    ("信息原则", "一屏完成行情 → 建议 → 下单", "市场页 3 列卡片，详情页左侧图表、右侧交易；不来回跳。"),
    ("简化原则", "纸感、低密度、可读", "暖纸色 + 1px 细边；正文 16px；一屏 6 张选手卡；去除玻璃和高饱和装饰。"),
    ("系统原则", "确定性骨架 + 智能体肌肉", "交易/定价/结算由确定性代码完成；LLM 只建议，失败自动降级，市场照常运行。"),
    ("审核 / 合规原则", "零真实资金 + 只读 AI", "0 充值 / 0 提现 / 0 兑换；AI 不下单、不改余额，每次调用留审计 trace。"),
]
for i, (name, claim, detail) in enumerate(principles):
    row, col = divmod(i, 2)
    x = MARGIN + col * 6.12
    y = 1.62 + row * 1.52
    width = 5.9 if i < 4 else 12.1
    rect(s, x, y, width, 1.32, fill=CARD, line=BORDER)
    text(s, x + 0.22, y + 0.12, 0.55, 0.4, f"0{i + 1}", 17, ACCENT, True)
    text(s, x + 0.78, y + 0.11, width - 1.0, 0.3, name, 10.5, ACCENT, True)
    text(s, x + 0.78, y + 0.4, width - 1.0, 0.3, claim, 12.5, INK, True)
    text(s, x + 0.78, y + 0.72, width - 1.0, 0.5, detail, 9.0, MUTED, line=1.3)
footer(s)
notes(s, "【40 秒】这一页讲设计原则，不是背条文，而是每个原则对应一个具体取舍："
         "先给结论、一屏完成、纸感低密度、确定性骨架让 LLM 挂了也能交易、合规零真实资金。")

# ============================================================
# 05 产品形态与 UX
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.1 用户体验设计", "界面：让数据和判断同时可读", 5)
pic_contain(s, ASSETS / "market-light.png", MARGIN, 1.6, 7.55, 4.72)
text(s, MARGIN, 6.38, 7.6, 0.24, "市场页：一行简报 + 筛选 + 3 列选手卡（一屏 6 张）", 9, FAINT)
pic_contain(s, ASSETS / "detail-light.png", 8.55, 1.6, 4.05, 2.35)
text(s, 8.55, 4.0, 4.05, 0.22, "详情页：价格曲线 / AI 建议 / 交易同屏", 9, FAINT)
pic_contain(s, ASSETS / "market-mobile.png", 8.55, 4.3, 1.72, 2.02)
text(s, 10.43, 4.3, 2.2, 0.9,
     "移动端：\n4 Tab + 顶栏头像\n下滑隐藏顶栏\n深浅色快捷切换", 9, MUTED, line=1.4)
footer(s)
notes(s, "【35 秒】产品长这样：桌面市场一屏 6 张卡，简报先给结论；详情页左边价格历史，右边 AI 建议和交易；"
         "移动端底部 4 个导航 + 顶栏头像，下滑隐藏顶栏，深浅色一键切换。全部按「可读、低密度」做减法。")

# ============================================================
# 06 技术选型
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.2 技术选型", "轻量、可复现、团队真正Hold得住", 6)
rows = [
    ("前端", "Vue 3.5.44 · Vue Router 5.4 · Vite 8.3 · TS 6.0 · Vitest 4.1", "轻量 SPA、类型安全、构建快；4 人里前端同学可独立维护"),
    ("后端", "Python 3.12 · FastAPI 0.161 · SQLAlchemy 2.1 · Pydantic 2.14", "自动 OpenAPI 文档、路由清晰、事务可控；与课程/团队技能匹配"),
    ("数据", "本地 SQLite / 线上 Render Postgres（psycopg2）", "本地零配置；线上持久化；一套 ORM 双环境复用"),
    ("AI", "DeepSeek API（OpenAI 兼容）+ rule_fallback", "自然语言理由 + 规则兜底；无 Key/超时/坏 JSON 都降级为 200"),
    ("部署", "Render：Static Site + Web Service + Cron + Postgres", "免费、HTTPS、BluePrint 可复现；CI/CD 与回滚路径清晰"),
    ("质量工具", "GitHub Actions · ruff · oxlint · eslint · vue-tsc · pytest", "合并门禁 4 个 job；本地命令与 CI 同口径，避免「本地绿 CI 红」"),
]
table(s, MARGIN, 1.62, SW - 2 * MARGIN, 4.55,
      ["层", "选型与版本（完整版本表在 README）", "为什么选它"],
      rows, [1.05, 5.35, 5.45], font_size=9.2, header_size=9.6)
text(s, MARGIN, 6.3, SW - 2 * MARGIN, 0.22,
     "原则：不选「简历上最响」的框架，选团队 6 天内能交付、能测试、能部署、能讲清楚的技术。", 9.5, SAGE, True)
text(s, MARGIN, 6.56, SW - 2 * MARGIN, 0.2,
     "引用来源：Vue / FastAPI / SQLAlchemy / Vite 官方仓库与文档；DeepSeek 官方 API 文档；版本号与链接见 README / requirements。",
     8.2, FAINT)
footer(s)
notes(s, "【35 秒】技术选型一条原则：轻量、可复现、团队 Hold 得住。前端 Vue3+Vite，后端 FastAPI + SQLAlchemy，"
         "线上 Postgres，AI 用 DeepSeek 并保留规则兜底；部署全部交给 Render + GitHub Actions。")

# ============================================================
# 07 仓库与协作
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.3 代码仓库与协作", "444 次提交、5 位贡献者、4 道 CI 门禁", 7)
text(s, MARGIN, 1.55, 7.2, 0.3, "github.com/July75-bit/Innovation ｜ 部署分支 develop ｜ 共 444 次提交（315 次非合并）", 10, MUTED, True)
chart_data = CategoryChartData()
chart_data.categories = ["D 王泽棠", "B 胡德昊", "A 倪颢容", "C 刘宏"]
chart_data.add_series("提交数", (186, 114, 74, 70))
chart = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(MARGIN), Inches(1.98),
                           Inches(6.3), Inches(3.2), chart_data).chart
chart.has_legend = False
chart.has_title = False
chart.font.size = Pt(9)
chart.font.color.rgb = MUTED
chart.font.name = FONT
plot = chart.plots[0]
plot.gap_width = 55
plot.series[0].format.fill.solid()
plot.series[0].format.fill.fore_color.rgb = ACCENT
chart.value_axis.has_major_gridlines = False
chart.value_axis.visible = False
chart.category_axis.format.line.color.rgb = BORDER
text(s, MARGIN, 5.32, 6.3, 0.24, "提交分布（GitHub Pulse / git shortlog，含合并提交）", 9, FAINT)

rect(s, 7.35, 1.98, 5.25, 1.45, fill=CARD, line=BORDER)
text(s, 7.55, 2.08, 4.9, 0.26, "协作与项目管理", 10.5, ACCENT, True)
text(s, 7.55, 2.38, 4.85, 0.9,
     "GitHub Issues / Projects 做任务与 Kanban；14 条缺陷逐条建 Issue 并关闭；\n"
     "提交信息统一 type(scope): 说明 + 验证；PR/Review 小团队互审。", 9.2, MUTED, line=1.4)
rect(s, 7.35, 3.58, 5.25, 1.35, fill=CARD, line=BORDER)
text(s, 7.55, 3.68, 4.9, 0.26, "CI 4 个 job（每次 push 自动跑）", 10.5, ACCENT, True)
text(s, 7.55, 3.98, 4.85, 0.8,
     "仓库卫生（冲突标记）→ 后端 ruff + pytest → 前端 eslint + vitest + build → 交付物完整性",
     9.2, MUTED, line=1.4)
rect(s, 7.35, 5.08, 5.25, 0.82, fill=RGBColor(0xEE, 0xE8, 0xDC), line=None)
text(s, 7.55, 5.18, 4.9, 0.6,
     "证据：Pulse 提交截图、Issue #22–#35、CI run 记录都在仓库/答辩材料里。", 9.4, INK, line=1.35)
footer(s)
notes(s, "【30 秒】仓库在 GitHub 的 July75-bit/Innovation，develop 是部署分支，共 444 次提交、315 次非合并。"
         "四个人都有持续提交；B 的 GitHub 账号有两个本地身份，已合并统计。协作靠 Issues/Projects，CI 4 个 job 每次 push 自动跑。")

# ============================================================
# 08 生命周期问题与解决
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.4 生命周期问题复盘", "6 个真实问题：每个都有原因、修复和验证", 8)
rows = [
    ("部署后数据全丢", "免费实例临时盘 + SQLite", "迁 Render Postgres；连接串归一化；启动检测到 SQLite 打警告"),
    ("线上启动 No module psycopg", "SQLAlchemy 2.1 默认驱动变更", "统一补 +psycopg2；6 条单测守 URL 归一化"),
    ("前端全站 CORS 失败", "CORS_ORIGINS 未填 / 带尾斜杠", "精确 origin + rstrip('/')；线上实测恢复"),
    ("简报把模型 JSON 透传", "模型输出未做白名单清洗", "后端清洗 + 前端兜底；新增 4 条测试"),
    ("CI 后端 14 秒红", "ruff C901 圈复杂度 11 > 10", "拆成 6 个 helper，复杂度降回阈值内"),
    ("首次打开 33.6 秒", "Render 免费实例 15 分钟休眠", "保温 cron + 骨架屏 + GET 重试 + 慢加载提示"),
]
table(s, MARGIN, 1.6, SW - 2 * MARGIN, 4.45,
      ["问题", "原因", "解决办法（都已验证）"],
      rows, [3.0, 4.1, 4.6], font_size=9.0, header_size=9.4)
text(s, MARGIN, 6.22, SW - 2 * MARGIN, 0.4,
     "复盘不是「踩坑列表」：每个问题都补了测试、监控或文档，避免同类问题再发生。", 10, SAGE, True)
footer(s)
notes(s, "【25 秒】挑了 6 个真实问题：最典型的是数据全丢（SQLite 临时盘→Postgres）、psycopg 驱动、CORS、"
         "模型输出透传、CI 圈复杂度、冷启动。每个都说明原因和修复；修复后都有测试或线上验证。")

# ============================================================
# 09 系统架构
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.5 概要设计", "系统架构：前后端分离 + 确定性交易内核", 9)
# 分层框
rect(s, 1.0, 1.65, 2.55, 1.05, fill=CARD, line=BORDER)
text(s, 1.0, 1.76, 2.55, 0.28, "用户浏览器", 10.5, INK, True, PP_ALIGN.CENTER)
text(s, 1.0, 2.06, 2.55, 0.5, "Vue 3 SPA\n（桌面 / 移动）", 9, MUTED, False, PP_ALIGN.CENTER, line=1.3)
rect(s, 4.05, 1.65, 2.55, 1.05, fill=CARD, line=BORDER)
text(s, 4.05, 1.76, 2.55, 0.28, "Render Static Site", 10.5, INK, True, PP_ALIGN.CENTER)
text(s, 4.05, 2.06, 2.55, 0.5, "dist/ + SPA fallback\nHTTPS / 全局 CDN", 9, MUTED, False, PP_ALIGN.CENTER, line=1.3)
rect(s, 7.1, 1.65, 2.8, 1.05, fill=CARD, line=BORDER)
text(s, 7.1, 1.76, 2.8, 0.28, "FastAPI /api（23 个接口）", 10.5, INK, True, PP_ALIGN.CENTER)
text(s, 7.1, 2.06, 2.8, 0.5, "11 个路由模块\n鉴权 / 交易 / AI / 运维", 9, MUTED, False, PP_ALIGN.CENTER, line=1.3)
rect(s, 10.45, 1.65, 2.2, 1.05, fill=CARD, line=BORDER)
text(s, 10.45, 1.76, 2.2, 0.28, "SQLAlchemy 2.1", 10.5, INK, True, PP_ALIGN.CENTER)
text(s, 10.45, 2.06, 2.2, 0.5, "ORM / 事务\n一套模型双库", 9, MUTED, False, PP_ALIGN.CENTER, line=1.3)
arrow(s, 3.56, 2.18, 4.03, 2.18)
arrow(s, 6.61, 2.18, 7.08, 2.18)
arrow(s, 9.91, 2.18, 10.43, 2.18)

# 第二层：core_engine / ai / db
rect(s, 1.0, 3.25, 3.25, 1.25, fill=CARD, line=BORDER)
text(s, 1.2, 3.36, 2.9, 0.28, "core_engine（纯计算）", 10.2, SAGE, True)
text(s, 1.2, 3.68, 2.9, 0.7, "模拟比赛 · z-score\n定价 P′ = max(1, P×(1+0.15S))", 8.8, MUTED, line=1.3)
rect(s, 4.5, 3.25, 3.1, 1.25, fill=CARD, line=BORDER)
text(s, 4.7, 3.36, 2.7, 0.28, "ai/（只读建议）", 10.2, SAGE, True)
text(s, 4.7, 3.68, 2.7, 0.7, "上下文 / LLM / 规则兜底\n6 字段契约 · 20s 超时", 8.8, MUTED, line=1.3)
rect(s, 7.85, 3.25, 2.85, 1.25, fill=CARD, line=BORDER)
text(s, 8.05, 3.36, 2.45, 0.28, "业务规则层", 10.2, SAGE, True)
text(s, 8.05, 3.68, 2.45, 0.7, "交易事务 · 停牌校验\n持仓上限 · 余额一致性", 8.8, MUTED, line=1.3)
rect(s, 10.95, 3.25, 1.7, 1.25, fill=CARD, line=BORDER)
text(s, 11.1, 3.36, 1.4, 0.28, "数据库", 10.2, SAGE, True)
text(s, 11.1, 3.68, 1.4, 0.7, "9 张表\nPostgres", 8.8, MUTED, line=1.3)
arrow(s, 5.9, 2.72, 5.9, 3.23)
arrow(s, 2.6, 2.72, 2.6, 3.23)
arrow(s, 9.2, 2.72, 9.2, 3.23)

# 第三层：部署与运维
rect(s, 1.0, 4.95, 4.9, 1.15, fill=DARK, line=None)
text(s, 1.2, 5.05, 4.5, 0.28, "Render：Static + Web + Cron + Postgres", 10.5, PAPER, True)
text(s, 1.2, 5.37, 4.5, 0.62, "Blueprint 可复现部署；健康检查 /api/health；\nGitHub Actions 4 job 门禁 + 自动部署", 8.8, RGBColor(0xC9, 0xC2, 0xB2), line=1.3)
rect(s, 6.1, 4.95, 6.55, 1.15, fill=CARD, line=BORDER)
text(s, 6.3, 5.05, 6.2, 0.28, "可观测性", 10.5, ACCENT, True)
text(s, 6.3, 5.37, 6.2, 0.62, "请求日志 / 运行日志 · /api/logs · /api/debug/db（只读自检）· health 探针 · 定时简报新鲜度",
     8.8, MUTED, line=1.3)
footer(s)
notes(s, "【40 秒】架构分四层：前端 SPA、FastAPI 路由、确定性业务内核（core_engine + 规则层）、数据库；"
         "AI 是旁路，只读建议不参与交易。部署是 Render 四件套：静态站、Web Service、Cron、Postgres。")

# ============================================================
# 10 定价 + AI 智能体
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.5.3 算法与 AI", "价格可拆解，建议可回落", 10)
rect(s, MARGIN, 1.62, 6.15, 3.0, fill=CARD, line=BORDER)
text(s, MARGIN + 0.25, 1.74, 5.6, 0.28, "定价模型：每条涨跌都能拆成一句话", 10.5, ACCENT, True)
text(s, MARGIN + 0.25, 2.12, 5.65, 0.45, "P′ = max(1.0, P × (1 + 0.15 · S))", 22, INK, True)
text(s, MARGIN + 0.25, 2.68, 5.65, 0.3, "S = clamp(z / 3.0, −1, 1)　｜　单次变动 |Δ| ≤ 20%", 11, MUTED, True)
for i, line in enumerate([
    "比赛表现用 z-score 标准化，避免强队恒涨、弱队恒跌",
    "0.15 权重 + 1.0 地板价 + ±20% 熔断，保证可解释、不失控",
    "每条 price_history 必须带 reason：现场可逐条归因",
]):
    text(s, MARGIN + 0.25, 3.18 + i * 0.34, 5.7, 0.28, f"· {line}", 9.2, MUTED)

rect(s, 7.15, 1.62, 5.5, 3.0, fill=CARD, line=BORDER)
text(s, 7.4, 1.74, 5.0, 0.28, "AI 智能体：只给建议，永不改余额", 10.5, ACCENT, True)
chain = ["感知行情", "分析师", "风控", "交易员", "人点采纳", "审计"]
x = 7.32
for i, step in enumerate(chain):
    pill(s, x, 2.12, 0.8, 0.34, step, fill=RGBColor(0xEE, 0xE8, 0xDC), color=INK, size=7.4)
    x += 0.86
text(s, 7.4, 2.68, 5.0, 0.62,
     "DeepSeek API（OpenAI 兼容）+ 20s 超时；无 Key / 超时 / 非法 JSON → source=rule_fallback，接口仍 200。",
     9.2, MUTED, line=1.35)
text(s, 7.4, 3.42, 5.0, 0.9,
     "契约固定 6 字段：player_id / action / reason / risk_level / source / disclaimer。\n"
     "L4 评测：16/16 走真模型、契约完整率 100%、P95 3.39s（门禁 10s）。",
     9.2, INK, line=1.45)

rect(s, MARGIN, 4.95, SW - 2 * MARGIN, 1.15, fill=DARK, line=None)
text(s, MARGIN + 0.28, 5.06, SW - 2 * MARGIN - 0.5, 0.28,
     "为什么不直接让模型定价？—— 确定性优先，智能体做增强", 11, PAPER, True)
text(s, MARGIN + 0.28, 5.4, SW - 2 * MARGIN - 0.5, 0.55,
     "规则版：稳定、零成本、可复现；LLM 版：自然语言理由、多角色视角。两者做混合：模型失败自动回落，交易与行情不受影响；"
     "评测只评「契约 / 可核性 / 合规 / 边界诚实」，不宣称预测准确率。",
     9.0, RGBColor(0xC9, 0xC2, 0xB2), line=1.35)
footer(s)
notes(s, "【35 秒】定价用 z-score + 线性映射，单次涨跌不超过 20%，每条价格都有 reason，现场能拆。"
         "AI 是旁路：分析师→风控→交易员，人在环、留审计；DeepSeek 挂了走规则兜底，接口仍 200。"
         "我们不给模型定价权，只让它给建议。")

# ============================================================
# 11 数据库设计
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.5.4 数据库设计", "9 张表：交易可追溯，AI 可审计", 11)
table(s, MARGIN, 1.62, 7.35, 3.95,
      ["分组", "表", "关键的不可变 / 一致性设计"],
      [
          ("账号", "users / auth_tokens", "余额与初始本金；令牌 30 天、可撤销"),
          ("市场", "players / price_history", "价格历史只追加；每条 reason 必填"),
          ("交易", "positions / trades", "流水只追加、带 balance_after；持仓唯一(user, player)"),
          ("智能体", "agent_traces / decision_logs / price_narratives", "每次调用/采纳/归因都留审计，只读业务"),
      ], [0.95, 3.3, 3.05], font_size=9.2, header_size=9.5)
# 简单关系示意
rect(s, 8.45, 1.62, 4.2, 1.25, fill=CARD, line=BORDER)
text(s, 8.62, 1.72, 3.9, 0.26, "核心关系", 10.5, ACCENT, True)
text(s, 8.62, 2.0, 3.9, 0.85, "users 1─N positions / trades / auth_tokens\nplayers 1─N price_history / positions / trades\n完整 E-R 图见 database_design.md §1（Mermaid）",
     8.4, MUTED, line=1.4)
rect(s, 8.45, 3.05, 4.2, 1.1, fill=CARD, line=BORDER)
text(s, 8.62, 3.15, 3.9, 0.26, "交易一致性", 10.5, ACCENT, True)
text(s, 8.62, 3.43, 3.9, 0.6, "余额、持仓、流水在同一事务里写；并发下单用行锁/条件更新；14 条交易规则测试 + 并发测试。",
     8.8, MUTED, line=1.35)
rect(s, 8.45, 4.35, 4.2, 1.22, fill=DARK, line=None)
text(s, 8.62, 4.45, 3.9, 0.26, "为什么不用缓存/队列？", 10.2, PAPER, True)
text(s, 8.62, 4.74, 3.9, 0.7, "课程量级不需要；优先保证「数据可追溯 + 事务正确」；ER 图与完整字段见 database_design.md。",
     8.6, RGBColor(0xC9, 0xC2, 0xB2), line=1.3)
footer(s)
notes(s, "【40 秒】数据库 9 张表，分账号、市场、交易、智能体四组。两个关键设计：交易流水只追加并记录 balance_after；"
         "持仓唯一约束 + 同一事务写余额/持仓/流水。AI 的调用、采纳、归因都落审计表，业务表只读。")

# ============================================================
# 12 接口设计
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.5.5 接口设计", "23 个接口，统一契约与错误码", 12)
rows = [
    ("行情", "GET /api/players · /api/players/{id} · /api/players/{id}/prices", "列表 / 详情 / 价格历史（按 ts 升序）"),
    ("交易", "GET /api/account · /api/account/history · POST /api/trades/buy|sell", "余额/资产曲线；买卖返回余额与流水"),
    ("身份", "POST /api/auth/register|login|logout · GET /api/auth/me", "PBKDF2 + 不透明令牌；30 天有效"),
    ("AI", "GET /api/analysis/{id} · /api/agent/decision|brief|panel|tools", "6 字段契约；只读；失败 200 + rule_fallback"),
    ("运维", "GET /api/health · /api/debug/db · /api/logs", "健康检查 / 只读自检 / 运行日志"),
]
table(s, MARGIN, 1.62, SW - 2 * MARGIN, 3.55,
      ["分组", "接口示例", "契约要点"],
      rows, [0.95, 7.2, 3.55], font_size=9.2, header_size=9.5)
rect(s, MARGIN, 5.35, 5.9, 0.95, fill=DARK, line=None)
text(s, MARGIN + 0.22, 5.45, 5.45, 0.75,
     "在线文档：https://playerstock-backend-mdlk.onrender.com/api/docs\nFastAPI 自动生成 OpenAPI / Swagger，可直接试调。",
     9.0, PAPER, line=1.35)
rect(s, 6.85, 5.35, 5.75, 0.95, fill=CARD, line=BORDER)
text(s, 7.05, 5.45, 5.35, 0.75,
     "工程约定：GET 失败自动重试 1 次（网络/502/503/504）；POST 绝不重试；统一错误码 + 中文 message；敏感字段永不返回。",
     9.0, MUTED, line=1.35)
footer(s)
notes(s, "【25 秒】接口总共 23 个，分行情、交易、身份、AI、运维五组。FastAPI 自动生成 Swagger，老师现场可以打开 /api/docs 试调。"
         "有一个工程细节：GET 可以安全重试一次，POST 永不重试，避免重复下单。")

# ============================================================
# 13 软件质量
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.6 软件质量", "质量不是「跑通过」，是每次都跑、跑得出来", 13)
metrics = [("330", "后端测试", "pytest（6 条 live 默认排除）"), ("182", "前端测试", "Vitest / 22 个文件"),
           ("98%", "核心覆盖率", "app + core_engine，1956 语句/45 未覆盖"), ("4", "CI 门禁 job", "卫生 / 后端 / 前端 / 交付物")]
for i, (value, label, detail) in enumerate(metrics):
    x = MARGIN + i * 3.12
    rect(s, x, 1.62, 2.9, 1.3, fill=CARD, line=BORDER)
    text(s, x + 0.22, 1.7, 2.45, 0.5, value, 25, ACCENT, True)
    text(s, x + 0.22, 2.22, 2.45, 0.26, label, 10.5, INK, True)
    text(s, x + 0.22, 2.5, 2.45, 0.3, detail, 7.8, MUTED, line=1.25)

rect(s, MARGIN, 3.15, 6.05, 3.25, fill=CARD, line=BORDER)
text(s, MARGIN + 0.24, 3.27, 5.6, 0.28, "质量控制与保证方法（3.6.1）", 10.5, ACCENT, True)
for i, line in enumerate([
    "日志：/api/logs 保留最近运行日志，关键路径记录请求/错误摘要",
    "异常：统一 ApiError + 错误码，前端可识别并给出中文提示",
    "契约：Pydantic schema 校验入参/出参；AI 6 字段固定契约",
    "并发：下单用事务 + 条件更新；有专门的并发测试",
    "降级：LLM / 网络 / 冷启动都有兜底路径，不阻塞交易",
]):
    text(s, MARGIN + 0.24, 3.62 + i * 0.5, 5.55, 0.42, f"· {line}", 9.2, MUTED, line=1.3)

rect(s, 7.05, 3.15, 5.55, 3.25, fill=CARD, line=BORDER)
text(s, 7.28, 3.27, 5.0, 0.28, "质量工具（3.6.2）", 10.5, ACCENT, True)
tools = [
    ("ruff（E/F/C901）", "Python 规范 + 圈复杂度，CI 与本地同版本 0.17.4"),
    ("oxlint / eslint", "前端规范；diff marker、硬编码色也有守卫"),
    ("vue-tsc", "类型检查进 build，类型错误直接挂 CI"),
    ("Vitest / pytest", "单元 + 集成 + 评测 + 并发；每次 push 跑"),
    ("GitHub Actions", "4 个 job 全绿才部署；44 秒级反馈"),
]
for i, (tool, detail) in enumerate(tools):
    text(s, 7.28, 3.6 + i * 0.52, 1.9, 0.3, tool, 9.2, INK, True)
    text(s, 9.2, 3.6 + i * 0.52, 3.2, 0.3, detail, 8.4, MUTED)
footer(s)
notes(s, "【20 秒】质量用数字说话：后端 330、前端 182，核心覆盖率 98%；CI 4 个 job 全绿才部署。"
         "除了测试，还有日志、统一异常、契约校验、事务并发和降级路径；工具链和 CI 同口径，避免「本地绿、CI 红」。")

# ============================================================
# 14 代码统计
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "03 产品实现 · 3.7 代码统计", "代码量不是目标，结构清楚才是", 14)
table(s, MARGIN, 1.62, 6.35, 3.45,
      ["语言", "文件数", "行数"],
      [("Python", "109", "16,391"), ("Vue", "20", "8,835"), ("TypeScript", "47", "6,350"),
       ("CSS", "3", "782"), ("HTML", "3", "1,083"), ("Markdown（文档）", "71", "12,452")],
      [2.2, 1.6, 2.0], font_size=10, header_size=10)
text(s, MARGIN, 5.22, 6.3, 0.26, "可执行代码合计约 33,000 行；文档约 12,000 行（62+ 份 md）", 9.5, SAGE, True)
rect(s, 7.35, 1.62, 5.25, 1.55, fill=CARD, line=BORDER)
text(s, 7.55, 1.72, 4.9, 0.26, "模块数（3.7）", 10.5, ACCENT, True)
text(s, 7.55, 2.02, 4.85, 1.0,
     "前端：8 个视图、9 个组件、7 个 composable、22 个测试文件；\n"
     "后端：11 个路由模块、9 个 AI 模块、4 个 core_engine 模块、9 张表。", 9.0, MUTED, line=1.35)
rect(s, 7.35, 3.32, 5.25, 2.0, fill=DARK, line=None)
text(s, 7.55, 3.44, 4.9, 0.26, "AI Vibe coding 与团队编写的比例", 10.5, PAPER, True)
text(s, 7.55, 3.76, 4.85, 1.4,
     "未做逐行归因，不编造百分比。\n"
     "AI 参与：代码建议、测试生成、文档整理；\n"
     "核心交易/定价/权限逻辑由成员编写并互审；\n"
     "所有提交经 CI 与代码评审，来源可追溯。", 9.0, RGBColor(0xC9, 0xC2, 0xB2), line=1.45)
footer(s)
notes(s, "【30 秒】代码统计：可执行代码约 3.3 万行，文档约 1.2 万行；模块数前端 8 视图/9 组件，后端 11 路由模块/9 AI 模块。"
         "关于 AI 生成比例：我们没有做不可靠的逐行归因，但 AI 用在建议、测试和文档，核心逻辑人工编写并互审，所有提交有 CI 和评审。")

# ============================================================
# 15 用户测试与容量
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "验收 · 测试与容量", "用户测试 + 智能体评测 + 压测，三条证据链", 15)
cards = [
    ("33 项", "用户测试表", "32 通过 / 1 部分通过", "对话/状态/错误/边界逐项实测，截图留痕"),
    ("16/16", "AI 契约评测", "source=llm 100% · P95 3.39s", "6 字段完整率 100%，合规/可核性全过"),
    ("11/11", "红队用例", "提示注入 / 越权 / 伪造来源", "全部守住，审计日志可追"),
    ("38 req/s", "只读压测", "≈190 人同时在线 · 0 错误", "瓶颈是免费档 0.1 vCPU，不是代码"),
]
for i, (value, label, mid, detail) in enumerate(cards):
    row, col = divmod(i, 2)
    x = MARGIN + col * 6.05
    y = 1.62 + row * 1.75
    rect(s, x, y, 5.8, 1.5, fill=CARD, line=BORDER)
    text(s, x + 0.22, y + 0.12, 1.7, 0.45, value, 21, ACCENT, True)
    text(s, x + 1.95, y + 0.12, 3.65, 0.28, label, 10.5, INK, True)
    text(s, x + 1.95, y + 0.42, 3.65, 0.26, mid, 9.2, SAGE, True)
    text(s, x + 1.95, y + 0.7, 3.65, 0.7, detail, 8.4, MUTED, line=1.3)
text(s, MARGIN, 5.25, SW - 2 * MARGIN, 0.62,
     "诚实说明：交叉用户测试样本较小；没有真实赛事数据与真实资金，因此不宣称预测准确率或长期留存。"
     " 这些是课程作品的边界，不是隐藏项。", 10, MUTED, line=1.35)
rect(s, MARGIN, 6.0, SW - 2 * MARGIN, 0.55, fill=RGBColor(0xEE, 0xE8, 0xDC), line=None)
text(s, MARGIN + 0.22, 6.08, SW - 2 * MARGIN - 0.5, 0.36,
     "证据索引：docs/acceptance/evidence（146 张截图）· test_report.md · agent_eval_report.md · load_test_report.md", 9, INK)
footer(s)
notes(s, "【15 秒】三条证据链：33 项用户测试（32 通过/1 部分）、AI 契约 16/16、红队 11/11、压测 38 req/s、190 并发 0 错误。"
         "同时诚实说明边界：交叉测试样本小、无真实赛果、不做准确率承诺。")

# ============================================================
# 16 演示衔接 / Q&A
# ============================================================
s = new_slide(prs)
canvas(s)
header(s, "演示与问答", "2 分钟现场演示：一条完整的判断→交易→复盘", 16)
steps = [
    ("01", "市场", "打开市场页：简报先给结论，3 列选手卡看涨跌与停牌"),
    ("02", "详情", "点开选手：价格曲线 + AI 建议（理由/风险/来源）+ 停牌提示"),
    ("03", "下单", "买入 2 股：余额、持仓、流水同屏变化；尝试停牌选手被规则拦住"),
    ("04", "复盘", "持仓/流水核对；个人页看资产曲线、交易统计、深浅色切换"),
    ("05", "兜底", "断网/无 Key 场景：AI 走 rule_fallback，行情和交易仍可用"),
]
for i, (num, name, detail) in enumerate(steps):
    x = MARGIN + i * 2.42
    rect(s, x, 1.62, 2.24, 1.5, fill=CARD, line=BORDER)
    text(s, x + 0.18, 1.72, 0.5, 0.4, num, 17, ACCENT, True)
    text(s, x + 0.72, 1.73, 1.4, 0.28, name, 10.5, INK, True)
    text(s, x + 0.18, 2.18, 1.9, 0.82, detail, 8.4, MUTED, line=1.3)
text(s, MARGIN, 3.6, 8.6, 0.28, "5 分钟问答 · 最可能被问到的 4 个问题", 10.5, ACCENT, True)
qas = [
    ("“这不就是赌博/竞猜吗？”", "不接入真钱、无充值提现兑换；定位是观赛判断与工程练习，合规声明在 README 与页面。"),
    ("“AI 乱说怎么办？”", "AI 只读建议、6 字段契约 + 规则兜底；每次调用留 trace，不写余额、不下单。"),
    ("“4 个人 6 天怎么分工？”", "A 前端 / B 后端与交易引擎 / C 定价与数据 / D AI·测试·部署·文档；接口契约第 1 天锁定。"),
    ("“系统挂了还能演示吗？”", "交易/定价是确定性代码；AI 有 rule_fallback，冷启动有保温 + 重试 + 骨架屏。"),
]
for i, (q, a) in enumerate(qas):
    row, col = divmod(i, 2)
    x = MARGIN + col * 6.1
    y = 3.95 + row * 1.25
    rect(s, x, y, 5.85, 1.08, fill=CARD, line=BORDER)
    text(s, x + 0.2, y + 0.1, 5.45, 0.3, q, 9.8, INK, True)
    text(s, x + 0.2, y + 0.42, 5.45, 0.58, a, 8.6, MUTED, line=1.3)
text(s, MARGIN, 6.66, 6.0, 0.3, "谢谢，欢迎提问。", 15, ACCENT, True)
footer(s)
notes(s, "【20 秒】下面用 2 分钟演示一条完整链路：市场→详情→买入→复盘，再补一个停牌拦截和 AI 降级；"
         "最后 5 分钟回答提问。谢谢。")

prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides))
