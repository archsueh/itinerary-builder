# CHANGELOG — itinerary-builder

> 变更记录。**向后兼容性单独标注**，因为本 skill 的产物是要交付给人的 HTML，静默改变渲染结果 = 静默改交付物。

## 2026-09-27 — 出境/航班支持 + weather 契约放宽

**动机**：从一张日本行程设计稿倒推对照，发现本 skill 有三处结构性缺口——① 航班没有归属字段；
② 报头缺「路线一行摘要」与「住宿一览」；③ `weather[]` 强制 `city` + 数值温度，导致
乐园格（USJ）、风险格（TYPHOON）无法表达。同时 `build_viz.py` 把非数值格当 `0` 处理，
会把气温图纵轴下限拽到冰点。

### 新增字段（全部可选，不给则整节不出现）

| 字段 | 位置 | 说明 |
|---|---|---|
| `route_line` | 报头 | 一行路线摘要，纯文本，渲染器不做推导 |
| `stays[]` | 报头 | `name`/`nights`/`status`，渲染成「住宿 A ×3 晚 ｜ B ×1 晚」 |
| `flights[]` | 新增「航班时间线」分区 | `leg`/`date`/`no`/`from`/`to`/`dep`/`arr`/`dur`/`pax`/`note`；`leg` 相同值自动归组 |

### 变更字段

- `weather[]` 契约放宽：
  - 主标签取 `city`，**缺省回退 `label`**（原来 `city` 是硬要求）；
  - 副标签 `label` **只在给了 `city` 时渲染**（避免与主标签重复）；
  - 新增 `temp` 自由文本，**优先级高于 `day`/`night`**，可写 `"25°/19°"` 或 `"—"`；
  - `day`/`night` 都缺失时温度位渲染 `—`，不再输出空 `<b></b>`；
  - `text` 支持 `<br>` 分两行。

### 修复

- **`build_viz.py` 非数值天气格被当 0 处理** → 新增 `_num()`，`temp_chart` 只收 `day`/`night`
  都能转数字的格子，**整格跳过**其余；并加纵轴最小跨度保护（`tmax - tmin < 6` 时撑到 6），
  避免只剩一格时图形退化。
- **空 `<small>` 幽灵间距**：非城市格的副标签为空时不再发 `<small>` 元素
  （空块仍吃 `.wk-city small` 的 `margin-top:2px`）。
- `check_quality.py` docstring 第 8 行「the 4 inline-SVG charts rendered」与实现不符
  （实现早已是「至少一张」，团队样本只出泳道图）→ 校正为 `at least one`。
- `build_swiss.py` 收尾日志 `WROTE … <n> bytes` 报的其实是**字符数**——
  中文按 UTF-8 占 3 字节，同一次输出会显示 `25183 bytes` 而磁盘上是 `28015 bytes`，
  看起来像写坏了。改为两个都报：`WROTE <path>  <chars> chars / <bytes> bytes`。

### 渲染器内部改动

- 章节编号从硬编码 `01`–`08` 改为 `_sec()` / `_add()` 注册表计数——
  新增「航班时间线」后自动重排为 `01`–`09`，不需要手改模板。
- 新增 CSS 块：`.route-line` / `.stays` / `.stays-lab` / `.fl-leg` / `.fl-row` /
  `.fl-date` / `.fl-main` / `.fl-route` / `.fl-dur` / `.fl-meta`。

### 文档

- `SKILL.md`：契约表 +3 行、新增「天气契约」「航班」两节、§2 核实 +1 条（出境航班时刻/中转/直挂）、
  §3 质疑表 +1 行（出境/跨时区）、资产表 +1 行、frontmatter description 补出境触发词。
- `references/roadbook-spec.md`：字段表 +3 行、`weather[]` 行重写、门禁口径「四张 SVG」→「至少一张 SVG」。
- `references/planning-rules.md` §11「出境游」扩写：时差必须落到具体时刻、同一 `leg` 航段耗时
  相加须等于总行程、联程/直挂核实、多人不同机、次日凌晨落地不算一天。

### 新增资产

- `assets/itinerary.flight.sample.json` — 出境样本（大阪进东京出 7 天 6 晚），
  演示全部四个新字段 + 非城市天气格。**所有数值为示例值，未经核实**，文件内 `_comment` 已声明。
- `scripts/probe_layout.js` — **布局体检门禁**（需 playwright，本机已装）。
  在 320/375/430/768 四个视口量 `scrollWidth` vs `clientWidth` 并列出越界元素，退出码 1 = 有溢出。
  补的是 `check_quality.py` 的盲区：那个脚本只能看文本，**看不到布局**——
  路书是在手机上打开的，一个没加 `min-width:0` 的 grid 就会让整页左右能拖，
  表现为「右边被切掉」，而 HTML 完全合法。
  > 反向验证过：人为注入一个 900px 宽的 `nowrap` 块 → 正确报 FAIL 并定位到该元素。
  > 为什么不用 Chrome 无头截图目测：`--window-size=430 --force-device-scale-factor=2`
  > 出的图会**假性裁切**（右侧看似被切、还出现一条红色竖线），页面其实没溢出。
  > 本次实际踩了这个坑，差点误报成布局 bug。**量 DOM，不要看图。**

### 向后兼容性 ✅ 已验证

三个既有样本（`itinerary.sample.json` / `itinerary.bike.sample.json` / `itinerary.team.sample.json`）
在新旧渲染器下**逐字节一致**（唯一差异是新增的 CSS 规则块，不影响既有选择器）。

| 样本 | 旧 | 新 | 判定 |
|---|---|---|---|
| `itinerary.sample.json` | 33217 B | 33217 B | IDENTICAL |
| `itinerary.bike.sample.json` | 31072 B | 31072 B | IDENTICAL |
| `itinerary.team.sample.json` | 27250 B | 27250 B | IDENTICAL |
| `itinerary.flight.sample.json` | — | 28015 B | 新样本 |

四样本 `check_quality.py` 全部 PASS。渲染时在 430px 视口实测**零横向溢出**
（`scrollWidth == clientWidth == 430`，越界元素 0 个）。

### 已知边界

- `flights[].dur` 是自由文本，**渲染器不做时区运算**——跨时区的落地时刻由规划阶段算好后填入 `arr`。
  这是刻意的：让机器猜时区比让人写错更危险（错误会被当成事实渲染出去）。
- 航空段**只进 `flights[]`**，不进 `viz.route[]`。混进去会把地面路线图压扁
  （3000km 航段 vs 515km 新干线）。样本 `_comment` 已声明此约定。
- 未做：多页/封面式路书、衬线标题、把泳道土色提升为页面主强调色——三者都与本 skill 既定的
  包豪斯身份（单页滚动 / 无衬线 / 单一朱红 `#e0362b`）冲突，见 `references/design-language.md`。

---

## 2026-09-24 — 三 skill 合并

`travel-roadbook`（规划+渲染）与 `roadbook-studio`（呈现层）退役并合并进本 skill，
决策（§1–§4）与渲染（`build_swiss.py` / `build_viz.py` / `check_quality.py`）同处一库。
同期「功能版」渲染器（蓝黑圆角卡片风格）退役。
