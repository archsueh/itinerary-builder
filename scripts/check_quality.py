#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roadbook / poster / route-md quality gate — zero deps, stdlib only.

Checks for HTML modes (all must pass; exit 1 on any FAIL):
  1. no emoji residue            (anti-AI-slop, see references/design-language.md §3)
  2. no external refs except AMap URI   (page must stay self-contained)
  3. at least one inline-SVG chart rendered   (viz block present in JSON?)
  4. no AI-slop CSS patterns     (purple gradient / neon / #0D1117 dark bg)
  5. no data-attribute injection noise  (e.g. data-page-node-id)
  6. no duplicate id             (dup id = 元素/锚点互踩，导航与 JS 取错节点)
  7. no template placeholder residue    (TODO / __CITY__ / 【目的地】 / Lorem / FIXME)
  8. no long 【】 authoring instruction left in   (【…】≥15 字 = 填稿指引未删)
  9. y-axis ticks not colliding   (相邻刻度像素间距 ≥ 20px — 见 build_viz.py _y_gridlines)

6–8 借鉴自 awangwang123/jianhao-travel-planner 的 tools/checklist.py（MIT），
只取检查项思路，代码自写（其骨架/指纹/navLock/存储键等项与本 skill 架构无关，不搬）。

Why Python and not grep/rg: this machine has NO ripgrep, and macOS BSD grep
rejects both `\\x{...}` and `\\|` alternation — the old `grep -nE '[\\x{1F000}-...]'`
command errored out and got swallowed by `|| echo OK`, i.e. a silent false-negative.

Usage:
  python3 scripts/check_quality.py <output.html>                  # roadbook mode (default)
  python3 scripts/check_quality.py --poster <output.html>         # poster mode (build_poster.py)
  python3 scripts/check_quality.py --route-md <route.md> <data.json>
      # companion Markdown vs the same JSON the poster uses

"""
import json
import os
import re
import sys

EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
)

CHARTS = ("沿途气温区间", "路线示意", "海拔剖面", "预算构成", "泳道")

# 排版符号白名单：design-language.md §3 明确允许用它们代替 emoji
# （方块 / 圆点 / 星标 / 箭头 / 破折号），故不计入 emoji 残留。
ALLOWED_SYMBOLS = set("★☆●○■□◆◇▲▼△▽▪▫·×÷—–…→←↑↓")

SLOP_PATTERNS = (
    ("紫渐变", re.compile(r"(purple|violet|#7c3aed|#8b5cf6|linear-gradient\([^)]*13[0-9],\s*\d+,\s*2[0-9]{2})", re.I)),
    ("霓虹/发光", re.compile(r"(neon|glow|text-shadow:\s*0\s+0\s+\d+px)", re.I)),
    ("暗底 #0D1117", re.compile(r"#0d1117", re.I)),
)

# y 轴刻度标签：左侧留白区（x<40）里、内容是「数字 + m 或 °」的 <text>。
# 只有气温图（x=6）与海拔剖面（x=4）会产出这种节点。
AXIS_TICK = re.compile(r'<text x="(\d+)" y="([\d.]+)"[^>]*>-?[\d.]+[m°]</text>')
MIN_AXIS_GAP_PX = 20


def main_html(path, mode="roadbook"):
    with open(path, encoding="utf-8") as f:
        s = f.read()

    fails = []

    # 1) emoji
    emo = sorted({c for c in s
                  if any(lo <= ord(c) <= hi for lo, hi in EMOJI_RANGES)
                  and c not in ALLOWED_SYMBOLS})
    print("[%s] emoji 残留：%d %s" % ("FAIL" if emo else "OK", len(emo), "".join(emo[:8])))
    if emo:
        fails.append("emoji")

    # 2) external refs — only uri.amap.com / amapuri:// allowed.
    #    `http(s)://www.w3.org/...` 是 XML 命名空间标识符（SVG/XMLNS），不是网络请求，
    #    出现在 <svg xmlns> 或 favicon 的 data-URI 里属正常，必须白名单。
    ALLOWED_HOSTS = ("amap.com", "www.w3.org")
    urls = sorted(set(re.findall(r'https?://[^"\'\s)>]+', s)))
    bad = [u for u in urls if not any(h in u for h in ALLOWED_HOSTS)]
    print("[%s] 外部引用：%d 个，越界 %d %s" % ("FAIL" if bad else "OK", len(urls), len(bad), bad[:3]))
    if bad:
        fails.append("external-refs")

    # 3) charts —
    #    roadbook：至少一张命名图表（气温/路线/海拔/预算/泳道）。
    #    poster：不要求命名图表（海报是另一套产物），但必须有内联 <svg> 路线示意图，
    #            且带 data-poster 标记，避免把路书误跑成海报模式。
    if mode == "poster":
        has_svg = "<svg" in s
        has_mark = 'data-poster=' in s
        print("[%s] 海报 SVG：%s · data-poster：%s" % (
            "OK" if has_svg and has_mark else "FAIL",
            "有" if has_svg else "无",
            "有" if has_mark else "无"))
        if not has_svg:
            fails.append("poster-svg")
        if not has_mark:
            fails.append("poster-mark")
    else:
        found = [c for c in CHARTS if c in s]
        print("[%s] SVG 图表：%d 张已渲染 %s%s" % (
            "OK" if found else "FAIL", len(found),
            "、".join(found) if found else "（无）",
            " → 检查 JSON 的 viz 块" if not found else ""))
        if not found:
            fails.append("charts")

    # 4) slop
    for name, pat in SLOP_PATTERNS:
        hits = pat.findall(s)
        if hits:
            print("[FAIL] AI-slop：%s（%d 处）" % (name, len(hits)))
            fails.append(name)
    if not any(p.search(s) for _, p in SLOP_PATTERNS):
        print("[OK] AI-slop：无紫渐变 / 霓虹 / 暗底")

    # 5) injected attribute noise (keeps archived HTML clean)
    noise = len(re.findall(r'\sdata-page-node-id="[^"]*"', s))
    print("[%s] 注入属性噪声：%d 处" % ("FAIL" if noise else "OK", noise))
    if noise:
        fails.append("attr-noise")

    # 6) duplicate id — 重复 id 会让锚点跳错、JS 取到第一个节点
    ids = re.findall(r'id="([A-Za-z_-][\w-]*)"', s)
    dup = sorted({x for x in ids if ids.count(x) > 1})
    print("[%s] id 唯一：%d 个 id，重复 %d %s" % (
        "FAIL" if dup else "OK", len(ids), len(dup), dup[:5]))
    if dup:
        fails.append("dup-id")

    # 7) template placeholder residue
    ph = {k: s.count(k) for k in ("TODO", "FIXME", "__CITY__", "【目的地】", "Lorem") if s.count(k)}
    print("[%s] 占位符残留：%s" % ("FAIL" if ph else "OK", ph or "无"))
    if ph:
        fails.append("placeholder")

    # 8) long 【】 = authoring instruction left in.
    #    【估算】【未核实】这类短标注是合法产物，故只拦 ≥15 字的长【】。
    lb = re.findall(r"【[^】]{15,}】", s)
    print("[%s] 长【】指引残留：%d 处 %s" % (
        "FAIL" if lb else "OK", len(lb), lb[0][:24] + "…" if lb else ""))
    if lb:
        fails.append("bracket-instruction")

    # 9) y 轴刻度叠字 —— 相邻刻度的像素间距。
    #    刻度条数必须由**可用高度**推出来，不能写死步长：成都→稻城海拔跨 3.6km，
    #    写死 200m 就会在 152px 里塞 19 条刻度、间距 8.4px，10px 的字直接叠死
    #    （2026-10-07 实测，修复见 build_viz.py `_y_gridlines`）。
    tight = []
    for svg in re.findall(r'<svg\b.*?</svg>', s, re.S):
        ys = sorted(float(m.group(2)) for m in AXIS_TICK.finditer(svg) if int(m.group(1)) < 40)
        gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        if gaps and min(gaps) < MIN_AXIS_GAP_PX:
            tight.append(min(gaps))
    print("[%s] y 轴刻度间距：%s" % (
        "FAIL" if tight else "OK",
        ("最小 %.1fpx < %dpx → 叠字" % (min(tight), MIN_AXIS_GAP_PX)) if tight
        else "≥ %dpx" % MIN_AXIS_GAP_PX))
    if tight:
        fails.append("axis-tick-gap")

    print()
    if fails:
        print("FAIL — 未通过项：%s" % "、".join(fails))
        return 1
    print("PASS — 全部通过")
    return 0


# ---- route-md mode ---------------------------------------------------------

def _load_poster_nodes(data: dict):
    """Import the poster's collector so MD and HTML share one definition."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    from build_poster import _collect_nodes  # local import
    poster = data.get("poster") or {}
    if not isinstance(poster, dict):
        poster = {}
    return _collect_nodes(data, poster)


def _parse_frontmatter(md: str) -> tuple[dict, str]:
    if not md.startswith("---"):
        return {}, md
    end = md.find("\n---", 3)
    if end < 0:
        return {}, md
    block = md[3:end].strip("\n")
    body = md[end + 4:]
    meta = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta, body


def _yamlish_bool(v: str) -> bool | None:
    s = (v or "").strip().lower()
    if s in ("true", "yes", "1"):
        return True
    if s in ("false", "no", "0"):
        return False
    return None


def _yamlish_str(v: str) -> str:
    s = (v or "").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        try:
            return json.loads(s)
        except Exception:
            return s[1:-1]
    return s


def main_route_md(md_path: str, json_path: str) -> int:
    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    fails = []
    meta, body = _parse_frontmatter(md)

    poster = data.get("poster")
    if not isinstance(poster, dict) or not poster:
        print("[FAIL] JSON 缺少 poster{}")
        fails.append("no-poster")
        print()
        print("FAIL — 未通过项：%s" % "、".join(fails))
        return 1

    nodes = _load_poster_nodes(data)
    names = [n["name"] for n in nodes]
    name_set = set(names)

    # 1) cumulative monotonic + segment sum
    if len(nodes) < 2:
        print("[FAIL] 节点数 < 2")
        fails.append("nodes")
    else:
        prev = None
        mono_ok = True
        for i, n in enumerate(nodes):
            c = float(n["cum_km"])
            if prev is not None and c < prev:
                mono_ok = False
                print("[FAIL] 累计里程非单调：%s cum=%s < prev=%s" % (n["name"], c, prev))
                fails.append("cum-monotonic")
                break
            prev = c
        if mono_ok:
            print("[OK] 累计里程单调递增（%d 站）" % len(nodes))

        seg_sum = 0.0
        for i in range(1, len(nodes)):
            seg_sum += float(nodes[i]["cum_km"]) - float(nodes[i - 1]["cum_km"])
        end = float(nodes[-1]["cum_km"])
        if abs(seg_sum - end) > 1e-6:
            print("[FAIL] 分段之和 %.6g ≠ 终点累计 %.6g" % (seg_sum, end))
            fails.append("seg-sum")
        else:
            print("[OK] 分段之和 = 终点累计（%gkm）" % end)

    # 2) every place name appearing as a route node in the MD table must be in JSON
    #    Parse the 分段 table rows: "| n | A → B | seg | cum | note |"
    table_names = []
    for m in re.finditer(
        r"^\|\s*\d+\s*\|\s*([^|]+?)\s*→\s*([^|]+?)\s*\|",
        body,
        re.M,
    ):
        table_names.append(m.group(1).strip())
        table_names.append(m.group(2).strip())
    # Also the 节点 line at the bottom: "节点（与海报相同）：A → B → …"
    trail = re.search(r"节点（与海报相同）：(.+)", body)
    trail_names = []
    if trail:
        trail_names = [x.strip() for x in trail.group(1).split("→") if x.strip()]

    mentioned = set(table_names) | set(trail_names)
    # Overview start/end
    for m in re.finditer(r"^\|\s*(起点|终点)\s*\|\s*([^|]+?)\s*\|", body, re.M):
        mentioned.add(m.group(2).strip())

    extra = sorted(mentioned - name_set)
    missing_in_md = [n for n in names if n not in mentioned]
    print("[%s] 地名 ⊆ JSON：MD 出现 %d 个，越界 %d %s" % (
        "FAIL" if extra else "OK", len(mentioned), len(extra), extra[:5]))
    if extra:
        fails.append("place-not-in-json")

    # 3) poster HTML node set == MD node set (via shared JSON collector)
    #    Compare ordered lists from JSON (source of truth for both artifacts).
    if trail_names and trail_names != names:
        print("[FAIL] MD 节点序列与 JSON/海报不一致：%s vs %s" % (trail_names, names))
        fails.append("node-set-mismatch")
    elif missing_in_md:
        print("[FAIL] JSON 节点未出现在 MD：%s" % missing_in_md)
        fails.append("node-set-mismatch")
    else:
        print("[OK] 节点集合与 JSON/海报一致：%s" % " → ".join(names))

    # 4) tested: true forbidden unless verified_by == user
    vb = str(data.get("verified_by") or "none").strip().lower().replace("-", "_")
    if vb in ("", "unverified"):
        vb = "none"
    if vb in ("self",):
        vb = "user"
    if vb in ("author", "source"):
        vb = "source_author"
    if vb not in ("none", "user", "source_author"):
        # unknown → treat as none for the gate
        vb_eff = "none"
    else:
        vb_eff = vb

    tested_meta = _yamlish_bool(meta.get("tested", "false"))
    fm_vb = (meta.get("verified_by") or "").strip().lower()

    if tested_meta is True and vb_eff != "user":
        print("[FAIL] tested: true，但 JSON verified_by=%r（≠ user）——"
              "海报 stamp 不能升级为 tested" % data.get("verified_by"))
        fails.append("tested-without-user")
    else:
        print("[OK] tested 与 verified_by 一致（tested=%s, verified_by=%s）"
              % (tested_meta, vb_eff))

    if fm_vb and fm_vb != vb_eff and not (
        vb_eff == "none" and fm_vb in ("none", "unverified")
    ):
        print("[FAIL] frontmatter verified_by=%r ≠ JSON %r" % (fm_vb, vb_eff))
        fails.append("verified-by-mismatch")
    else:
        print("[OK] frontmatter verified_by 对齐 JSON")

    # 5) emoji residue in MD (same ranges; keep it sober)
    emo = sorted({c for c in md
                  if any(lo <= ord(c) <= hi for lo, hi in EMOJI_RANGES)
                  and c not in ALLOWED_SYMBOLS})
    print("[%s] emoji 残留：%d %s" % ("FAIL" if emo else "OK", len(emo), "".join(emo[:8])))
    if emo:
        fails.append("emoji")

    # 6) segment table: reconcilable with JSON cum diffs
    seg_rows = list(re.finditer(
        r"^\|\s*\d+\s*\|\s*([^|]+?)\s*→\s*([^|]+?)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|",
        body,
        re.M,
    ))
    if len(nodes) >= 2 and len(seg_rows) != len(nodes) - 1:
        print("[FAIL] 分段表行数 %d ≠ 节点相邻段数 %d"
              % (len(seg_rows), len(nodes) - 1))
        fails.append("seg-row-count")
    else:
        bad_seg = []
        for i, m in enumerate(seg_rows):
            a, b = nodes[i], nodes[i + 1]
            expect_seg = float(b["cum_km"]) - float(a["cum_km"])
            expect_cum = float(b["cum_km"])
            got_seg = float(m.group(3))
            got_cum = float(m.group(4))
            if abs(got_seg - expect_seg) > 1e-6 or abs(got_cum - expect_cum) > 1e-6:
                bad_seg.append(i + 1)
            if m.group(1).strip() != a["name"] or m.group(2).strip() != b["name"]:
                bad_seg.append(i + 1)
        if bad_seg:
            print("[FAIL] 分段表与 JSON 不一致：行 %s" % bad_seg)
            fails.append("seg-table")
        else:
            print("[OK] 分段表与 JSON 段距/累计一致（%d 段）" % len(seg_rows))

    print()
    if fails:
        print("FAIL — 未通过项：%s" % "、".join(fails))
        return 1
    print("PASS — 全部通过")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "roadbook"
    if args and args[0] == "--poster":
        mode = "poster"
        args = args[1:]
        if len(args) < 1:
            print(__doc__)
            sys.exit(2)
        sys.exit(main_html(args[0], mode=mode))
    if args and args[0] == "--route-md":
        args = args[1:]
        if len(args) < 2:
            print(__doc__)
            sys.exit(2)
        sys.exit(main_route_md(args[0], args[1]))
    if len(args) < 1:
        print(__doc__)
        sys.exit(2)
    sys.exit(main_html(args[0], mode=mode))
