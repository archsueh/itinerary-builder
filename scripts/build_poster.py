#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a single-page 3:4 route poster HTML from an itinerary JSON.

Usage:
    python3 scripts/build_poster.py <data.json> [output.html]

If output is omitted, writes "<input>-海报.html" next to the input.

Why a separate script (not a theme switch in build_swiss.py)
-----------------------------------------------------------
This is a different artifact — a share/print poster — not a skin of the
multi-section roadbook. Its layout (centred hierarchy, double frame, stamp,
capsule tags, schematic route as the hero) conflicts with five Swiss/Bauhaus
roadbook rules; stuffing both into one file is how the old "功能版" renderer
got retired. See references/design-language-print.md §8 decision 1.

Palette choice (this implementation)
------------------------------------
Layout & components follow design-language-print.md; the accent is the
roadbook red `#e0362b` (single emphasis, Bauhaus restraint per SKILL.md),
not the print-language orange/brick/olive triad. Paper is warm cream.
Sans stack matches the roadbook — poster layout, roadbook tokens.

Data contract
-------------
Requires a top-level `poster{}` object. Route nodes prefer `viz.route[]`
(name + segment km → cumulative). Optional `poster.path` (list of [x,y] in
0–1) or per-node `x`/`y` fine-tune the schematic; no map API, no network.

Stdlib only. No poster{} → exits 2 with a clear message (does not touch
build_swiss.py output).
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import sys

# ---- tokens: Bauhaus roadbook palette on warm paper ----
INK = "#16140f"
MUTED = "#6f6a60"
FAINT = "#9a948a"
PAPER = "#f4f1ea"
CARD = "#ffffff"
LINE = "#e0ddd6"
RULE = "#cfccc3"
ACCENT = "#e0362b"
FRAME = "#b8b3a6"
CONTOUR = "#e8e4d8"
PILL_BG = "#ebe7dc"
FONT = (
    "Inter,'Helvetica Neue','PingFang SC',"
    "'Hiragino Sans GB','Microsoft YaHei',sans-serif"
)

# Poster canvas (CSS px / SVG viewBox units; 3:4)
PW, PH = 1080, 1440


def esc(x):
    return html.escape(str(x), quote=True)


def esc_text(x):
    raw = str(x)
    parts = re.split(r"(<br\s*/?>)", raw, flags=re.IGNORECASE)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            out.append("<br>")
        else:
            out.append(html.escape(p, quote=False))
    return "".join(out)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _title_with_highlight(title: str, highlight: str | None) -> str:
    """Wrap the first occurrence of highlight in an accent span."""
    if not highlight:
        return esc(title)
    idx = title.find(highlight)
    if idx < 0:
        return esc(title)
    before = esc(title[:idx])
    mid = esc(highlight)
    after = esc(title[idx + len(highlight) :])
    return (
        '%s<span class="hl">%s</span>%s' % (before, mid, after)
    )


def _slogan_html(lines, highlight: str | None) -> str:
    if not lines:
        return ""
    if isinstance(lines, str):
        lines = [lines]
    bits = []
    for line in lines:
        if highlight and highlight in line:
            idx = line.find(highlight)
            bits.append(
                "%s<span class=\"hl\">%s</span>%s"
                % (
                    esc(line[:idx]),
                    esc(highlight),
                    esc(line[idx + len(highlight) :]),
                )
            )
        else:
            bits.append(esc(line))
    return "<br>".join(bits)


def _collect_nodes(d: dict, poster: dict) -> list[dict]:
    """Build [{name, cum_km, x?, y?, icon?}, ...] from viz.route or poster.nodes."""
    explicit = poster.get("nodes")
    if explicit:
        out = []
        cum = 0.0
        for i, n in enumerate(explicit):
            if not isinstance(n, dict) or not n.get("name"):
                continue
            km = _num(n.get("km"))
            if "cum_km" in n and _num(n["cum_km"]) is not None:
                cum = _num(n["cum_km"])
            elif km is not None:
                if i == 0 and km == 0:
                    cum = 0.0
                else:
                    cum = cum + (km or 0.0) if i > 0 else (km or 0.0)
            out.append(
                {
                    "name": str(n["name"]),
                    "cum_km": cum,
                    "x": _num(n.get("x")),
                    "y": _num(n.get("y")),
                    "icon": n.get("icon"),
                    "note": n.get("note") or "",
                }
            )
        return out

    route = (d.get("viz") or {}).get("route") or []
    out = []
    cum = 0.0
    for i, r in enumerate(route):
        if not isinstance(r, dict) or not r.get("name"):
            continue
        km = _num(r.get("km")) or 0.0
        if i > 0:
            cum += km
        else:
            cum = 0.0 if km == 0 else km
        out.append(
            {
                "name": str(r["name"]),
                "cum_km": cum,
                "x": _num(r.get("x")),
                "y": _num(r.get("y")),
                "icon": r.get("icon"),
                "note": r.get("note") or "",
            }
        )
    return out


def _default_path(n: int) -> list[tuple[float, float]]:
    """Winding schematic in map-area unit square (0–1). Not geography."""
    if n < 2:
        return [(0.2, 0.15), (0.8, 0.85)]
    # A soft S-curve with slight jogs — readable on a phone, not a map.
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = 0.18 + 0.64 * t + 0.10 * math.sin(t * math.pi * 2.2)
        y = 0.12 + 0.76 * t + 0.08 * math.cos(t * math.pi * 1.6 + 0.4)
        # keep inside padding
        x = max(0.08, min(0.92, x))
        y = max(0.06, min(0.94, y))
        pts.append((x, y))
    return pts


def _resolve_path(nodes: list[dict], poster: dict) -> list[tuple[float, float]]:
    raw = poster.get("path")
    if isinstance(raw, list) and len(raw) >= 2:
        pts = []
        for p in raw:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                x, y = _num(p[0]), _num(p[1])
                if x is not None and y is not None:
                    pts.append((max(0.0, min(1.0, x)), max(0.0, min(1.0, y))))
        if len(pts) >= 2:
            # resample / align to node count by taking evenly if lengths differ
            if len(pts) == len(nodes):
                return pts
            # interpolate onto node count
            out = []
            for i in range(len(nodes)):
                t = i / max(1, len(nodes) - 1)
                f = t * (len(pts) - 1)
                j = int(f)
                j = min(j, len(pts) - 2)
                frac = f - j
                x = pts[j][0] * (1 - frac) + pts[j + 1][0] * frac
                y = pts[j][1] * (1 - frac) + pts[j + 1][1] * frac
                out.append((x, y))
            return out

    # per-node x/y if all present
    if nodes and all(n["x"] is not None and n["y"] is not None for n in nodes):
        return [(n["x"], n["y"]) for n in nodes]

    return _default_path(len(nodes) if nodes else 2)


def _fmt_km(v: float) -> str:
    if abs(v - round(v)) < 1e-6:
        return "%dkm" % int(round(v))
    return ("%gkm" % v).replace(".0km", "km")


def _icon_svg(kind: str, cx: float, cy: float, scale: float = 1.0) -> str:
    """Tiny decorative POI icons (std SVG, accent stroke)."""
    s = 14 * scale
    if kind == "fuel":
        return (
            f'<g transform="translate({cx:.1f} {cy:.1f})" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1.6">'
            f'<rect x="{-s*0.35:.1f}" y="{-s*0.45:.1f}" '
            f'width="{s*0.55:.1f}" height="{s*0.9:.1f}" rx="1"/>'
            f'<path d="M{s*0.25:.1f} {-s*0.2:.1f} V{s*0.35:.1f} '
            f'H{s*0.55:.1f} V{-s*0.05:.1f}"/>'
            f'<circle cx="{s*0.55:.1f}" cy="{s*0.15:.1f}" r="{s*0.12:.1f}"/>'
            f"</g>"
        )
    if kind == "stay":
        return (
            f'<g transform="translate({cx:.1f} {cy:.1f})" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1.6">'
            f'<path d="M{-s*0.5:.1f} 0 L0 {-s*0.55:.1f} L{s*0.5:.1f} 0 '
            f'V{s*0.5:.1f} H{-s*0.5:.1f} Z"/>'
            f'<rect x="{-s*0.12:.1f}" y="{s*0.05:.1f}" '
            f'width="{s*0.24:.1f}" height="{s*0.35:.1f}"/>'
            f"</g>"
        )
    if kind == "pin":
        return (
            f'<g transform="translate({cx:.1f} {cy:.1f})" fill="{ACCENT}" stroke="none">'
            f'<path d="M0 {-s*0.15:.1f} '
            f'C{-s*0.45:.1f} {-s*0.7:.1f} {s*0.45:.1f} {-s*0.7:.1f} 0 {-s*0.15:.1f} '
            f'C{s*0.35:.1f} {s*0.05:.1f} 0 {s*0.55:.1f} 0 {s*0.55:.1f} '
            f'C0 {s*0.55:.1f} {-s*0.35:.1f} {s*0.05:.1f} 0 {-s*0.15:.1f} Z"/>'
            f'<circle cx="0" cy="{-s*0.38:.1f}" r="{s*0.16:.1f}" fill="{PAPER}"/>'
            f"</g>"
        )
    return ""


def _contour_group(mw: float, mh: float) -> str:
    """Faint contour decoration — not geographic."""
    parts = []
    centres = [(0.22, 0.28), (0.72, 0.55), (0.40, 0.78)]
    for cx, cy in centres:
        for r in (0.06, 0.10, 0.14):
            parts.append(
                '<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" '
                'fill="none" stroke="%s" stroke-width="1"/>'
                % (cx * mw, cy * mh, r * mw, r * mh * 0.7, CONTOUR)
            )
    # mountain triangles
    tris = [(0.85, 0.18), (0.12, 0.62), (0.78, 0.88)]
    for tx, ty in tris:
        x, y = tx * mw, ty * mh
        parts.append(
            '<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z" '
            'fill="none" stroke="%s" stroke-width="1.2"/>'
            % (x, y, x - 12, y + 18, x + 12, y + 18, RULE)
        )
    return "".join(parts)


def _label_side(i: int, n: int, x: float) -> str:
    """Alternate labels left/right; ends prefer outside."""
    if i == 0:
        return "right" if x < 0.5 else "left"
    if i == n - 1:
        return "left" if x > 0.5 else "right"
    return "right" if i % 2 == 0 else "left"


def render_route_svg(nodes: list[dict], path: list[tuple[float, float]], poster: dict) -> str:
    """Schematic route map — not a geographic map."""
    # Map area inside the poster content column
    mw, mh = 920, 560
    if len(nodes) < 2:
        return (
            '<svg class="route" viewBox="0 0 %d %d" role="img" '
            'aria-label="路线示意图（示意，非地图）">'
            '<text x="%d" y="%d" fill="%s" font-size="14" text-anchor="middle"'
            ' font-family="%s">至少需要 2 个节点</text></svg>'
            % (mw, mh, mw // 2, mh // 2, MUTED, FONT)
        )

    pts = [(p[0] * mw, p[1] * mh) for p in path]
    # smooth-ish polyline via quadratic midpoints
    d_parts = ["M%.1f %.1f" % pts[0]]
    for i in range(1, len(pts)):
        if i < len(pts) - 1:
            mx = (pts[i][0] + pts[i + 1][0]) / 2
            my = (pts[i][1] + pts[i + 1][1]) / 2
            d_parts.append("Q%.1f %.1f %.1f %.1f" % (pts[i][0], pts[i][1], mx, my))
        else:
            d_parts.append("L%.1f %.1f" % pts[i])
    d = " ".join(d_parts)

    layers = [_contour_group(mw, mh)]
    # road casing (ink) + core (accent) — highway-symbol feel, restrained
    layers.append(
        '<path d="%s" fill="none" stroke="%s" stroke-width="12" '
        'stroke-linecap="round" stroke-linejoin="round"/>' % (d, INK)
    )
    layers.append(
        '<path d="%s" fill="none" stroke="%s" stroke-width="6" '
        'stroke-linecap="round" stroke-linejoin="round"/>' % (d, ACCENT)
    )
    # paper dash down the middle
    layers.append(
        '<path d="%s" fill="none" stroke="%s" stroke-width="2" '
        'stroke-linecap="round" stroke-dasharray="6 8" '
        'stroke-linejoin="round" opacity="0.85"/>' % (d, PAPER)
    )

    n = len(nodes)
    for i, (node, (x, y)) in enumerate(zip(nodes, pts)):
        is_end = i == 0 or i == n - 1
        r = 9 if is_end else 7
        if is_end:
            layers.append(
                '<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" stroke="%s" stroke-width="2"/>'
                % (x, y, r, ACCENT, PAPER)
            )
        else:
            layers.append(
                '<circle cx="%.1f" cy="%.1f" r="%d" fill="%s" stroke="%s" stroke-width="2.5"/>'
                % (x, y, r, PAPER, ACCENT)
            )

        side = _label_side(i, n, path[i][0])
        # push labels away from the road; alternate vertical bias
        vbias = -22 if i % 2 == 0 else 26
        lx = x + (36 if side == "right" else -36)
        ly = y + vbias
        layers.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
            'stroke="%s" stroke-width="1" stroke-dasharray="3 3"/>'
            % (x, y, lx, ly - 4, RULE)
        )
        anchor = "start" if side == "right" else "end"
        name = esc(node["name"])
        km_s = esc(_fmt_km(node["cum_km"]))
        layers.append(
            '<text x="%.1f" y="%.1f" text-anchor="%s" font-family="%s" font-size="13">'
            '<tspan fill="%s" font-weight="600">%s</tspan>'
            '<tspan dx="5" fill="%s" font-weight="700" font-variant-numeric="tabular-nums">%s</tspan>'
            "</text>"
            % (lx, ly, anchor, FONT, INK, name, ACCENT, km_s)
        )

        icon = node.get("icon")
        if icon:
            ox = x + (22 if side == "left" else -22)
            oy = y + 22
            layers.append(_icon_svg(str(icon), ox, oy))

    # stamp
    stamp = poster.get("stamp") or {}
    if stamp:
        sx, sy = 120, 160
        rot = stamp.get("rotate", -10)
        status = esc(stamp.get("status") or stamp.get("line1") or "已骑行")
        proof = esc(stamp.get("proof") or stamp.get("line2") or "√ 亲测")
        date = esc(stamp.get("date") or stamp.get("line3") or "")
        layers.append(
            '<g transform="translate(%.1f %.1f) rotate(%s)">'
            '<circle cx="0" cy="0" r="48" fill="%s" stroke="%s" stroke-width="2.2"/>'
            '<circle cx="0" cy="0" r="43" fill="none" stroke="%s" stroke-width="1"/>'
            '<text text-anchor="middle" font-family="%s" fill="%s">'
            '<tspan x="0" y="-12" font-size="13" font-weight="700">%s</tspan>'
            '<tspan x="0" y="5" font-size="12" font-weight="600">%s</tspan>'
            '<tspan x="0" y="22" font-size="11" font-variant-numeric="tabular-nums">%s</tspan>'
            "</text>"
            '<line x1="-28" y1="-2" x2="28" y2="-2" stroke="%s" stroke-width="1"/>'
            "</g>"
            % (
                sx,
                sy,
                rot,
                PAPER,
                ACCENT,
                ACCENT,
                FONT,
                ACCENT,
                status,
                proof,
                date,
                ACCENT,
            )
        )

    return (
        '<svg class="route" viewBox="0 0 %d %d" role="img" '
        'aria-label="路线示意图（示意，非真实地图）">%s</svg>'
        % (mw, mh, "".join(layers))
    )


def render_stats(stats: list) -> str:
    if not stats:
        return ""
    cells = []
    for i, s in enumerate(stats[:3]):
        if not isinstance(s, dict):
            continue
        val = esc(s.get("value") or s.get("v") or "")
        label = esc(s.get("label") or s.get("text") or "")
        accent = bool(s.get("accent") or s.get("emphasize") or i == 1)
        cls = "stat accent" if accent else "stat"
        cells.append(
            '<div class="%s"><div class="stat-v">%s</div>'
            '<div class="stat-l">%s</div></div>' % (cls, val, label)
        )
    if not cells:
        return ""
    return '<div class="stats">%s</div>' % "".join(cells)


def render_tags(tags: list) -> str:
    if not tags:
        return ""
    pills = []
    for t in tags:
        s = str(t).strip()
        if not s:
            continue
        if not s.startswith("#"):
            s = "#" + s
        pills.append('<span class="pill">%s</span>' % esc(s))
    if not pills:
        return ""
    return '<div class="tags">%s</div>' % "".join(pills)


def build(d: dict) -> str:
    poster = d.get("poster")
    if not isinstance(poster, dict) or not poster:
        raise ValueError(
            "缺少顶层 poster{} —— 海报是独立产物，请在 itinerary.json 里加 poster 块；"
            "路书仍用 build_swiss.py"
        )

    nodes = _collect_nodes(d, poster)
    path = _resolve_path(nodes, poster)
    route_svg = render_route_svg(nodes, path, poster)

    kicker = esc(poster.get("kicker") or d.get("eyebrow") or "")
    endpoints = esc(poster.get("endpoints") or "")
    title_raw = poster.get("title") or (
        "".join(d.get("title_lines") or []) or d.get("title") or ""
    )
    highlight = poster.get("highlight")
    title_html = _title_with_highlight(str(title_raw), highlight)
    subtitle = esc_text(poster.get("subtitle") or d.get("subtitle") or "")
    # also highlight a number in subtitle if present as poster.subtitle_highlight
    sh = poster.get("subtitle_highlight")
    if sh and sh in (poster.get("subtitle") or ""):
        sub_raw = poster.get("subtitle") or ""
        idx = sub_raw.find(sh)
        subtitle = (
            esc(sub_raw[:idx])
            + '<span class="hl">%s</span>' % esc(sh)
            + esc(sub_raw[idx + len(sh) :])
        )

    slogan = _slogan_html(
        poster.get("slogan") or [],
        poster.get("slogan_highlight"),
    )
    stats_html = render_stats(poster.get("stats") or [])
    tags_html = render_tags(poster.get("tags") or [])
    footer = esc_text(
        poster.get("footer")
        or d.get("footer")
        or "路线为示意图，非真实地图 · 样本数据仅供演示"
    )
    page_title = esc(d.get("title") or title_raw or "路线海报")

    css = """
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:#e8e4dc;}
body{
  font-family:%(font)s;
  color:%(ink)s;
  -webkit-font-smoothing:antialiased;
  line-height:1.5;
}
.sheet{
  width:min(100vw, 430px);
  margin:0 auto;
  background:%(paper)s;
  aspect-ratio:3/4;
  position:relative;
  box-shadow:0 1px 0 %(line)s;
}
@media print{
  html,body{background:%(paper)s;}
  .sheet{width:100%%;max-width:none;box-shadow:none;margin:0;}
}
.frame{
  position:absolute;inset:14px;
  border:2px solid %(frame)s;
  pointer-events:none;
}
.frame::after{
  content:"";position:absolute;inset:8px;
  border:1px solid %(frame)s;opacity:.7;
}
.inner{
  position:relative;
  z-index:1;
  height:100%%;
  padding:36px 34px 28px;
  display:flex;flex-direction:column;
}
.head{
  display:flex;justify-content:space-between;align-items:baseline;
  gap:12px;margin-bottom:12px;
}
.kicker{
  font-size:11px;letter-spacing:.16em;color:%(muted)s;
  font-weight:600;text-transform:uppercase;
}
.endpoints{
  font-size:12px;letter-spacing:.08em;color:%(ink)s;
  font-weight:700;text-transform:uppercase;white-space:nowrap;
}
h1{
  font-size:36px;font-weight:800;letter-spacing:.02em;
  line-height:1.15;margin:0 0 8px;text-align:center;
}
h1 .hl{
  color:%(accent)s;font-size:1.38em;font-weight:800;
  margin:0 .04em;font-variant-numeric:tabular-nums;
}
.sub{
  text-align:center;font-size:13.5px;color:%(ink)s;
  margin-bottom:10px;line-height:1.55;
}
.sub .hl{color:%(accent)s;font-weight:700;font-variant-numeric:tabular-nums;}
.rule{
  height:4px;width:100%%;margin:0 0 14px;
  background:linear-gradient(90deg,%(accent)s 0 72%%,%(rule)s 72%% 100%%);
}
.map{
  flex:1 1 auto;min-height:0;display:flex;align-items:center;justify-content:center;
  margin:4px 0 12px;
}
.map svg.route{width:100%%;height:auto;display:block;}
.slogan{
  text-align:center;font-size:13.5px;color:%(ink)s;
  line-height:1.65;margin:4px 0 10px;font-weight:500;
}
.slogan .hl{color:%(accent)s;font-weight:700;}
.stats{
  display:grid;grid-template-columns:1fr 1fr 1fr;
  border:1.5px solid %(ink)s;background:%(card)s;
  margin:0 0 10px;
}
.stat{
  padding:10px 6px 9px;text-align:center;
  border-right:1px solid %(rule)s;
}
.stat:last-child{border-right:none;}
.stat-v{
  font-size:18px;font-weight:800;color:%(ink)s;
  font-variant-numeric:tabular-nums;letter-spacing:.01em;line-height:1.2;
}
.stat.accent .stat-v{color:%(accent)s;}
.stat-l{
  margin-top:6px;font-size:11px;color:%(muted)s;line-height:1.4;
}
.tags{
  display:flex;flex-wrap:wrap;gap:8px;justify-content:center;
  margin:0 0 10px;
}
.pill{
  display:inline-block;padding:5px 12px;
  border:1px solid %(ink)s;border-radius:999px;
  background:%(pill)s;font-size:11.5px;color:%(ink)s;
  letter-spacing:.02em;line-height:1.3;
}
.foot{
  text-align:center;font-size:10.5px;color:%(faint)s;line-height:1.55;
  margin-top:auto;padding-top:6px;
}
""".strip() % dict(
        font=FONT,
        ink=INK,
        muted=MUTED,
        faint=FAINT,
        paper=PAPER,
        card=CARD,
        line=LINE,
        rule=RULE,
        accent=ACCENT,
        frame=FRAME,
        pill=PILL_BG,
    )

    body = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<article class="sheet" data-poster="1">
  <div class="frame" aria-hidden="true"></div>
  <div class="inner">
    <header class="head">
      <div class="kicker">{kicker}</div>
      <div class="endpoints">{endpoints}</div>
    </header>
    <h1>{title_html}</h1>
    <p class="sub">{subtitle}</p>
    <div class="rule" aria-hidden="true"></div>
    <div class="map">{route_svg}</div>
    <p class="slogan">{slogan}</p>
    {stats}
    {tags}
    <footer class="foot">{footer}</footer>
  </div>
</article>
</body>
</html>
""".format(
        title=page_title,
        css=css,
        kicker=kicker,
        endpoints=endpoints,
        title_html=title_html,
        subtitle=subtitle,
        route_svg=route_svg,
        slogan=slogan,
        stats=stats_html,
        tags=tags_html,
        footer=footer,
    )
    return body


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = sys.argv[1]
    out = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.splitext(src)[0] + "-海报.html"
    )
    with open(src, "r", encoding="utf-8") as f:
        d = json.load(f)
    try:
        html_out = build(d)
    except ValueError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_out)
    print("WROTE %s  %d chars / %d bytes" % (out, len(html_out), os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
