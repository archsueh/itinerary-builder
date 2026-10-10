#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a companion Markdown route document from an itinerary JSON.

Usage:
    python3 scripts/build_route_md.py <data.json> [output.md]

If output is omitted, writes "<input>-路线.md" next to the input.

Why this exists
---------------
Hand-written route Markdown drifts from the poster: wrong place names,
cumulative km mistaken for segment km, technical points hung on the wrong
leg, invented weather/fuel notes, and someone else's "亲测" stamp copied as
`tested: true`. This script reads the **same** JSON the poster uses
(`poster{}` + `viz.route[]`), so the document and the poster cannot diverge
on nodes or mileage.

Verified status
---------------
`poster.stamp` is a decorative seal for the share image. It must NOT become
`tested: true` in the Markdown. Use top-level `verified_by`:

  - none / missing / unverified  → tested: false，文案「未核实」
  - user                         → tested: true，文案「用户亲测」
  - source_author                → tested: false，文案「来源作者亲测（注明来源）」

Optional `source` is free text citing where claims come from (same spirit as
footer / note provenance in roadbook-spec.md).

Stdlib only. No poster{} → exits 2. Invents nothing: segment notes are only
whatever the JSON already put on the destination stop's `note`.
"""
from __future__ import annotations

import json
import os
import sys

# Same node collection as the poster — keeps node sets identical.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_poster import _collect_nodes, _fmt_km, _num  # noqa: E402


VERIFIED_LABEL = {
    "none": "未核实",
    "unverified": "未核实",
    "": "未核实",
    "user": "用户亲测",
    "source_author": "来源作者亲测",
}


def _verified_by(d: dict) -> str:
    raw = d.get("verified_by")
    if raw is None or raw == "":
        return "none"
    return str(raw).strip().lower().replace("-", "_")


def _normalize_verified(v: str) -> str:
    if v in ("none", "unverified", ""):
        return "none"
    if v in ("user", "self"):
        return "user"
    if v in ("source_author", "author", "source"):
        return "source_author"
    # Unknown values are treated as unverified — never silently upgrade.
    return "none"


def _segments(nodes: list[dict]) -> list[dict]:
    """Adjacent pairs: segment_km = cum[i] - cum[i-1]; note from destination."""
    out = []
    for i in range(1, len(nodes)):
        a, b = nodes[i - 1], nodes[i]
        seg = float(b["cum_km"]) - float(a["cum_km"])
        out.append(
            {
                "from": a["name"],
                "to": b["name"],
                "seg_km": seg,
                "cum_km": float(b["cum_km"]),
                "note": (b.get("note") or "").strip(),
            }
        )
    return out


def _validate_nodes(nodes: list[dict]) -> list[str]:
    errs = []
    if len(nodes) < 2:
        errs.append("至少需要 2 个路线节点")
        return errs
    prev = None
    for i, n in enumerate(nodes):
        c = float(n["cum_km"])
        if prev is not None and c < prev:
            errs.append(
                "累计里程非单调递增：节点 %d「%s」cum_km=%s < 前一站 %s"
                % (i, n["name"], c, prev)
            )
        prev = c
    segs = _segments(nodes)
    total_seg = sum(s["seg_km"] for s in segs)
    end = float(nodes[-1]["cum_km"])
    if abs(total_seg - end) > 1e-6:
        errs.append(
            "分段之和 %.6g ≠ 终点累计 %.6g" % (total_seg, end)
        )
    return errs


def build(d: dict, *, source_path: str | None = None) -> str:
    poster = d.get("poster")
    if not isinstance(poster, dict) or not poster:
        raise ValueError(
            "缺少顶层 poster{} —— 路线 Markdown 与海报共用同一份数据；"
            "请在 itinerary.json 里加 poster 块"
        )

    nodes = _collect_nodes(d, poster)
    errs = _validate_nodes(nodes)
    if errs:
        raise ValueError("；".join(errs))

    v_raw = _verified_by(d)
    v = _normalize_verified(v_raw)
    if v_raw not in ("", "none", "unverified", "user", "self",
                     "source_author", "author", "source") and v_raw:
        # Unknown token: keep building but stay unverified; surface in source.
        pass

    tested = v == "user"
    # Hard gate inside the builder: stamp must never flip tested on.
    # (check_quality --route-md also enforces this against the written file.)

    title = (
        poster.get("title")
        or "".join(d.get("title_lines") or [])
        or d.get("title")
        or "路线文档"
    )
    subtitle = poster.get("subtitle") or d.get("subtitle") or ""
    tags = list(poster.get("tags") or [])
    tags_clean = []
    for t in tags:
        s = str(t).strip()
        if not s:
            continue
        tags_clean.append(s[1:] if s.startswith("#") else s)

    source = (d.get("source") or "").strip()
    mileage_source = (d.get("mileage_source") or "").strip()
    footer = (
        (poster.get("footer") or d.get("footer") or "").strip()
    )

    start = nodes[0]["name"]
    end = nodes[-1]["name"]
    total_km = float(nodes[-1]["cum_km"])
    segs = _segments(nodes)

    v_label = VERIFIED_LABEL.get(v, "未核实")
    if v == "source_author" and source:
        v_label = "来源作者亲测（%s）" % source
    elif v == "source_author":
        v_label = "来源作者亲测（须在 source 注明出处）"

    # --- frontmatter ---
    fm_tags = ", ".join(json.dumps(t, ensure_ascii=False) for t in tags_clean)
    lines = ["---"]
    lines.append('name: %s' % json.dumps("%s · 路线文档" % title, ensure_ascii=False))
    lines.append('title: %s' % json.dumps(title, ensure_ascii=False))
    desc = subtitle or ("%s → %s · %s" % (start, end, _fmt_km(total_km)))
    lines.append('description: %s' % json.dumps(desc, ensure_ascii=False))
    if tags_clean:
        lines.append("tags: [%s]" % fm_tags)
    else:
        lines.append("tags: []")
    lines.append("tested: %s" % ("true" if tested else "false"))
    lines.append("verified_by: %s" % v)
    if source:
        lines.append("source: %s" % json.dumps(source, ensure_ascii=False))
    if source_path:
        lines.append(
            "generated_from: %s"
            % json.dumps(source_path, ensure_ascii=False)
        )
    lines.append("---")
    lines.append("")

    # --- body ---
    lines.append("# %s" % title)
    lines.append("")
    if subtitle:
        lines.append("> %s" % subtitle)
        lines.append("")
    lines.append(
        "> 核实状态：**%s**。本文件由 `build_route_md.py` 从 itinerary JSON 生成；"
        "地名与里程只来自 JSON，脚本不补写路况、气温或设施。"
        % v_label
    )
    lines.append("")

    lines.append("## 行程概览")
    lines.append("")
    lines.append("| 项目 | 详情 |")
    lines.append("|---|---|")
    lines.append("| 起点 | %s |" % start)
    lines.append("| 终点 | %s |" % end)
    lines.append("| 全程累计 | %s |" % _fmt_km(total_km))
    lines.append("| 核实状态 | %s |" % v_label)
    if mileage_source:
        lines.append("| 里程口径 | %s |" % mileage_source)
    if source:
        lines.append("| 来源 | %s |" % source)
    lines.append("")

    lines.append("## 分段")
    lines.append("")
    lines.append(
        "分段里程 = 相邻累计之差；累计里程 = 从起点到该站。"
        "备注只取自 JSON 里**到达站**的 `note`，无则留空。"
    )
    lines.append("")
    lines.append("| 段 | 起 → 止 | 分段 km | 累计 km | 备注 |")
    lines.append("|---|---|---|---|---|")
    for i, s in enumerate(segs, 1):
        note = s["note"] or "—"
        lines.append(
            "| %d | %s → %s | %s | %s | %s |"
            % (
                i,
                s["from"],
                s["to"],
                _fmt_km(s["seg_km"]).replace("km", ""),
                _fmt_km(s["cum_km"]).replace("km", ""),
                note,
            )
        )
    lines.append("")

    stats = poster.get("stats") or []
    if stats:
        lines.append("## 数据卡")
        lines.append("")
        lines.append("来自 `poster.stats`（与海报三格数据卡同源）：")
        lines.append("")
        lines.append("| 数值 | 说明 |")
        lines.append("|---|---|")
        for st in stats:
            if not isinstance(st, dict):
                continue
            val = st.get("value") or st.get("v") or ""
            label = st.get("label") or st.get("text") or ""
            lines.append("| %s | %s |" % (val, label))
        lines.append("")

    if tags_clean:
        lines.append("## 标签")
        lines.append("")
        lines.append(" ".join("#" + t for t in tags_clean))
        lines.append("")

    lines.append("## 来源与核实")
    lines.append("")
    lines.append(
        "- `verified_by` = `%s` → %s。"
        % (v, v_label)
    )
    lines.append(
        "- `poster.stamp` 只服务海报版式，**不会**把本文的 `tested` 写成 true。"
    )
    if source:
        lines.append("- source：%s" % source)
    if mileage_source:
        lines.append("- mileage_source：%s" % mileage_source)
    if footer:
        # strip simple HTML breaks for markdown
        foot = footer.replace("<br>", " / ").replace("<br/>", " / ").replace("<br />", " / ")
        lines.append("- footer：%s" % foot)
    lines.append(
        "- 节点（与海报相同）：%s"
        % " → ".join(n["name"] for n in nodes)
    )
    lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = sys.argv[1]
    out = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.splitext(src)[0] + "-路线.md"
    )
    with open(src, "r", encoding="utf-8") as f:
        d = json.load(f)
    # Prefer a repo-relative path in frontmatter when possible.
    rel = src
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel = os.path.relpath(os.path.abspath(src), root)
    except Exception:
        pass
    try:
        md = build(d, source_path=rel)
    except ValueError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("WROTE %s  %d chars / %d bytes" % (out, len(md), os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
