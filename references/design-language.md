# 路书精装版 · 设计语言细则

本文件是 `roadbook-beautify` 的视觉与质量基线，对应 Hsueh 的「包豪斯极简」审美与反 AI-slop 原则。

## 1. 设计哲学：瑞士国际主义排版（Swiss / International Typographic Style）

来源：Josef Müller-Brockmann 模块栅格 + Massimo Vignelli Canon。

- **模块栅格**：内容落在统一基线网格；时间轴 = 左列日期 / 中列轴线 / 右列内容的 3 列栅格。
- **左对齐字阶**：标题、标签、正文全部左对齐，不居中堆砌；靠字号/字重/字距建立层级。
- **限制色板**：墨黑 + 单一强调色，不引入第二、第三色相（阶段不靠多色区分，靠序号与字阶区分）。
- **发丝线（hairline）**：1px 浅灰分隔代替卡片阴影；扁平、无 `box-shadow`、无圆角投影。
- **留白即结构**：区块间大间距（section `margin-top:42px`）替代边框堆叠。

## 2. 设计令牌（tokens）

```
--ink:    #16140f   墨黑（主文字 / 序号块底）
--muted:  #6f6a60   次级文字
--faint:  #9a948a   注释 / 页脚
--paper:  #f6f5f1   暖白纸面（非纯白，带印刷感）
--card:   #ffffff   卡片底
--line:   #e0ddd6   发丝线
--rule:   #cfccc3   稍重分隔线（区块标题下划线）
--accent: #e0362b   朱红（唯一强调色：顶栏、CTA、时间轴点、序号、标签字）
--maxw:   760px     内容最大宽度
```

字体栈：`"Inter","Helvetica Neue","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif`。
（注：huashu-md-html 默认中文衬线；此处按用户包豪斯极简走 sans，遵循用户审美优先于通用默认。）

## 3. 反 AI-slop 硬约束（生成后必须过）

| 禁止 | 原因 |
|---|---|
| 紫渐变 / 赛博霓虹 | 套路化 AI 感 |
| `#0D1117` 暗底 | 暗色套路 + 本路书是白天户外场景 |
| emoji 图标（⚠️✈️🚗…） | 廉价；用 CSS 方块 `■` / 圆点 `●` / 序号代替 |
| 大圆角 + 重投影 | 非瑞士；扁平发丝线才是正解 |
| 多色阶段区分（蓝/绿/橙） | 违背单一强调色原则 |

> **例外 1：泳道图 `viz.swimlane`。** 多人多城市的泳道图里，「哪个城市」本身就是信息，
> 必须用色相区分。但只能用**低饱和土色系**——默认
> `#c96442`（杭州）/ `#8b7355`（南京）/ `#5c6b73`（北京）/ `#7a6a4f`（武汉），
> 即上面那条禁令针对的「蓝/绿/橙」**饱和度**，不是色相数量本身。
> **禁止彩虹色、禁止高饱和。** 其余所有图表仍守单一强调色（朱红 `#e0362b`）。
>
> **例外 2：路线海报 `build_poster.py`（独立产物，不是路书皮肤）。** 版式允许居中、双线外框、
> 胶囊圆角、核验印章——这些与瑞士纪律冲突，故放在独立脚本里，**不进** `build_swiss.py`。
> 强调色仍用路书红 `#e0362b`（单一强调）；详见 `references/design-language-print.md` 与 SKILL.md §7b。

**允许且鼓励**：序号 01–07 分区、字距标签（天气/景点/美食/门票/贴士）、细线时间轴、左对齐大标题、朱红单一强调。

## 4. 本机环境事实（实测，勿重复排查）

- `archviz-layout`、`huashu-md-html`：未安装。用户后续说「用 layout 优化」时先 `ls ~/.workbuddy-ai/skills/` 检测，装了就联动，没装走兜底。
- `guizang-ppt-skill`：ELOOP 符号链接环，且是 PPT 工具，不适配 HTML —— 永远跳过。
- `pandoc`：未安装（brew 大概率被代理拦）。huashu-md-html 的 `md_to_html.py` 依赖它，故文章流路线在本机不可用。
- 兜底路线：`scripts/build_swiss.py` 纯标准库、零网络、零外部依赖，任何环境都能跑。

## 5. 结构映射（itinerary JSON → 精装版）

| JSON 字段 | 精装版呈现 |
|---|---|
| title / eyebrow / title_lines / subtitle | masthead：朱红顶栏 + 字距 eyebrow + 大标题（次行降权） + lead |
| amap_uri | 朱红实心 CTA 按钮（唤起高德 App）+ 复制链接卡片 |
| weather[] | 2–3 列发丝线网格，大号温度数字 |
| stages[].stops[] | 时间轴：日期列 / 朱红圆点轴线 / 内容卡（名称 + 里程 + 天气/景点/美食/门票/贴士 标签行） |
| tickets[] | 细线表格，表头下双线 |
| clothing[] | 方块标记的分组卡 |
| tips[] | 序号列表，发丝线分隔 |
| checklist[]（可选） | 原生 checkbox（`accent-color` 朱红）+ 朱红字距组名 + 发丝线分隔；组首行墨色 2px 粗线（同门票表头）；已勾项转淡色加删除线；打印隐藏「清空勾选」 |
| footer（含 `<br>`） | 居中页脚，保留换行 |

## 6. 自检命令

```bash
# 0) 跑生成器
python3 scripts/build_swiss.py roadbook.json

# 1) 质量自检：emoji 残留 + 外部引用 + 四张 SVG 图表
python3 scripts/check_quality.py 输出.html
```

> **环境事实（实测，勿重复排查）**：本机**没有 `rg`（ripgrep）**，且 macOS 自带 BSD `grep`
> 既不支持 `\x{...}` 也不支持 `\|` 转义交替 —— 旧的 `grep -nE '[\x{1F000}-...]'` 会直接报
> `invalid character range`，被 `|| echo "OK"` 吞掉后**假阴性漏检**。
> 因此自检一律走 `scripts/check_quality.py`（纯标准库，零依赖）。

## 7. 数据可视化细则（viz 区块 · 联动 archviz-layout）

精装版 **04 数据可视化** 由 `scripts/build_viz.py` 生成 inline SVG，与整页同语言。令牌与 CSS 一致（定义在 `build_viz.py`）：

```
INK=#16140f  MUTED=#6f6a60  FAINT=#9a948a  LINE=#cfccc3  CARD=#ffffff
ACCENT=#e0362b  TINTS=[#16140f,#3a352d,#6f6a60,#9a948a,#cfccc3]
FONT="Inter,...PingFang SC...sans-serif"
```

**图表类型（数据驱动）**：沿途气温区间（来自 `weather[]`，恒渲染）· 路线示意（viz.route）· 预算构成（viz.budget）· 海拔剖面（viz.elevation）。任一数据缺失则静默跳过。

**archviz-layout 联动（已装时自动启用）**：采用其「类型 D 嵌入式数据可视化」+ 瑞士双轨纪律，对照自检：

| 纪律 | 实现 |
|---|---|
| 柱状 `<rect>` 边角 `rx="1"` | 预算条、路线节点方块 |
| 网格/轴线发丝线宽 ≤ `0.8px` | archviz=True 时 `hw=0.8`，否则 1 |
| 数值 `tabular-nums` 等宽对齐 | 温度/里程/预算/海拔数字均加 `font-variant-numeric:tabular-nums` |
| 单一强调色 | 路书红 `#e0362b`（父 skill 拥有调色板，**不**改为 terracotta / 电蓝）；辅助序列用墨色 tints |
| 禁 3D 柱 / 彩色饼图 | 仅扁平堆叠条、折线、面积；无透视、无多色扇区 |

**y 轴刻度密度（2026-10-07 修）**：刻度条数由**可用绘图高度**推出，**不写死步长**——`build_viz.py` 的 `_y_gridlines()` 取 `MIN_TICK_GAP_PX = 22`，步长在 `1/2/5 × 10^n` 阶梯上选，并**对齐到步长的整数倍**（轴上出现 1000 / 2000 / 3000，而不是 1050 / 2050 / 3050）。

写死步长会随数据跨度爆炸：成都→稻城海拔跨 3.6km，旧代码固定 200m 一档，在 152px 里塞了 **19 条刻度、间距 8.4px**，10px 的字直接叠死。气温图同源（固定 5° 一档，跨度 >40° 即触发，例如哈尔滨→三亚的行程）。

代价：整数倍对齐会让极窄跨度少一条线（示例 03/04 的气温图由 4 条变 3 条）。**不损失信息**——气温图每个数据点本身已直标数值，刻度只是读图参考。门禁 `check_quality.py` 第 9 项机械拦「相邻刻度 < 20px」。

**图表反 slop（与整页一致）**：禁渐变填充、禁投影、禁 emoji 轴标签、禁彩虹分类色；海拔/预算均为单强调色 + 灰阶 tints。SVG 视觉面积占比受控（4 张卡，单页内可读，不喧宾夺主）。

**兜底**：archviz-layout 不存在时，`build_swiss.py` 仍调 `render_viz(d, archviz=False)`，按相同令牌出图（发丝线 1px），交付不被阻塞。

**自检**：`python3 scripts/check_quality.py 输出.html` 覆盖九项（emoji / 外链 / 图表渲染 / slop / 注入噪声 / 重复 id / 占位符 / 长【】 / y 轴刻度叠字）；横向溢出由 `scripts/probe_layout.js` 单独查。
