#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a Swiss / Bauhaus-styled roadbook HTML from an itinerary JSON (itinerary-builder output).

Usage:
    python3 build_swiss.py <roadbook.json> [output.html]

If output is omitted, writes "<input>-精装.html" next to the input.

Design language: International Typographic Style (Müller-Brockmann modular grid,
Vignelli Canon). Monochrome ink + single accent, hairline rules, flat (no shadow),
generous whitespace, left-aligned typographic hierarchy. No gradients, no neon,
no emoji icons, no dark mode — per anti-AI-slop + Hsueh 包豪斯极简 aesthetic.
Stdlib only: re-runnable, no pandoc, no external deps, no network calls.
"""
import json
import html
import os
import re
import sys

try:
    from build_viz import render_viz
except Exception:
    render_viz = lambda d, archviz=False: ""

# archviz-layout hook: when installed, adopt its Type D (嵌入式数据可视化) +
# Swiss dual-track discipline on the inline SVG charts (rx=1 bars, hairline
# <=0.8px, tabular-nums, single accent). Parent palette (roadbook red) is kept.
ARCHVIZ = os.path.isdir(os.path.expanduser("~/.workbuddy-ai/skills/archviz-layout"))

if len(sys.argv) < 2:
    print("usage: build_swiss.py <roadbook.json> [output.html]")
    sys.exit(1)

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(SRC)[0] + "-精装.html"

with open(SRC, "r", encoding="utf-8") as f:
    d = json.load(f)


def esc(x):
    return html.escape(str(x), quote=True)


def esc_text(x):
    # allow literal <br> to pass through; escape everything else
    raw = str(x)
    parts = re.split(r'(<br\s*/?>)', raw, flags=re.IGNORECASE)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append("<br>")
        else:
            out.append(html.escape(p, quote=False))
    return "".join(out)


amap = d.get("amap_uri", "")

# ---- weather ----
# 一格 = 主标签 + 温度行 + 说明。主标签取 city，缺省回退 label；温度行可用
# 显式 `temp` 覆盖（自由文本，非城市格可写「—」）；说明支持 <br> 分两行。
weather_cards = ""
for w in d.get("weather", []):
    name = w.get("city") or w.get("label") or ""
    sub = w.get("label", "") if w.get("city") else ""
    if w.get("temp"):
        temp_html = "<b>{}</b>".format(esc(w["temp"]))
    elif w.get("day") not in (None, "") or w.get("night") not in (None, ""):
        temp_html = "<b>{}°</b>/{}°".format(esc(w.get("day", "")), esc(w.get("night", "")))
    else:
        temp_html = "<b>—</b>"
    # 副标签为空时不发 <small>——空块仍吃 .wk-city small 的 margin-top:2px，会留一条幽灵间距。
    sub_html = "<small>{}</small>".format(esc(sub)) if sub else ""
    weather_cards += (
        '<div class="wk"><div class="wk-city">{name}{sub}</div>'
        '<div class="wk-t">{temp}<span>{text}</span></div></div>'
    ).format(name=esc(name), sub=sub_html, temp=temp_html,
             text=esc_text(w.get("text", "")))

# ---- stages / stops ----
FIELD_ORDER = [("km", "里程"), ("weather", "天气"), ("spots", "景点"),
               ("food", "美食"), ("tickets", "门票"), ("tips", "贴士")]


def stop_block(s):
    name = esc(s.get("name", ""))
    rows = ""
    km = s.get("km")
    if km:
        rows += '<div class="km">里程 · {km}</div>'.format(km=esc(km))
    for key, label in FIELD_ORDER[1:]:
        val = s.get(key)
        if val:
            rows += ('<div class="row"><span class="lab">{lab}</span>'
                     '<span class="val">{val}</span></div>').format(
                lab=esc(label), val=esc(val))
    return (
        '<div class="cnt"><div class="cnt-name">{name}</div>{rows}</div>'
    ).format(name=name, rows=rows)


timeline_html = ""
stage_idx = 0
for st in d.get("stages", []):
    stage_idx += 1
    stops_html = ""
    for s in st.get("stops", []):
        date = esc(s.get("date", ""))
        time = esc(s.get("time", ""))
        stops_html += (
            '<div class="tl-row"><div class="tl-date">{date}<span>{time}</span></div>'
            '<div class="tl-axis"><span class="dot"></span></div>'
            '{cnt}</div>'
        ).format(date=date, time=time, cnt=stop_block(s))
    timeline_html += (
        '<div class="stage"><span class="stage-no">{no:02d}</span>'
        '<span class="stage-name">{name}</span></div>'
        '<div class="tl">{stops}</div>'
    ).format(no=stage_idx, name=esc(st.get("name", "")), stops=stops_html)

# ---- tickets ----
ticket_rows = ""
for t in d.get("tickets", []):
    ticket_rows += (
        '<tr><td>{name}</td><td class="price">{price}</td><td>{book}</td></tr>'
    ).format(name=esc(t.get("name", "")), price=esc(t.get("price", "")),
             book=esc(t.get("book", "")))

# ---- clothing ----
cloth_html = ""
for c in d.get("clothing", []):
    cloth_html += (
        '<div class="cloth"><div class="cloth-g"><i class="sq"></i>{g}</div>'
        '<div class="cloth-it">{it}</div></div>'
    ).format(g=esc(c.get("group", "")), it=esc(c.get("items", "")))

# ---- tips ----
tip_items = ""
for t in d.get("tips", []):
    tip_items += "<li>{t}</li>".format(t=esc(t))

# ---- header extras: route_line / stays ----
# 两者都是「扫一眼就够」的行前信息，放在报头里、不进分区。
# 每条自带 4 空格缩进 + 结尾换行；缺省时为空串，保证旧 JSON 的输出逐字节不变。
route_line_html = ""
if d.get("route_line"):
    route_line_html = '    <div class="route-line">{}</div>\n'.format(esc_text(d["route_line"]))

stays_html = ""
_stays = d.get("stays") or []
if _stays:
    statuses = {s.get("status", "") for s in _stays}
    hoist = statuses.pop() if len(statuses) == 1 else None
    segs = []
    for s in _stays:
        seg = "{name} ×{n} 晚".format(name=esc(s.get("name", "")), n=esc(s.get("nights", "")))
        if not hoist and s.get("status"):
            seg += "（{}）".format(esc(s["status"]))
        segs.append(seg)
    stays_html = ('    <div class="stays"><span class="stays-lab">住宿</span>{segs}{tail}</div>\n'
                  ).format(segs=" ｜ ".join(segs),
                           tail="（{}）".format(esc(hoist)) if hoist else "")

# ---- flights ----
# 按 leg 分组（去程 / 返程 …），组内保持原序。出境行程的核心交通：逐段一行，
# 第二行放「谁 + 中转/行李提示」。时刻按当地时区写，duration 写实际飞行时长。
flight_html = ""
_flights = d.get("flights") or []
if _flights:
    groups = []
    for f in _flights:
        leg = f.get("leg") or ""
        if groups and groups[-1][0] == leg:
            groups[-1][1].append(f)
        else:
            groups.append((leg, [f]))
    for leg, rows in groups:
        if leg:
            flight_html += '    <div class="fl-leg">{}</div>\n'.format(esc(leg))
        for f in rows:
            carrier = " ".join(x for x in (f.get("carrier", ""), f.get("no", "")) if x)
            route = "{} → {}".format(esc(f.get("from", "")), esc(f.get("to", "")))
            dur = ('<span class="fl-dur">飞 {}</span>'.format(esc(f["duration"]))
                   if f.get("duration") else "")
            meta = " ｜ ".join(x for x in (esc(f.get("who", "")), esc_text(f.get("note", ""))) if x)
            flight_html += (
                '    <div class="fl-row"><div class="fl-date">{date}</div>'
                '<div class="fl-main"><div class="fl-route">{carrier}{sep}{route}{dur}</div>'
                '<div class="fl-meta">{meta}</div></div></div>\n'
            ).format(date=esc(f.get("date", "")), carrier=esc(carrier),
                     sep=" · " if carrier else "", route=route, dur=dur, meta=meta)
    flight_html = flight_html.rstrip("\n")

# ---- how-to steps ----
steps = [
    "在<b>手机浏览器</b>（Safari / Chrome）中打开本页；微信内请先用「在浏览器中打开」。",
    "点击上方按钮，<b>高德地图 App 会自动弹出</b>并生成行程路线图。",
    "若没有反应，复制下面的链接，粘贴到手机浏览器地址栏打开。",
]
step_html = "".join("<li>{s}</li>".format(s=s) for s in steps)

viz_html = render_viz(d, archviz=ARCHVIZ)

# ---- 分区组装（序号由计数器给，插入可选分区后不出现空号）----
# inner 自带 4 空格缩进；缺省分区为空串，保证无 flights 的旧 JSON 输出逐字节不变。


def _sec(no, ttl, inner):
    return ('  <section>\n'
            '    <div class="sec-title"><span class="no">{no:02d}</span>'
            '<span class="ttl">{ttl}</span></div>\n'
            '{inner}\n'
            '  </section>\n').format(no=no, ttl=esc(ttl), inner=inner)


_sections = []
_no = 0


def _add(ttl, inner):
    global _no
    _no += 1
    _sections.append(_sec(_no, ttl, inner))


_add("怎么在手机上打开", '    <ol class="steps">{}</ol>'.format(step_html))
_add("行程链接（备用）",
     '    <div class="copy-card">\n'
     '      <div class="link-box" id="linkBox">{}</div>\n'
     '      <button class="btn-copy" id="btnCopy" type="button">复制</button>\n'
     '    </div>'.format(esc(amap)))
if flight_html:
    _add("航班时间线", flight_html)
_add("沿途天气速览",
     '    <div class="weather-grid">{}</div>\n'
     '    <div class="src-note">{}</div>'.format(weather_cards, esc(d.get("weather_note", ""))))
_add("数据可视化", "    " + viz_html)
_add("逐站路书", "    " + timeline_html)
_add("门票与花费参考",
     '    <table class="tk"><tr><th style="width:30%">景点/项目</th>'
     '<th style="width:30%">票价参考</th><th>预约/说明</th></tr>{}</table>\n'
     '    <div class="src-note" style="margin-top:12px; color:#3a352d;">{}</div>\n'
     '    <div class="src-note">{}</div>'.format(
         ticket_rows, esc(d.get("tickets_total", "")), esc(d.get("budget_note", ""))))
_add("穿着建议", "    " + cloth_html)
_add("注意事项", '    <ul class="tips">{}</ul>'.format(tip_items))

sections_html = "\n".join(_sections)

CSS = """
:root{
  --ink:#16140f; --muted:#6f6a60; --faint:#9a948a;
  --paper:#f6f5f1; --card:#ffffff; --line:#e0ddd6; --rule:#cfccc3;
  --accent:#e0362b;
  --maxw:760px;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
html{font-size:16px;-webkit-text-size-adjust:100%;}
body{
  font-family:"Inter","Helvetica Neue","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:var(--paper); color:var(--ink); line-height:1.75;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
.wrap{max-width:var(--maxw); margin:0 auto; padding:0 22px calc(40px + env(safe-area-inset-bottom));}
/* masthead */
.masthead{border-top:5px solid var(--accent); padding:30px 0 22px;}
.eyebrow{font-size:12px; letter-spacing:.22em; text-transform:uppercase; color:var(--accent); font-weight:600; margin-bottom:14px;}
h1{font-size:38px; line-height:1.18; font-weight:700; letter-spacing:-.01em;}
h1 .l2{display:block; color:var(--muted); font-weight:500; font-size:30px;}
.lead{margin-top:16px; font-size:14.5px; color:var(--muted); line-height:1.7; max-width:60ch;}
.lead b{color:var(--ink); font-weight:600;}
/* wechat tip */
.wechat-tip{margin:22px 0; padding:12px 14px; border-left:3px solid var(--accent); background:#fbf1ef; font-size:13px; color:#8a3329; line-height:1.6;}
/* CTA */
.cta{margin:6px 0 8px;}
.btn-open{display:block; width:100%; text-align:center; text-decoration:none;
  background:var(--accent); color:#fff; font-size:18px; font-weight:600; letter-spacing:.02em;
  padding:17px 14px;}
.btn-open:active{transform:translateY(1px); background:#c92f25;}
.btn-open .sub{display:block; font-size:12px; font-weight:400; opacity:.85; margin-top:4px; letter-spacing:.04em;}
.cta-note{font-size:12.5px; color:var(--faint); text-align:center; margin-top:10px;}
/* section */
section{margin-top:42px;}
.sec-title{display:flex; align-items:baseline; gap:12px; margin-bottom:18px; padding-bottom:8px; border-bottom:1px solid var(--rule);}
.sec-title .no{font-size:12px; font-weight:700; color:var(--accent); letter-spacing:.05em;}
.sec-title .ttl{font-size:17px; font-weight:700; letter-spacing:.02em;}
.steps{list-style:none; counter-reset:s;}
.steps li{counter-increment:s; position:relative; padding:0 0 14px 38px; font-size:14px; color:#3a352d; line-height:1.7;}
.steps li::before{content:counter(s,decimal-leading-zero); position:absolute; left:0; top:1px;
  width:26px; height:26px; background:var(--ink); color:#fff; font-size:11px; font-weight:600;
  display:flex; align-items:center; justify-content:center; letter-spacing:0;}
/* copy card */
.copy-card{border:1px solid var(--line); background:var(--card); display:flex; gap:0; align-items:stretch;}
.link-box{flex:1; min-width:0; padding:12px 13px; font-size:11px; color:var(--muted); word-break:break-all; line-height:1.55; user-select:all; font-family:ui-monospace,SFMono-Regular,Menlo,monospace;}
.btn-copy{flex:none; width:74px; border:none; border-left:1px solid var(--line); background:var(--card); color:var(--accent); font-size:14px; font-weight:600; cursor:pointer; font-family:inherit;}
.btn-copy:active{background:#f1efea;}
/* weather */
.weather-grid{display:grid; grid-template-columns:repeat(2,1fr); gap:1px; background:var(--line); border:1px solid var(--line);}
@media(min-width:520px){.weather-grid{grid-template-columns:repeat(3,1fr);}}
.wk{background:var(--card); padding:13px 13px;}
.wk-city{font-size:14px; font-weight:600;}
.wk-city small{display:block; font-size:10.5px; font-weight:400; color:var(--faint); letter-spacing:.04em; margin-top:2px;}
.wk-t{margin-top:8px; font-size:12px; color:var(--muted); line-height:1.5;}
.wk-t b{font-size:20px; color:var(--ink); font-weight:700; margin-right:2px;}
.wk-t span{display:block; margin-top:3px;}
.src-note{font-size:12px; color:var(--faint); margin-top:12px; line-height:1.65;}
/* header extras */
.route-line{margin-top:16px; padding-top:12px; border-top:1px solid var(--line); font-size:14px; color:var(--ink); line-height:1.7;}
.stays{margin-top:9px; font-size:12.5px; color:var(--muted); line-height:1.7;}
.stays-lab{display:inline-block; margin-right:8px; font-size:11px; font-weight:700; letter-spacing:.12em; color:var(--faint);}
/* flights */
.fl-leg{margin:20px 0 8px; font-size:11.5px; font-weight:700; letter-spacing:.14em; color:var(--accent); text-transform:uppercase;}
.fl-leg:first-child{margin-top:0;}
.fl-row{display:grid; grid-template-columns:56px 1fr; column-gap:12px; padding:11px 0; border-top:1px solid var(--line);}
.fl-row:first-child{border-top:none;}
.fl-date{font-size:12px; font-weight:600; color:var(--muted); line-height:1.5; font-variant-numeric:tabular-nums;}
.fl-main{min-width:0;}
.fl-route{font-size:13.5px; font-weight:600; color:var(--ink); line-height:1.6;}
.fl-dur{margin-left:6px; font-size:11.5px; font-weight:400; color:var(--faint);}
.fl-meta{margin-top:4px; font-size:12.5px; color:var(--muted); line-height:1.65;}
/* timeline */
.stage{display:flex; align-items:baseline; gap:10px; margin:30px 0 16px;}
.stage-no{font-size:13px; font-weight:700; color:#fff; background:var(--ink); width:26px; height:26px; display:inline-flex; align-items:center; justify-content:center;}
.stage-name{font-size:15px; font-weight:700; letter-spacing:.03em;}
.tl{position:relative;}
.tl-row{display:grid; grid-template-columns:62px 22px 1fr; column-gap:0; padding-bottom:22px;}
.tl-row:last-child{padding-bottom:0;}
.tl-date{font-size:12px; font-weight:600; color:var(--muted); text-align:right; padding-top:2px; line-height:1.3;}
.tl-date span{display:block; font-weight:400; font-size:11px; color:var(--faint); margin-top:2px;}
.tl-axis{position:relative;}
.tl-axis::before{content:""; position:absolute; left:50%; top:6px; bottom:-22px; width:1px; background:var(--rule); transform:translateX(-50%);}
.tl-row:last-child .tl-axis::before{display:none;}
.dot{position:absolute; top:7px; left:50%; transform:translateX(-50%); width:11px; height:11px; border-radius:50%; background:var(--accent); border:2px solid var(--paper); box-shadow:0 0 0 1px var(--rule);}
.cnt{background:var(--card); border:1px solid var(--line); padding:14px 15px;}
.cnt-name{font-size:15.5px; font-weight:700; line-height:1.4; margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid var(--line);}
.km{font-size:11.5px; letter-spacing:.06em; color:var(--accent); font-weight:600; margin-bottom:9px; text-transform:uppercase;}
.row{display:grid; grid-template-columns:46px 1fr; gap:10px; padding:7px 0; border-top:1px dashed var(--line);}
.row:first-child{border-top:none;}
.lab{flex:none; font-size:11.5px; font-weight:700; letter-spacing:.08em; color:var(--muted); align-self:start; padding-top:1px;}
.val{font-size:13.5px; color:#3a352d; line-height:1.65;}
/* tickets table */
table.tk{width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); font-size:13px;}
table.tk th,table.tk td{padding:10px 11px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; line-height:1.5;}
table.tk th{background:#f1efea; font-weight:700; font-size:12px; letter-spacing:.03em; border-bottom:2px solid var(--ink);}
table.tk tr:last-child td{border-bottom:none;}
table.tk td.price{white-space:nowrap; color:var(--ink); font-weight:600;}
/* clothing */
.cloth{background:var(--card); border:1px solid var(--line); padding:13px 15px; margin-bottom:1px;}
.cloth-g{font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; margin-bottom:4px;}
.cloth-g .sq{width:8px; height:8px; background:var(--accent); display:inline-block; flex:none;}
.cloth-it{font-size:13px; color:#3a352d; line-height:1.6;}
/* tips */
.tips{list-style:none; counter-reset:t;}
.tips li{counter-increment:t; position:relative; padding:8px 0 8px 30px; font-size:13.5px; color:#3a352d; line-height:1.68; border-top:1px solid var(--line);}
.tips li:first-child{border-top:none;}
.tips li::before{content:counter(t,decimal-leading-zero); position:absolute; left:0; top:9px; font-size:11px; font-weight:700; color:var(--accent);}
footer{margin-top:46px; padding-top:18px; border-top:1px solid var(--rule); font-size:11.5px; color:var(--faint); text-align:center; line-height:1.8;}
/* visualization */
.viz-grid{display:grid; grid-template-columns:1fr; gap:14px;}
@media(min-width:560px){.viz-grid{grid-template-columns:1fr 1fr;}}
.viz-card{background:var(--card); border:1px solid var(--line); padding:14px 15px; font-variant-numeric:tabular-nums;}
.viz-card h4{font-size:13px; font-weight:700; margin-bottom:10px; letter-spacing:.02em;}
.viz-card svg{display:block; width:100%; height:auto;}
#toast{position:fixed; left:50%; bottom:calc(26px + env(safe-area-inset-bottom)); transform:translateX(-50%) translateY(8px);
  background:rgba(22,20,15,.94); color:#fff; font-size:13.5px; padding:10px 18px; opacity:0; pointer-events:none;
  transition:opacity .18s ease,transform .18s ease; z-index:9; white-space:nowrap;}
#toast.show{opacity:1; transform:translateX(-50%) translateY(0);}
"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <div class="eyebrow">{eyebrow}</div>
    <h1>{t1}<span class="l2">{t2}</span></h1>
    <p class="lead">{subtitle}</p>
{route_line}{stays}  </header>

  <div class="wechat-tip">微信内可能无法直接跳转高德：请先点右上角「···」→ 选择「在浏览器中打开」，再点下方按钮。</div>

  <div class="cta">
    <a class="btn-open" href="{amap}">在高德地图中打开行程<span class="sub">自动唤起已安装的高德地图 App</span></a>
    <div class="cta-note">手机需已安装「高德地图」App</div>
  </div>

{sections}
  <footer>{footer}</footer>
</div>
<div id="toast" role="status"></div>
<script>
(function(){{
  var btn=document.getElementById('btnCopy'),box=document.getElementById('linkBox'),toast=document.getElementById('toast'),timer=null;
  function show(m){{toast.textContent=m;toast.classList.add('show');if(timer)clearTimeout(timer);timer=setTimeout(function(){{toast.classList.remove('show');}},1600);}}
  if(btn&&box){{btn.addEventListener('click',function(){{
    var t=box.textContent.replace(/\\s+/g,'');
    if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(t).then(function(){{show('已复制，去浏览器地址栏粘贴');}},function(){{fallback(t);}});}}
    else{{fallback(t);}}
  }});}}
  function fallback(t){{var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{{document.execCommand('copy');show('已复制，去浏览器地址栏粘贴');}}catch(e){{show('请长按链接文本手动复制');}}document.body.removeChild(ta);}}
}})();
</script>
</body>
</html>
""".format(
    title=esc(d.get("title", "")),
    css=CSS,
    eyebrow=esc(d.get("eyebrow", "")),
    t1=esc(d.get("title_lines", [""])[0]),
    t2=esc(d.get("title_lines", ["", ""])[1]) if len(d.get("title_lines", [])) > 1 else "",
    subtitle=esc(d.get("subtitle", "")),
    amap=amap,
    route_line=route_line_html,
    stays=stays_html,
    sections=sections_html,
    footer=esc_text(d.get("footer", "")),
)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)

# len(HTML) 是字符数；文件按 UTF-8 落盘，中文占 3 字节，两者差得很远。
# 报「bytes」会让人误以为写坏了（25183 chars / 28015 bytes），所以两个都报。
print("WROTE %s  %d chars / %d bytes" % (OUT, len(HTML), os.path.getsize(OUT)))
