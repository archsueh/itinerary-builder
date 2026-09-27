# Contributing

Thanks for your interest. This repo is a single skill, not a template gallery — the
scope is deliberately narrow: **plan a trip that holds up, then render one page you
can carry on a phone.**

## The two halves are not negotiable

```
需求澄清 → 核实 → 质疑 → 论证(decisions) → itinerary.json → 渲染 HTML → 门禁 → 交付
   §1       §2     §3      §4              §5               §6        §8     §8
```

Planning decides **what** and **why**; rendering only consumes the result. A PR that
makes the renderer re-order stops, re-derive mileage, or invent a rationale is out of
scope — that logic belongs in the planning half, and the two must not blur.

## Before you open a PR

```bash
# 1. Re-render the examples and run the quality gate on each
python3 scripts/build_examples.py --write

# 2. Layout probe — a roadbook is opened on a phone
npm install --no-save playwright && npx playwright install chromium
node scripts/probe_layout.js examples/01-selfdrive-chengdu-daocheng.html

# 3. Confirm nothing drifted
python3 scripts/build_examples.py --check
```

`examples/*.html` are **generated but committed** so a clone is browsable without
running anything. If you touch `assets/*.sample.json` or `scripts/build_swiss.py` and
forget step 1, CI fails — that is intentional. Never hand-edit `examples/`.

## Guidelines

- **Single accent, no exceptions.** `#e0362b` is the only accent on the page. The
  swimlane chart is the sole place categorical hues are allowed, and only from the
  low-saturation earth set (`#c96442` / `#8b7355` / `#5c6b73` / `#7a6a4f`). No rainbow.
- **Numbers are numbers.** A field the renderer draws must carry a bare number, not
  `"约340km"`. If a chart cannot be drawn, skip the chart — do not fake a value.
- **Do not fabricate.** Mileage, weather, ticket prices must come from a tool or a
  traceable source. Unknown is written as unknown and marked in `footer`.
- **Zero runtime deps.** `build_swiss.py`, `build_viz.py` and `check_quality.py` are
  stdlib-only by design, and the output HTML is self-contained (no CDN, no chart
  library). The only allowed external reference in an output page is the AMap URI.
- **Samples are the contract.** Every field in `references/roadbook-spec.md` must be
  exercised by at least one `assets/*.sample.json`, and vice versa. Adding a field
  without a sample that proves it renders is not a complete change.

## Adding a field

1. Add it to the renderer and make it **optional** — absent field ⇒ section omitted,
   never a broken layout.
2. Prove backward compatibility: render every pre-existing sample with the old and new
   renderer and diff. They must be byte-identical apart from added CSS rules.
3. Add a sample that exercises it (or extend an existing one).
4. Sync `SKILL.md` (contract table + any prose section), `references/roadbook-spec.md`,
   and `references/planning-rules.md` if it changes planning behaviour.
5. Append to `CHANGELOG.md` with an explicit **backward-compatibility verdict**.
6. `python3 scripts/build_examples.py --write` and commit the regenerated examples.

## Reporting issues

Include: the input JSON (or the shape of it), the exact command, what you expected,
what came out, and whether `check_quality.py` / `probe_layout.js` passed. A failing
gate output pasted verbatim is worth more than a description of it.
