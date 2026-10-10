#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roadbook HTML quality gate — zero deps, stdlib only.

Checks (all must pass; exit 1 on any FAIL):
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
  python3 scripts/check_quality.py <output.html>           # roadbook mode (default)
  python3 scripts/check_quality.py --poster <output.html>  # poster mode (build_poster.py)

"""
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


def main(path, mode="roadbook"):
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


if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "roadbook"
    if args and args[0] == "--poster":
        mode = "poster"
        args = args[1:]
    if len(args) < 1:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], mode=mode))
