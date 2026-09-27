#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build (or verify) the committed examples from the sample JSONs.

Why this exists
---------------
`examples/*.html` are **generated** artifacts committed to the repo so that a
clone is browsable without running anything. Generated files drift silently:
someone edits `assets/itinerary.sample.json`, forgets to re-render, and the
example on GitHub keeps showing the old contract. That is exactly the failure
this script prevents — it is the repo's anti-drift gate.

Modes
-----
  --write   re-render every example from its sample and run the quality gate
  --check   render to a temp dir, diff against the committed example, and run
            the quality gate. Exits 1 if anything is stale or fails. (CI default)

Usage
-----
  python3 scripts/build_examples.py --write
  python3 scripts/build_examples.py --check

Zero deps, stdlib only. The layout probe (`scripts/probe_layout.js`) is a
separate, heavier check that needs Node + Playwright — CI runs it as its own
job; see .github/workflows/ci.yml.
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (sample json, committed example html)
MAPPING = [
    ("assets/itinerary.sample.json", "examples/01-selfdrive-chengdu-daocheng.html"),
    ("assets/itinerary.bike.sample.json", "examples/02-bike-qinghai-lake.html"),
    ("assets/itinerary.team.sample.json", "examples/03-team-swimlane.html"),
    ("assets/itinerary.flight.sample.json", "examples/04-flight-japan.html"),
]

# The renderer stamps nothing time-dependent, so a byte comparison is valid.
# If that ever stops being true, compare a normalised form here instead.
_STYLE_RE = re.compile(r"<style>.*?</style>", re.S)

# Pin the archviz hook. `build_swiss.py` otherwise auto-detects
# ~/.workbuddy-ai/skills/archviz-layout, which makes its output depend on
# machine-local state — and a committed artifact that only reproduces on one
# machine is worse than no artifact. CI caught exactly this: every example
# diverged from line 163 (the SVG charts) on a runner without the skill.
# Pinning to "1" also keeps the examples matching docs/screenshots/.
RENDER_ENV = dict(os.environ, ROADBOOK_ARCHVIZ="1")


def render(sample, out):
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "build_swiss.py"),
         os.path.join(ROOT, sample), out],
        capture_output=True, text=True, cwd=ROOT, env=RENDER_ENV,
    )
    if r.returncode != 0:
        raise RuntimeError("render failed for %s:\n%s" % (sample, r.stderr.strip()))
    return r.stdout.strip()


def gate(path):
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "check_quality.py"), path],
        capture_output=True, text=True, cwd=ROOT,
    )
    return r.returncode == 0, r.stdout.strip()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if mode not in ("--write", "--check"):
        print(__doc__)
        return 2

    fails = []
    tmpdir = tempfile.mkdtemp(prefix="itinerary-examples-")

    for sample, example in MAPPING:
        sample_p = os.path.join(ROOT, sample)
        example_p = os.path.join(ROOT, example)
        name = os.path.basename(example)

        if not os.path.exists(sample_p):
            print("[FAIL] %-40s 样本缺失 %s" % (name, sample))
            fails.append(name + " (missing sample)")
            continue

        target = example_p if mode == "--write" else os.path.join(tmpdir, name)
        try:
            render(sample, target)
        except RuntimeError as e:
            print("[FAIL] %-40s %s" % (name, e))
            fails.append(name + " (render)")
            continue

        ok, out = gate(target)
        tail = [l for l in out.splitlines() if l.strip()][-1] if out else "(no output)"
        if not ok:
            print("[FAIL] %-40s 门禁未过：%s" % (name, tail))
            fails.append(name + " (gate)")
            continue

        if mode == "--write":
            print("[WROTE] %-40s %s" % (name, tail))
        else:
            if not os.path.exists(example_p):
                print("[FAIL] %-40s 示例未提交" % name)
                fails.append(name + " (untracked)")
                continue
            fresh = open(target, encoding="utf-8").read()
            committed = open(example_p, encoding="utf-8").read()
            if fresh != committed:
                # Report the first differing line so the fix is obvious.
                fa, cb = fresh.splitlines(), committed.splitlines()
                i = next((k for k in range(min(len(fa), len(cb))) if fa[k] != cb[k]), None)
                detail = "第 %d 行起不同" % (i + 1) if i is not None else "长度不同"
                print("[FAIL] %-40s 示例与样本不同步（%s）" % (name, detail))
                fails.append(name + " (stale)")
                continue
            print("[OK]   %-40s 同步 · %s" % (name, tail))

    print()
    if fails:
        print("FAIL — %d 项未通过：%s" % (len(fails), "、".join(fails)))
        if mode == "--check":
            print("      （本地跑 `python3 scripts/build_examples.py --write` 重新生成后提交）")
        return 1
    print("PASS — %d 个示例全部%s" % (len(MAPPING), "已重建" if mode == "--write" else "同步且过门禁"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
