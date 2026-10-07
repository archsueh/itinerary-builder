# CHANGELOG — itinerary-builder

> 变更记录。**向后兼容性单独标注**，因为本 skill 的产物是要交付给人的 HTML，静默改变渲染结果 = 静默改交付物。

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
