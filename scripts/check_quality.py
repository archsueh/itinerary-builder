#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roadbook HTML quality gate — zero deps, stdlib only.

Checks (all must pass; exit 1 on any FAIL):
  1. no emoji residue            (anti-AI-slop, see references/design-language.md §3)
  2. no external refs except AMap URI   (page must stay self-contained)
  3. at least one inline-SVG chart rendered   (viz block present in JSON?)
  4. no AI-slop CSS patterns     (purple gradient / neon / #0D1117 dark bg)
  5. no data-attribute injection noise  (e.g. data-page-node-id)

Why Python and not grep/rg: this machine has NO ripgrep, and macOS BSD grep
rejects both `\\x{...}` and `\\|` alternation — the old `grep -nE '[\\x{1F000}-...]'`
command errored out and got swallowed by `|| echo OK`, i.e. a silent false-negative.

Usage:  python3 scripts/check_quality.py <output.html>
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


def main(path):
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

    # 3) charts — 至少一张。单线自驾出气温/路线/海拔/预算；团队出行只出泳道图，
    #    故不要求四张齐全，只要求「有图」，并列出实际渲染了哪些供人核对。
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

    print()
    if fails:
        print("FAIL — 未通过项：%s" % "、".join(fails))
        return 1
    print("PASS — 全部通过")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
