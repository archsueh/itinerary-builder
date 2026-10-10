# CHANGELOG — itinerary-builder

> 变更记录。**向后兼容性单独标注**，因为本 skill 的产物是要交付给人的 HTML，静默改变渲染结果 = 静默改交付物。

## 2026-10-11（日）— 配套 Markdown 路线文档 `build_route_md.py`

与海报共用同一份 `itinerary.json`（含 `poster{}`），生成可读的路线 Markdown，专门挡住手写文档里的地名/里程/亲测跑偏。

### 向后兼容性

✅ **对既有 JSON / 精装版 HTML / 海报 HTML 完全兼容**。
- `build_swiss.py` / `build_poster.py` **零改动行为**；示例 01–05 HTML 重建后**逐字节未变**。
- 新增可选字段 `verified_by` / `source`；缺省 = 未核实，不影响海报渲染。
- `check_quality.py` 默认与 `--poster` 模式不变；路线 MD 走 `--route-md`。

### 变更

- **新增 `scripts/build_route_md.py`**（纯标准库）：概览表 + 分段表（段距 = 相邻累计差）+ `poster.stats` 数据卡 + 标签 + 来源与核实。**不自造**路况/气温/设施。
- 核实口径：`verified_by` = `none` | `user` | `source_author`；**仅 `user` → `tested: true`**。`poster.stamp` 只服务海报，不能升级为已测。
- `scripts/check_quality.py` 增加 `--route-md <md> <json>`：累计单调、分段和、地名 ⊆ JSON、节点集与海报一致、未核实不得 `tested: true`。
- `scripts/build_examples.py` 增加 `ROUTE_MD_MAPPING` → `examples/05-poster-moto-day.md`。
- 样本：到达站 note 挂上「绿汁坡 72 拐」；`verified_by: none` + `source` 标明示例。
- 文档：`SKILL.md` §7b、`roadbook-spec.md`、`README.md`、本 CHANGELOG。

### 验证

- `build_examples.py --write` / `--check` → 全过（含路线 MD）
- 示例 01–05 HTML 与改前逐字节一致
- 故意错误样本（非单调累计 / 错地名 / 累计当分段 / 未核实却 `tested: true`）门禁均拒绝

---

## 2026-10-11（日）— 可选出口：单页 3:4 路线海报 `build_poster.py`

接入 `references/design-language-print.md` 的版式（逆推自摩旅海报），作为**独立产物**，不替换精装版路书。

### 向后兼容性

✅ **对既有 JSON / 精装版 HTML 完全兼容**。
- `build_swiss.py` / `build_viz.py` **零改动**；示例 01–04 重建后**逐字节未变**。
- `poster{}` 是可选字段；没有它时 `build_poster.py` 退出码 2，不碰精装版。
- `check_quality.py` 默认模式不变；海报走 `--poster`（要求内联 SVG + `data-poster`，不要求命名图表标题）。

### 变更

- **新增 `scripts/build_poster.py`**（纯标准库）：`itinerary.json`（含 `poster{}`）→ 单文件 3:4 竖版海报 HTML。
  - 顶栏 kicker / endpoints、大标题（`highlight` 强调色放大）、副标题、SVG 路线示意图、slogan、三格数据卡、胶囊标签、可选核验印章。
  - 路线节点优先复用 `viz.route[]`（段距累加）；可选 `poster.path`（0–1）或节点 `x/y` 微调形状；**不调地图 API、不联网**。
  - **色板取舍**：版式跟印刷风；强调色用路书红 `#e0362b`（单一强调），不用橙/砖红/灰橄榄三色。
- `scripts/check_quality.py` 增加 `--poster` 模式。
- `scripts/build_examples.py` 增加 `POSTER_MAPPING`（与路书 MAPPING 分开）。
- 样本 `assets/itinerary.poster.sample.json` → `examples/05-poster-moto-day.html`（**示例地名与里程，标明未经核实**）。
- 文档：`SKILL.md` §7b、`roadbook-spec.md`、`design-language.md` 例外 2、`design-language-print.md` §10、`README.md` 效果图。

### 为什么是独立脚本

海报与路书是两种产物（一页分享图 vs 多段可交互页），版式与瑞士纪律正面冲突。塞进 `build_swiss.py` 会重蹈「功能版」退役的覆辙（见 `design-language-print.md` §8 决策 1）。

### 验证

- `build_examples.py --write` / `--check` → **5/5**
- 示例 01–04 与改前逐字节一致
- `check_quality.py --poster examples/05-poster-moto-day.html` → PASS

---

## 2026-10-10（六）— 订单截图 / 邮件识别流程 + 可勾选出行清单 `checklist[]`

借鉴 Paths（trip.gopaths.ai）的两处做法，按本 skill 的「决策先定死 + 单文件离线」口径落地；
其多人协作、账号分享、对话改行程、实时天气等**不借**（要后端或违背两半不能混）。

### 向后兼容性

✅ **对既有 JSON 完全兼容**。`checklist[]` 是可选字段，**不给时不注入任何 HTML / CSS / JS**：
示例 01 / 02 / 03 重建后**逐字节未变**（`cmp` 一致）；`"checklist": []` 渲染结果也与示例 01 逐字节一致。
⚠️ 示例 04 **有变化**——是因为样本主动加了 `checklist[]`：新增 1 个 CSS 块、末尾第 10 分区「出行清单」、
1 个 `<script>`；前 9 个分区的字节未动。

### 变更

**① 订单截图 / 邮件识别（纯流程文字 + 契约口径，不写代码）**

- `SKILL.md` §2 新增「订单截图 / 邮件识别」：机票 / 火车票 / 酒店确认单 → **只抽取不推断** →
  列**待确认表**（字段 / 识别值 / 来源 / 置信）→ **用户确认后才写入**现有字段（`flights[]` / `stays[]` /
  `stops[].km`）→ 看不清的标「未核实」，不猜。
- **来源标注复用现有字段**，不新造 `source`：逐条写 `flights[].note` / `stops[].tips`，整份汇总写 `footer`
  （`references/roadbook-spec.md` 新增「字段来源标注」表）。
- **敏感信息不落盘**：完整订单号 / 票号 / PNR 只留后四位；证件号、手机号、付款卡号、他人全名一律不写。

**② 可勾选的出行清单 `checklist[]`**

- 契约：每项 `text`（必给，支持 `<br>`）+ 可选 `group` / `when`。`group` 相同的连续项自动归组
  （同 `flights[].leg` 的规则：按数组顺序、不排序）；缺 `text` 的项与非对象项跳过。
- `scripts/build_swiss.py`：注意事项之后插入「出行清单」分区（序号由 `_add()` 计数器给）。
  - 原生 `<input type="checkbox">` + `<label>` 整行可点；`accent-color` 用路书红，单一强调色不破。
  - **勾选状态只存本机 `localStorage`**：key = `roadbook-checklist:` + `sha1(title␟subtitle)[:10]`，
    条目用 `sha1(group␟text)[:8]` 定位而**不用数组下标**——改顺序、插新项不会把勾错位；
    `file://` 下多份路书共用一个 origin 时也互不串号。同组同文的重复项加 `-2` 后缀各自独立。
  - `localStorage` 不可用（隐私模式等）时静默降级为「本次打开有效」，不报错。
  - 「已完成 n / N」计数 + 「清空勾选」按钮；`@media print` 隐藏按钮、条目不跨页断开、保留勾选状态。
  - 不联网、不引外部库、无新 `id`（不碰门禁第 6 项）；纯标准库（新增 `hashlib`）。
- `references/booking-and-budget.md` §7：要逐项做完的动作改指向 `checklist[]`，§1 倒计时节点用 `when` 落进去；
  订单号「路书里只写后四位」。
- `assets/itinerary.flight.sample.json` 加 7 项 / 3 组清单（证件与凭证 / 出发前 48h / 随身行李），
  与 `tips[]` 分工：tips 讲「要知道什么」，checklist 列「要做完什么」，不整句重复。
- 文档同步：`SKILL.md` 契约表 + 「出行清单」一节、`roadbook-spec.md` 字段表、`README.md` 契约表与示例表、
  `design-language.md` 结构映射。

### 为什么不动 `build_viz.py`

它不是独立输出模板，而是 `build_swiss.py` 调用的**纯 SVG 图表函数**（`render_viz(d) -> html`），
只消费 `weather[]` 与 `viz{}`。清单是交互控件不是图表，放进去会破坏它「纯函数、与数据结构无耦合」的定位。

### 验证

- `build_examples.py --write` → 4/4 重建 + 门禁 PASS；随后 `--check` → **4/4 同步且过门禁**
- `check_quality.py` → **4/4 PASS**（9 项）；边界样本（无组项、重复项、`<br>`、`<script>` 被转义、缺 `text` 项、非对象项）PASS
- `probe_layout.js` → **4 示例 × 4 视口全 PASS**（box 上临时装 playwright，`NODE_PATH` 指过去跑）
- 行为实测（playwright，375px）：点文字可勾选 → 计数 `2 / 7` → `localStorage` 写入 → **刷新后状态保留** →
  清空后计数归零、key 移除；无页面报错、**零网络请求**；print 媒体下按钮隐藏，导出 PDF 勾选可见

### 已知边界

- `docs/screenshots/04-flight-*.png` 未重拍（不含新分区）——截图环境字体与本次验证机不同，重拍会引入无关差异。
- 勾选状态只在**同一台设备、同一浏览器**里有效；路书转发给同行者后各勾各的，这是刻意的（不联网）。

## 2026-10-09（五）— 新增可选出口：行程动画（map-motion 数据桥）

### 向后兼容性

✅ **完全向后兼容**。未改渲染器、未改数据契约、未改样本 ——
4 个入库示例 HTML **逐字节未变**（`build_examples.py --check` 全 PASS）。
新脚本是**新增的独立出口**，不被任何现有流程调用；不跑它，行为与之前完全一致。

### 变更

- **新增 `scripts/itinerary_to_motion.py`**（纯标准库、零依赖）：
  `itinerary.json` → [map-motion](https://github.com/SpaceZephyr/map-motion) 的镜头表 `spec.json`，
  把一份路书延伸成一段地图动效视频（MP4/GIF）。三个 profile 自动选：
  `ground`（title → trip → overview）/ `flight`（pins + flight）/ `mixed`（去程航线 + 地面行程）。
- `SKILL.md` 新增 **§7「可选出口：行程动画」**；「资产与脚本」表加一行。
- `references/amap-tools.md` 新增 **「两条高德通道，不要混」** ——
  本 skill 走**高德 MCP**（无需 key），map-motion 走**高德 REST**（需「Web服务」key），
  同一趟路会被算两遍，**数字可能有差**；纪律是各用各的，不要互相凑数。

### 为什么是「独立出口」而不是「并入」

map-motion 与本 skill **相邻但产出物不同**（MP4 vs HTML），且有两条硬冲突：

| 冲突 | 本 skill | map-motion |
|---|---|---|
| 依赖等级 | **零强依赖**（渲染兜底纯标准库） | `uv` + playwright chromium + ffmpeg |
| 架构原则 | **两半不能混**（决策 / 渲染） | 视频渲染是第三个关注点 |

并入 = 把「零依赖 HTML 生成器」改成「重依赖视频渲染器」。故采用**独立 skill + 单向数据桥**：
桥只搬**地名与日期**，里程/路线由 map-motion 用自己的通道重算，**不搬数字**。

### 实测（4 个入库样本）

| 样本 | profile | 镜头序列 | 关键字段 |
|---|---|---|---|
| `itinerary.sample.json` | ground | title → trip → overview | 4 站；`dates` 2 项；`elevation: true`（有 `m`） |
| `itinerary.bike.sample.json` | ground | title → trip → overview | 6 站（含闭环）；`elevation: true`；日序 `D1–D4` 不是日历日期 → 正确地不写 `dates` |
| `itinerary.team.sample.json` | ground | title → trip → overview | 无 `viz.route` → 退到 `stages.stops`；`km` 为 `—` → 不写里程；`「杭州 · 论坛」`→ 拆成 `{"name": ..., "at": "杭州"}` |
| `itinerary.flight.sample.json` | **mixed** | title → pins → flight → flight → trip → overview | 城市 厦门 → 上海 → 大阪（中转段「浦东 T1」按上一段到达城市推得）；地面 大阪/京都/东京 |

4 份 spec 均通过 map-motion `compile.py` 的契约解析（用假 key 跑，全部推进到地理编码那步才停）。
`trip.stops` 的对象形式 `{"name", "at"}` 经 `compile.py:305` 源码确认受支持。

## 2026-10-08（二）— 修 y 轴刻度密度（写死步长 → 按高度推导）；门禁 +1 项

### 向后兼容性

⚠️ **渲染结果有变**（不是静默改，故在此明写）：4 个入库示例的 HTML **字节全部变化**。
变的是 y 轴刻度线与刻度值，数据、布局、色彩、文字**均未变**。各示例的图表曲线逐点未动。

### 问题（实测，非推断）

**y 轴刻度步长写死在代码里，与数据跨度无关**：

| 图 | 旧步长 | 实测后果 |
|---|---|---|
| 海拔剖面 | 固定 **200m** | 成都→稻城跨 3.6km → **19 条刻度挤在 152px 里，间距 8.4px**，10px 的字直接叠死 |
| 沿途气温 | 固定 **5°** | 本批 4 个示例尚可（4–7 条）；**跨度 >40° 即触发**（如哈尔滨→三亚，13 条 → 间距 12px） |

旧代码还有个次要问题：刻度从 `int(mmin)` 起步 —— 数据派生的任意值，于是轴上出现
`1050 / 2050 / 3050` 这种读不出规律的数字。

### 变更

- `scripts/build_viz.py`
  - 新增 `MIN_TICK_GAP_PX = 22` / `_nice_step()` / `_y_gridlines()` / `_axis_num()`。
  - 步长在 `1/2/5 × 10^n` 阶梯上按**可用绘图高度**选取（**刻意不含 2.5**：会产出 25 / 250 这类不整的步长）。
  - 刻度值**对齐到步长的整数倍** → 轴上出现 1000 / 2000 / 3000。
  - 气温图与海拔剖面**共用**同一套逻辑（同源缺陷，只修一处等于留一颗雷）。
  - `_axis_num()` 不用 `%g`：超过 6 位有效数字它会切成科学计数法（`1000000` → `1e+06`）。
- `scripts/check_quality.py` **门禁 8 → 9 项**：新增「y 轴刻度叠字」——按 `<svg>` 分块取左侧留白区
  （`x<40`）的刻度标签，要求相邻间距 ≥ 20px。
- `references/design-language.md` 补「y 轴刻度密度」一节（含代价说明）；`SKILL.md` / `README.md` 门禁项数同步 9。

### 修复效果（实测）

| 图 | 旧 | 新 |
|---|---|---|
| 海拔·成都→稻城 | 19 条 / 8.4px / `450…4050` | **4 条 / 42.0px / `1000 2000 3000 4000`** |
| 海拔·环青海湖 | 6 条 / 26.6px / `2210…3210` | 5 条 / 26.6px / `2400…3200`（值变圆整） |
| 气温·示例 01 | 7 条 / 24.6px | **逐字节不变** |
| 气温·示例 02 | 5 条 / `-1,4,9,14,19` | 5 条 / `0,5,10,15,20`（值变圆整） |
| 气温·示例 03/04 | 4 条 | 3 条（整数倍对齐的代价，见下） |

**已知代价**：整数倍对齐会让极窄跨度少一条线（示例 03/04 气温图 4 → 3 条）。
判定为可接受 —— 气温图**每个数据点本身已直标数值**（柱顶 `27°` 等），刻度只是读图参考，
少一条线不损失信息；而整数倍刻度让轴「扫一眼能读」，收益更大。

### 验证

- `build_examples.py --check` → **4/4 同步且过门禁**（先确认它能侦测到漂移，再 `--write` 重建）
- `check_quality.py` → **4/4 PASS**；新第 9 项**正负例双向验证**：
  灌入 19 条 8.4px 刻度 → `FAIL axis-tick-gap`；正常示例 → `OK ≥ 20px`
- `probe_layout.js` → **4 示例 × 4 视口全 PASS**
- 各示例 diff **均为 1 行**（viz card 那一行），确认改动范围未外溢

## 2026-10-08（一）— 修复 `probe_layout.js` 的本机调用路径、缺依赖报错与 SVG 诊断

### 向后兼容性

**产物零影响**：不改渲染器、不改数据契约、不改任何 `examples/*.html` 的字节。
仅动 `scripts/probe_layout.js` 的依赖加载、诊断输出与文档，以及 `SKILL.md` / `README.md` 的调用说明。
**唯一对外契约变化是退出码**：新增 `3`（用法错误 / 崩溃），原先归入 `2` 的这两种情况改判 `3`；
CI 只判「非零即失败」，不受影响。

### 问题（本次实跑复现，非推断）

1. `scripts/probe_layout.js` 文档头**写死了**
   `/Users/mac/.workbuddy-ai/binaries/node/versions/22.22.2-3/bin/node`。
   **该路径已失效** —— 托管运行时重装时版本后缀会升（实测 `22.22.2-3` → `22.22.2-6`）。
   照着文档跑会报 `no such file or directory: .../bin/node`，看起来像脚本坏了。
2. `SKILL.md` / `README.md` 给的是裸 `node scripts/probe_layout.js`。
   本机裸 `node` 确实能解析到托管运行时，但**加载不到 playwright** → `MODULE_NOT_FOUND`。
   **这个报错极具误导性：看起来像环境缺依赖，实际是命令少了 `NODE_PATH`。**
   （上一轮就是在这里被绊住的，当时误判为「自己调用错了」，真因是文档给的命令在本机跑不通。）
3. 越界元素列表**对 SVG 元素完全失效**：用 `String(el.className)` 取 class，
   SVG 的 `className` 是 `SVGAnimatedString` **对象** → 打印成 `[object SVGAnimatedString]`。
   本 skill 的图表全是 inline SVG，越界元素多半正是它们 → **诊断信息在最需要时全废**。
   只在**有溢出时**才可见，所以正例（4 个示例全 PASS）永远暴露不出来。

### 变更

- `scripts/probe_layout.js`
  - 文档头改用 `versions/current` 解析版本目录，并注明**不要写死版本号**及其原因。
  - 新增 **fail-closed 依赖守卫**：`require('playwright')` 失败且 `code === 'MODULE_NOT_FOUND'` 时，
    打印「不是脚本坏了，是 NODE_PATH 没设」+ 本机正确命令 + 安装命令，**退出码 2**；其他异常照旧抛出。
  - **修 `[object SVGAnimatedString]`**：越界元素列表原用 `String(el.className)` 取 class，
    SVG 元素的 `className` 是 `SVGAnimatedString` **对象**，打印出来是一坨 `[object SVGAnimatedString]`。
    而本 skill 的图表**全是 inline SVG**——越界元素多半正是它们，等于诊断信息在最需要时全废。
    改用 `el.getAttribute('class')`（HTML/SVG 通吃）。**是在给本批次造溢出负例时暴露的**，
    正例（无溢出）永远看不到。
  - 退出码 `2` 与「用法错误 / 崩溃」解耦：后两者改判 **3**。原脚本把两者都记为 2，
    加上本批次把 2 定义成「缺 playwright」后，CI 日志会把脚本 bug 读成「环境没配好」。
- `SKILL.md` §6 给出本机精确调法（`versions/current` + `NODE_PATH`）；§资产表补退出码 2、3 的含义。
- `README.md` 命令块补 `NODE_PATH` 兜底写法与退出码说明（保持对外可移植，**不写死本机路径**）。

### 退出码约定（新增）

| 码 | 含义 |
|---|---|
| 0 | 全部视口无横向溢出 |
| 1 | 有溢出（列出越界元素） |
| **2** | **加载不到 playwright（`NODE_PATH` 未设，或本机未安装）** |
| **3** | **用法错误 / 未预期错误（崩溃）** |

### 验证

- `build_examples.py --check` → **4/4 同步且过门禁**
- `probe_layout.js` → **4 示例 × 4 视口全 PASS**
- 守卫**正负例双向验证**：不设 `NODE_PATH` → `rc=2` + 可操作提示；设了 → `rc=0`
- **退出码三态实测**：无 `NODE_PATH` → `2`；无参数 → `3`；人为 `nowrap` 溢出页 → `1`；正常示例 → `0`
- **SVG 诊断修复实测**：溢出页越界元素从 `class="[object SVGAnimatedString]"` 变为真实 class / 空串
- `node --check scripts/probe_layout.js`、`ast.parse(check_quality.py)` 语法通过

## 2026-10-07 — 借鉴 `jianhao-travel-planner`：门禁 +3 项、实查纪律 +4 条、速查卡前置

### 来源与合规

- 仓库：`awangwang123/jianhao-travel-planner`（见好 · 旅行规划器），**MIT**，
  评估日 218★ / 16 forks，`pushed_at` 2026-10-06（活跃）。
- 形态与本 skill 同类（AI agent 旅行路书 skill → 单文件 HTML），**但设计哲学不同**：
  它重信息完备（十板块 / 配图 / 发布），本 skill 重「决策先定死 + 瑞士排版 + 四张图表」。
- **评估结论：只读思路，不合并、不安装。** 合并会破坏本 skill「决策 / 渲染两半不能混」的架构。
- **合规**：只借鉴**规矩与检查项的思路**，**未移植任何文本、代码或模板**；其 `SKILL.md` 的
  版本演进史（50+ 版真实翻车实录）是本次最高价值的信息源，但属其作者的作品，不复制。
- 与本 skill 架构无关、故**不搬**的项：骨架 CSS 指纹 / navLock / 存储键跨成品污染 /
  配图对称律 / 价格切碎（双币种）/ 发布渠道与上线实测 —— 前几项对应它自己的骨架派生模型，
  本 skill 是 `itinerary.json` 单一事实源、无骨架派生、无配图、不发布。

### 变更

**① `scripts/check_quality.py` 门禁 5 项 → 8 项**

- `id 唯一` —— 重复 id 会让锚点跳错、JS 取到第一个节点（FAIL）
- `占位符残留` —— `TODO` / `FIXME` / `__CITY__` / `【目的地】` / `Lorem`（FAIL）
- `长【】指引残留` —— `【…】` ≥15 字视为填稿指引未删；**`【估算】`/`【未核实】` 等短标注合法，不受影响**（FAIL）

**② `SKILL.md` 新增「执行速查卡」（第一屏 5 条）**

- 上游实证：*「AI 制作时不深读 skill，埋在深处的条款等于不存在」*（其条款全文在副本里、
  制作时没翻，导致三次同类翻车）。本文件 20KB，故把 5 条最低限度约束前置到第一屏。

**③ `SKILL.md` §2 新增「实查纪律（四条）」**

- **止损点** —— 同一信息最多 2 轮，禁止循环死磕；验证码 / 风控一次即停手换路径
- **用户线索双向校验** —— 核实结果与用户记忆不符时如实回告，不硬凑用户期待
- **价格与时效的实时性** —— 按当前时点重查 + 每条价格带时戳与来源 + 官方源优先序
- **收录完备性差集核查** —— 交付前对照第三方热门路线做差集；核验查「写的对不对」，差集查「该写而没写」

**④ `SKILL.md` §4 新增「成稿语言纪律（两条）」**

- **相对时间禁令** —— 禁「今天 / 明天 / 现在」，一律绝对日期（路书提前交付、延后阅读，相对时间一过就变错）
- **信息归位一处** —— 每个信息只有一个家，跨区块禁整句复制，改一处漏一处就是前后矛盾

**⑤ `SKILL.md` §5 补一条本 skill 自身的真实缺陷**

- **`viz.route` 不得当地图读** —— 它是累计里程折线、不表达地理方位。此前**没有任何地方说明这一点**，
  读者会拿它判断方位。现要求在图题/图注写明；若确要表达方位，画前必须先对照真实地图核实
  （「示意图非等比」≠「方位可以随意」，画错比不画更害人）。

**⑥ `SKILL.md` §6 明确 fail-closed 语义**

- 任何 FAIL 不许交付；**任何未执行的检查必须向用户显式声明**——「没跑」不等于「通过」。

### 向后兼容性

**门禁变严，对既有产物是潜在破坏性变更**（此前通过、现在可能 FAIL）。已实测：
`build_examples.py --check` 的 4 个入库示例**全部仍 PASS**，新增三项零误伤。
三处新检查都只拦**真实缺陷**（重复 id / 模板占位符 / 未删的填稿指引），不含风格偏好。
`itinerary.json` 契约、渲染输出、示例 HTML **均无改动**。

## 2026-10-07 — 逆推「印刷复古风」设计语言（纯文档，**未接入渲染器**）

### 背景

用户提供一张摩旅海报（`1080×1440`，3:4，小红书竖版，「骑进80年代 · 小绿汁 134km 国道摩旅一日线」），
要求逆推并「补进 skill」。

逐项测量后判定：**它不是现有路书的换肤，是另一套设计语言**——与 `design-language.md` 的
五条核心纪律**四条正面冲突**（单一强调色 / 发丝线 / 全 sans / 无大圆角 / 左对齐）。
性质与当年退役的「功能版渲染器」相同，故**先记录语言，不接渲染器**。

### 新增

- `references/design-language-print.md`（9 节）：设计令牌（实测 hex）、版式几何（实测 px 与占宽比）、
  10 个组件清单、**路线图 8 层配方**、测量方法与原始读数、接入前的三个决策。

### 变更

- `SKILL.md` 资产表 +1 行，标注为「候选第二设计语言（未接入）」。

### 向后兼容性

**完全兼容。** 纯新增文档，无脚本改动，无契约改动，`build_examples.py --check` 与门禁不受影响。

### 关键测量结论（备查）

- 纸底 `#f4eede`（66.3%）· 墨 `#392b1e`（暖深棕，非纯黑）· 强调橙 `#d9561e` ·
  砖红 `#96442e` · 灰橄榄 `#bcb99a`。内容栏 `x 72–1007`（占宽 86.7%），双线外框（外 26-27 / 内 34）。
- **本语言没有绿色。** 目视以为的「绿树」经色相聚类（H 80–150° 仅 2px）+ 切图复核，
  确认是**三座小房子**（`#d9561e`/`#96442e`/`#bdb5a2`）。差点给一套语言补上不存在的颜色。
- 路线是**地图公路符号**：实心粗橙描边 + 沿中心线的纸色短划线 + 空心圆环节点 + 虚线引线，
  不是现有 `build_viz.py` 的「累计里程折线」。**两者是两张不同的图，非升级关系。**

## 2026-09-30 — 吸收第三方 `travel-planning` 的预订/预算知识（纯文档）

### 背景

本机从市场装了第三方 skill `travel-planning` v1.0.1（`~/.workbuddy-ai/skills/travel-planning/`，
`source=marketplace`），与本 skill 在「规划旅行」触发词上冲突。逐项比对后判定**两者不是同类**：

| | `travel-planning` | 本 skill |
|---|---|---|
| 本质 | 行程**管理器**（长期记忆 + 行前提醒 + 清单） | 行程**构建器 + 渲染器** |
| 产出 | markdown 文件，存 `~/travel-planning/` | 单文件 HTML 路书 |
| 代码 | 无（纯 md 指令） | 5 个脚本 + CI |

**决策：不合并。** 理由是形态不同（管家 vs 设计师，塞进一个 skill 违反「按能力命名」），
且它是第三方（有 `installedContentHash`，改动会被市场更新覆盖）。
**改为吸收其事务层知识后退役该 skill。**

### 新增

- `references/booking-and-budget.md` — 预订节奏与预算优化（7 节）：
  行前倒计时（T-90/60/45/30/14/7）、预订时机窗口、平季与旺季、省钱战术、
  签证与保险提前量、多城市与跨境衔接、出行前确认清单。

### 变更

- `SKILL.md` §1 末尾加一段：**日期确认后同步过一遍预订节奏**，把签证/护照作为硬期限前置检查
  （护照有效期 ≥ 返程日 +6 个月；复杂签证留 90 天以上）。
- `SKILL.md` 资产表 +1 行。
- `SKILL.md`「环境事实」表 +1 行：记录 `travel-planning` 已退役，避免以后重复排查/装回。

### 本土化改写（非照搬）

原 skill 是欧美视角，本文件全部重写：

- 「复杂签证」例子由「中国、俄罗斯、印度」改为**申根/美/英/加/澳**——对中文用户，中国签证不是问题；
- 「平季」由 Europe / Asia / Americas 三段改为**中国语境**（4–5 月、9–10 月）；
- 旺季由「Christmas / Golden Week」改为**春节 / 国庆 / 暑假**；
- 支付建议改按**出境人民币用户**的实际顺序（先换 20% → 当地 ATM → 免货转卡）。
- 另补原 skill 概览未提、但在其 `multi-city.md` 里的两条：**多城市最小停留规则**、**开口程机票**。

### 不吸收

长期记忆（`~/travel-planning/memory.md`）、打包清单模板、预算分类表模板、`travelers.md`。
前三者本 skill 已有替代（`tips[]` / `clothing[]` / `viz.budget[]`）；
长期记忆与「一次性交付一页路书」的定位冲突，属**刻意放弃**。

### 向后兼容性 ✅

**未触碰渲染器、契约、样本。** `build_swiss.py` / `build_viz.py` / `check_quality.py` 零改动，
`examples/*.html` 不需重建。本次是纯新增文档 + `SKILL.md` 文字。

---

## 2026-09-27（晚）— 发布为 GitHub 仓库 + 修复生成物不可复现

仓库上线：<https://github.com/archsueh/itinerary-builder>（MIT，public）。

### 修复：入库的渲染成品依赖本机状态，换机器就复现不出来

**症状**：本地 `build_examples.py --check` PASS，CI 上 4 个示例**全部**报「不同步」，
且都从**第 163 行**起（SVG 图表区）不同。

**根因**：`build_swiss.py` 用本机目录存在性决定渲染参数——

```python
ARCHVIZ = os.path.isdir(os.path.expanduser("~/.workbuddy-ai/skills/archviz-layout"))
```

本机装了 `archviz-layout` → `archviz=True`（柱状 `rx="1"`、发丝线 ≤0.8px）；
CI runner 上没有 → 退化成 1px 兜底。于是**入库的生成物只在这一台机器上复现得出来**。

**为什么这次才暴露**：以前 `examples/*.html` 不存在——渲染成品从没入过库，
一直是「本机跑一次给人看」。这次为了让 clone 下来不跑任何东西就能浏览，
把成品入了库并加了防漂移门禁，机器依赖才第一次变成可见问题。
**这正是把生成物入库时最该防的事，CI 抓对了。**

**修法**：加显式覆盖 `ROADBOOK_ARCHVIZ=1|0`，自动探测降级为兜底；
`build_examples.py` 渲染时**钉死 `ROADBOOK_ARCHVIZ=1`**，让入库成品与机器无关。
钉 `1` 而非 `0` 是为了与已发布的 `docs/screenshots/` 保持一致（截图是 archviz=True 下拍的）。

**验证**：
- `ROADBOOK_ARCHVIZ=0` 渲染 → 与已提交示例差 2 行，**恰好都在 `viz-grid` 内**，复现 CI 的失败签名；
- 钉死后 `--check` PASS；`probe_layout.js` 四视口零溢出（CI 该 job 本次本就通过）。

### 新增

- `README.md` — 含四张全页截图、契约表、设计哲学、双门禁说明
- `CONTRIBUTING.md`、`LICENSE`（MIT）、`.gitignore`、`.github/workflows/ci.yml`
- `scripts/build_examples.py` — `--write` 重建 / `--check` 防漂移，本地与 CI 共用一条命令
- `examples/*.html` — 4 份渲染成品（**生成物但入库**，供 clone 后直接浏览）
- `docs/screenshots/` — 430px 视口 ×2x 截图（全页 + 首屏各 4 张）
- `SKILL.md` frontmatter 补 `license: MIT` + `metadata.version` / `metadata.source`

### CI

两个 job：`gate`（示例同步 + 质量门禁，零依赖）、`layout`（Playwright 四视口布局探测）。
首次运行 `layout` 通过、`gate` 失败——即上述机器依赖问题，已修复。

### 隐私

`assets/itinerary.team.sample.json` 使用**真实姓名与真实航班/酒店**（7 人），
由当事人确认可公开。已在该样本 `_comment` 中显式标注，提醒复用者先自行匿名化。

---

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
