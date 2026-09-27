#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roadbook information-visualization generator (inline SVG, zero deps).

Reads an itinerary JSON (itinerary-builder output) and emits self-contained inline SVG charts in the
Swiss / Bauhaus visual language (ink #16140f + single accent #e0362b, hairlines,
flat, no shadows). Designed to be embedded into the roadbook HTML so the page
stays fully self-contained (no chart CDN, no JS chart lib).

Charts (data-driven via an optional top-level "viz" block + always-available
weather[]):
  - temp range chart      (from weather[] — renders when at least one cell has
                            numeric day+night; cells without a temperature, e.g.
                            a venue or typhoon-alert cell showing '—', are
                            skipped rather than plotted as 0°)
  - route schematic        (viz.route: ordered nodes + km/hours to next)
  - budget stacked bar     (viz.budget: label/amount)
  - elevation area         (viz.elevation: km/m samples)
  - swimlane               (viz.swimlane: multi-person × calendar — team trips
                            where each traveller has a different route. This is
                            the only chart allowed categorical colours, because
                            city identity IS the information; keep them low-
                            saturation earth tones, never a rainbow.)

If a data block is missing, that chart is silently skipped. render_viz(d,
archviz=...) returns the inner HTML (cards) or "" when nothing can be drawn.

Local-skill hook:
  When `archviz-layout` is installed, pass archviz=True to adopt its
  "类型 D 嵌入式数据可视化" + "瑞士国际主义双轨" discipline:
    - bar <rect> edges rx="1" (no hard 3D / no colorful pie)
    - hairline grid/axis width <= 0.8px
    - tabular-nums on numeric labels (data column alignment)
    - single accent (roadbook red #e0362b; parent owns the palette, NOT swapped
      to terracotta/blue) + ink tints for auxiliary series
  This module is otherwise the zero-dependency fallback and never imports
  archviz-layout — it only adopts its published rules.

Reuse & extraction policy (decided 2026-09-24 — DO NOT split yet):
  `render_viz(dict) -> html` is a pure function, decoupled from the roadbook
  schema (depends only on optional top-level `weather[]` and `viz{}`).
  Decision: keep it inside `itinerary-builder` for now.

  Adjudicated by an independent judge (`jev ask`, 2026-09-24):
    - next action ................ choice -> "keep" p=0.91 (confidence 0.86)
    - stay inside today .......... noul 0.75
    - "one consumer is, BY ITSELF,
       sufficient reason to defer"  noul 0.28   <-- the weak link
    - "dataviz-svg" satisfies the
       skill-naming hard constraints noul 0.91

  Caveat on rationale: the single-consumer fact alone is NOT the load-bearing
  reason — the judge put it at 0.28. The operative reasons are (a) the interface
  is a stable pure function, so extracting later is cheap; (b) no known second
  consumer; (c) pre-scaffolding adds maintenance surface with no present payoff.

  TRIGGER to extract a standalone skill: a 2nd independent consumer appears
  (e.g. financial-report charts, training-log charts). Then move this module into
  a `dataviz-svg` skill (domain-form naming, like `archviz-layout` /
  `scrollytelling-html`) and make this skill depend on it optionally.
"""
import html

# ---- design tokens (match the roadbook HTML CSS) ----
INK = "#16140f"
MUTED = "#6f6a60"
FAINT = "#9a948a"
LINE = "#cfccc3"
CARD = "#ffffff"
PAPER = "#f6f5f1"
ACCENT = "#e0362b"
# ink tints for multi-category bars (Bauhaus: mono + single accent)
TINTS = ["#16140f", "#3a352d", "#6f6a60", "#9a948a", "#cfccc3"]
FONT = "Inter, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif"

W = 720  # viewBox width for all charts


def _esc(s):
    return html.escape(str(s), quote=False)


def _tnum(s):
    """wrap numeric text in a tabular-nums style (archviz Type D alignment)."""
    return ' style="font-variant-numeric:tabular-nums"'


def _num(v):
    """float(v) when v is a number or a numeric string, else None.

    A `weather[]` cell is not required to carry a temperature — a venue cell
    (USJ) or a risk cell (TYPHOON) may show '—'. Treating those as 0 would drag
    the axis floor to freezing, so every consumer must filter on this.
    """
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def temp_chart(weather, archviz=False):
    # 只画有数值温度的格子；非城市格（景点 / 风险项）可以没有 day/night。
    rows = [w for w in (weather or [])
            if _num(w.get("day")) is not None and _num(w.get("night")) is not None]
    if not rows:
        return ""
    cities = [_esc(w.get("city") or w.get("label") or "") for w in rows]
    days = [_num(w["day"]) for w in rows]
    nights = [_num(w["night"]) for w in rows]
    n = len(cities)
    pad_x, pad_y = 38, 26
    H = 210
    tmin = min(nights) - 3
    tmax = max(days) + 3
    if tmax - tmin < 6:
        tmax = tmin + 6
    hw = 0.8 if archviz else 1

    def y(t):
        return H - pad_y - (t - tmin) / (tmax - tmin) * (H - 2 * pad_y)

    grid = ""
    for g in range(int(tmin), int(tmax) + 1, 5):
        yy = y(g)
        grid += '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="%.1f"/>' % (pad_x, yy, W - pad_x, yy, LINE, hw)
        grid += '<text x="%d" y="%.1f" fill="%s" font-size="10" font-family="%s"%s>%d°</text>' % (6, yy + 3, FAINT, FONT, _tnum(g), g)
    bars = ""
    for i, c in enumerate(cities):
        x = pad_x + (i * (W - 2 * pad_x) / (n - 1)) if n > 1 else W / 2
        yd, yn = y(days[i]), y(nights[i])
        bars += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2.5"/>' % (x, yd, x, yn, INK)
        bars += '<rect x="%.1f" y="%.1f" width="11" height="11" fill="%s"/>' % (x - 5.5, yd - 5.5, ACCENT)
        bars += '<text x="%.1f" y="%.1f" fill="%s" font-size="11" font-weight="700" font-family="%s" text-anchor="middle"%s>%g°</text>' % (x, yd - 12, INK, FONT, _tnum(days[i]), days[i])
        bars += '<text x="%.1f" y="%d" fill="%s" font-size="10.5" font-family="%s" text-anchor="middle">%s</text>' % (x, H - 8, MUTED, FONT, c)
    svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" aria-label="沿途气温区间">'
           '%s%s</svg>') % (W, H, grid, bars)
    return _card("沿途气温区间（昼/夜）", svg)


def route_chart(route, archviz=False):
    if not route or len(route) < 2:
        return ""
    total = sum(float(r.get("km", 0)) for r in route[1:])
    if total <= 0:
        return ""
    pad_x, H = 30, 170
    y_mid = 78
    xs = [pad_x]
    cum = 0.0
    for r in route[1:]:
        cum += float(r.get("km", 0))
        xs.append(pad_x + cum / total * (W - 2 * pad_x))
    rx = ' rx="1"' if archviz else ""
    seg = ""
    for i in range(1, len(route)):
        x0, x1 = xs[i - 1], xs[i]
        seg += '<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="2"/>' % (x0, y_mid, x1, y_mid, INK)
        km = route[i].get("km", "")
        hrs = route[i].get("hours", "")
        gain = route[i].get("gain")          # 段累计爬升(m) —— 骑行/徒步的第一性数据
        lbl = "%s km" % km if km != "" else ""
        if hrs != "":
            lbl += " · %sh" % hrs
        if gain not in ("", None):
            lbl += " · ↑%gm" % float(gain)
        seg += '<text x="%.1f" y="%d" fill="%s" font-size="10.5" font-family="%s" text-anchor="middle"%s>%s</text>' % ((x0 + x1) / 2, y_mid + 18, MUTED, FONT, _tnum(lbl), _esc(lbl))
        # 爬升的等效里程（§10：每 100m 爬升 ≈ +1km 等效努力）—— 仅在给了 gain 时提示
        if gain not in ("", None) and float(gain) >= 300:
            eff = float(gain) / 100.0
            seg += ('<text x="%.1f" y="%d" fill="%s" font-size="9" font-family="%s" '
                    'text-anchor="middle"%s>等效 +%gkm</text>') % (
                (x0 + x1) / 2, y_mid + 31, FAINT, FONT, _tnum(""), eff)
    nodes = ""
    for i, r in enumerate(route):
        x = xs[i]
        is_end = (i == len(route) - 1)
        fill = ACCENT if is_end else INK
        nodes += '<rect x="%.1f" y="%.1f" width="14" height="14" fill="%s"%s/>' % (x - 7, y_mid - 7, fill, rx)
        ty = y_mid - 18 if i % 2 == 0 else y_mid + 40
        nodes += '<text x="%.1f" y="%d" fill="%s" font-size="11.5" font-weight="700" font-family="%s" text-anchor="middle">%s</text>' % (x, ty, INK, FONT, _esc(r.get("name", "")))
        note = r.get("note")
        if note:
            nodes += '<text x="%.1f" y="%d" fill="%s" font-size="9.5" font-family="%s" text-anchor="middle">%s</text>' % (x, ty + 13, FAINT, FONT, _esc(note))
    svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" aria-label="路线示意">%s%s</svg>') % (W, H, seg, nodes)
    return _card("路线示意（累计里程）", svg)


def budget_chart(budget, archviz=False):
    if not budget:
        return ""
    items = [(_esc(b.get("label", "")), float(b.get("amount", 0))) for b in budget]
    total = sum(a for _, a in items)
    if total <= 0:
        return ""
    pad_x, H, bar_h = 20, 92, 30
    bar_w = W - 2 * pad_x
    rx = ' rx="1"' if archviz else ""
    x = pad_x
    segs = ""
    legend = ""
    for i, (lab, amt) in enumerate(items):
        w = amt / total * bar_w
        color = ACCENT if i == 0 else TINTS[i % len(TINTS)]
        segs += '<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"%s/>' % (x, 14, w, bar_h, color, rx)
        x += w
        pct = amt / total * 100
        legend += ('<span style="display:inline-flex;align-items:center;gap:6px;margin:4px 12px 0 0;font-size:11.5px;color:%s;font-family:%s">'
                   '<span style="width:10px;height:10px;background:%s;display:inline-block"></span>%s %g元 (%.0f%%)</span>') % (MUTED, FONT, color, lab, amt, pct)
    svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" aria-label="预算构成">'
           '%s<text x="%d" y="%d" fill="%s" font-size="11" font-family="%s"%s>合计约 %g 元（不含隐性支出）</text></svg>') % (W, H, segs, pad_x, H - 6, FAINT, FONT, _tnum(total), total)
    return _card("预算构成（参考/估算）", svg + '<div style="margin-top:8px">%s</div>' % legend)


def _elev_from_route(route):
    """从 route[].km / route[].m 推导海拔剖面采样点。

    这样 route 是唯一真源：给了 m 就不用再单独维护一份 elevation[]，
    消除「两处 km 必须人工对齐」的漂移风险。任一点缺 m 则整体不推导（宁可不出图）。
    """
    pts, cum = [], 0.0
    for i, r in enumerate(route or []):
        if i > 0:
            try:
                cum += float(r.get("km", 0) or 0)
            except (TypeError, ValueError):
                return []
        m = r.get("m")
        if m in ("", None):
            return []
        try:
            pts.append({"km": cum, "m": float(m)})
        except (TypeError, ValueError):
            return []
    return pts if len(pts) >= 2 else []


def elevation_chart(elevation, archviz=False):
    if not elevation or len(elevation) < 2:
        return ""
    kms = [float(e.get("km", 0)) for e in elevation]
    ms = [float(e.get("m", 0)) for e in elevation]
    pad_x, pad_y = 38, 24
    H = 200
    hw = 0.8 if archviz else 1
    kmin, kmax = min(kms), max(kms)
    mmin, mmax = min(ms) - 50, max(ms) + 50

    def X(k):
        return pad_x + (k - kmin) / (kmax - kmin) * (W - 2 * pad_x)

    def Y(m):
        return H - pad_y - (m - mmin) / (mmax - mmin) * (H - 2 * pad_y)

    grid = ""
    for g in range(int(mmin), int(mmax) + 1, 200):
        yy = Y(g)
        grid += '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="%.1f"/>' % (pad_x, yy, W - pad_x, yy, LINE, hw)
        grid += '<text x="%d" y="%.1f" fill="%s" font-size="10" font-family="%s"%s>%dm</text>' % (4, yy + 3, FAINT, FONT, _tnum(g), g)
    pts = " ".join("%.1f,%.1f" % (X(k), Y(m)) for k, m in zip(kms, ms))
    area = "M%.1f,%.1f L%s L%.1f,%.1f Z" % (X(kms[0]), H - pad_y, pts.replace(" ", " L"), X(kms[-1]), H - pad_y)
    line = '<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5"/>' % (pts, INK)
    fill = '<path d="%s" fill="%s" fill-opacity="0.12"/>' % (area, ACCENT)
    xticks = ""
    for k, m in zip(kms, ms):
        xticks += '<text x="%.1f" y="%d" fill="%s" font-size="9.5" font-family="%s" text-anchor="middle"%s>%dk</text>' % (X(k), H - 6, FAINT, FONT, _tnum(k), int(k))
    svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" aria-label="海拔剖面">%s%s%s%s</svg>') % (W, H, grid, fill, line, xticks)
    return _card("海拔剖面（参考）", svg)


def swimlane_chart(spec, archviz=False):
    """人员 × 日历泳道图 —— 多人并行行程（团队/家庭出行）。

    spec = {
      "dates":  ["5/28", ...],                     # 横轴日历
      "cities": {"杭州": "#c96442", ...},           # 类别配色（低饱和土色系）
      "phases": [{"at": "5/28", "label": "杭·论坛"}, ...],   # 顶部阶段带
      "lanes":  [{"person": "刘恩鹏", "hero": false,
                  "segments": [{"from": "5/28", "to": "5/29",
                                "label": "杭州论坛", "city": "杭州",
                                "muted": false}]}, ...],
      "notes":  [{"lane": "何璞", "at": "5/28", "label": "瑞丽→杭"}, ...],  # 无块的文字标注
      "verify": ["核验：...", "同行：..."]
    }

    单人行程不要用这张图（用 route_chart）；这张专治「多个人走不同路线」。
    """
    if not spec:
        return ""
    dates = spec.get("dates") or []
    lanes = spec.get("lanes") or []
    if len(dates) < 2 or not lanes:
        return ""

    cities = spec.get("cities") or {}
    phases = spec.get("phases") or []
    notes = spec.get("notes") or []
    verify = spec.get("verify") or []

    LEFT, COL, ROW, BAR, TOP = 118, 70, 40, 22, 76
    idx = {d: i for i, d in enumerate(dates)}
    W = LEFT + len(dates) * COL + 22
    H = TOP + len(lanes) * ROW + 26 + (len(verify) * 20 if verify else 0)

    def X(d):
        return LEFT + idx.get(d, 0) * COL

    o = ['<rect width="%d" height="%d" fill="%s"/>' % (W, H, PAPER)]

    # 日期标签 + 网格
    o.append('<g font-size="10" fill="%s" font-family="%s">' % (MUTED, FONT))
    for i, d in enumerate(dates):
        o.append('<text x="%d" y="26">%s</text>' % (LEFT + i * COL, _esc(d)))
    o.append('</g>')
    o.append('<g stroke="%s" stroke-width="0.6">' % LINE)
    for i in range(len(dates)):
        gx = LEFT + 30 + i * COL
        o.append('<line x1="%d" y1="38" x2="%d" y2="%d"/>' % (gx, gx, TOP + len(lanes) * ROW - 6))
    o.append('</g>')

    # 顶部阶段带
    if phases:
        o.append('<g font-size="11" font-weight="700" fill="%s" font-family="%s">' % (ACCENT, FONT))
        for p in phases:
            o.append('<text x="%d" y="52">%s</text>' % (X(p.get("at", dates[0])) + 4, _esc(p.get("label", ""))))
        o.append('</g>')

    # 泳道
    for r, lane in enumerate(lanes):
        y = TOP + r * ROW
        hero = lane.get("hero")
        name_fill = ACCENT if hero else INK
        star = " ★" if hero else ""
        o.append('<text x="12" y="%d" font-size="12" fill="%s" font-family="%s">%s%s</text>'
                 % (y + 14, name_fill, FONT, _esc(lane.get("person", "")), star))

        for seg in lane.get("segments") or []:
            f, t = idx.get(seg.get("from")), idx.get(seg.get("to"))
            if f is None or t is None or t < f:
                continue
            x = LEFT + f * COL
            w = (t - f + 1) * COL
            muted = seg.get("muted")
            color = cities.get(seg.get("city"), INK)
            o.append('<rect x="%d" y="%d" width="%d" height="%d"%s fill="%s" opacity="%s"/>'
                     % (x, y, w, BAR, ' rx="1"' if archviz else ' rx="2"',
                        color, "0.4" if muted else "0.88"))
            lab = seg.get("label", "")
            if lab:
                o.append('<text x="%d" y="%d" font-size="%s" fill="%s" font-family="%s">%s</text>'
                         % (x + 8, y + 15, "9" if len(lab) > 12 else "10",
                            INK if muted else "#F5F4ED", FONT, _esc(lab)))

    # 行内文字标注（无块的行程）
    for n in notes:
        li = next((i for i, l in enumerate(lanes) if l.get("person") == n.get("lane")), None)
        if li is None:
            continue
        o.append('<text x="%d" y="%d" font-size="9" fill="%s" font-family="%s">%s</text>'
                 % (X(n.get("at", dates[0])), TOP + li * ROW + 15, MUTED, FONT, _esc(n.get("label", ""))))

    # 核验行
    if verify:
        vy = TOP + len(lanes) * ROW - 6
        o.append('<line x1="118" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="0.8"/>'
                 % (vy, W - 22, vy, LINE))
        o.append('<g font-size="10" fill="%s" font-family="%s">' % (MUTED, FONT))
        for i, v in enumerate(verify):
            o.append('<text x="118" y="%d">%s</text>' % (vy + 20 + i * 20, _esc(v)))
        o.append('</g>')

    svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;height:auto" role="img" '
           'aria-label="人员与日历泳道">%s</svg>') % (W, H, "".join(o))
    title = spec.get("title") or "人员 × 日历泳道（多人行程）"
    # 泳道图比其它图宽，占满整行
    return ('<div class="viz-card" style="grid-column:1/-1"><h4>%s</h4>%s</div>'
            % (_esc(title), svg))


def _card(title, inner):
    return ('<div class="viz-card"><h4>%s</h4>%s</div>') % (_esc(title), inner)


def render_viz(d, archviz=False):
    """Return inner HTML (cards) for the visualization section, or '' if nothing.

    archviz=True adopts archviz-layout Type D (嵌入式数据可视化) + Swiss
    dual-track discipline: rx=1 bars, hairline <=0.8px, tabular-nums, single
    accent (roadbook red). It never swaps the palette.
    """
    parts = []
    if d.get("weather"):
        parts.append(temp_chart(d["weather"], archviz=archviz))
    viz = d.get("viz", {})
    if isinstance(viz, dict):
        if viz.get("route"):
            parts.append(route_chart(viz["route"], archviz=archviz))
        if viz.get("budget"):
            parts.append(budget_chart(viz["budget"], archviz=archviz))
        # 海拔剖面：优先用显式 elevation[]，否则从 route[].m 推导（route 为唯一真源）
        elev = viz.get("elevation") or _elev_from_route(viz.get("route") or [])
        if elev:
            parts.append(elevation_chart(elev, archviz=archviz))
        if viz.get("swimlane"):
            parts.append(swimlane_chart(viz["swimlane"], archviz=archviz))
    if not parts:
        return ""
    return '<div class="viz-grid">%s</div>' % "".join(parts)
