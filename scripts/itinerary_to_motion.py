#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""itinerary.json  →  map-motion 镜头表 spec.json

单向数据桥。把本 skill 的行程契约翻译成 map-motion 的镜头表，
让一份路书能延伸出一段「这趟的行程动画」。**反方向不存在** ——
map-motion 不认识 itinerary.json，本脚本也不读 map-motion 的任何产物。

设计约束（与 SKILL.md 的「两半不能混」一致）：
  · 本脚本是**出口**，不参与决策、不改 itinerary.json、不影响 HTML 渲染链。
  · **纯标准库**，零新依赖（不 import 第三方，不联网）。
  · 只搬运**地点名与日期**，里程/路线一律交给 map-motion 用自己的高德通道重算 ——
    避免与 build_swiss.py 走的高德 MCP 通道算出两套数。

用法：
    python3 scripts/itinerary_to_motion.py itinerary.json              # → itinerary.motion.json
    python3 scripts/itinerary_to_motion.py itinerary.json -o 片子.json
    python3 scripts/itinerary_to_motion.py itinerary.json --globe --style satellite
    python3 scripts/itinerary_to_motion.py itinerary.json --size landscape   # 横屏发 B 站

参数：
    --mode    driving|walking|bicycling|line   出行方式（缺省按标题/眉题里的词自动判）
    --style   map-motion 的 14 种样式之一（缺省按 mode 选）
    --size    portrait|landscape|square（缺省 portrait）
    --profile auto|ground|flight|mixed（缺省 auto）
    --globe   在片头 title 卡后插一个 globe 俯冲镜头
    --no-title    不出片头标题卡
    --return / --no-return   是否原路返程（缺省：首尾站点同名则自动开）
    --all-legs    出境片含返程航段（缺省只画去程）
    --json    只输出 spec JSON 到 stdout，不写文件、不打印摘要

输出末尾会打印 **待人工核对清单** —— map-motion 编译时会把地名交给高德解析，
同名地点会解析错（它自己的坑清单里记着「香格里拉 → 某家酒店」），必须逐行核对。
"""

import argparse
import json
import os
import re
import sys

# ── 出行方式识别：按关键词打分，命中最多者胜 ────────────────────────────
MODE_HINTS = {
    "bicycling": ["骑行", "单车", "自行车", "环湖骑", "摩托", "摩旅"],
    "walking": ["徒步", "登山", "爬山", "健行", "trekking", "citywalk", "步行"],
    "driving": ["自驾", "驾车", "包车", "房车", "开车", "越野"],
}

VEHICLE_OF_MODE = {"driving": "car", "walking": "walk", "bicycling": "bike", "line": "dot"}

# mode → 推荐样式（街道级只能用瓦片样式；矢量样式封顶 8 级）
STYLE_OF_MODE = {"driving": "journal", "bicycling": "satellite", "walking": "satellite", "line": "amap"}

# 机场名 → 城市。用于从「厦门高崎 T4 08:05」「浦东 T1 14:45」里剥出城市。
# 只放机场名（几乎不变），不放会变的东西。命中的结果一律标为「需核对」。
AIRPORT_CITY = {
    "高崎": "厦门", "浦东": "上海", "虹桥": "上海", "首都": "北京", "大兴": "北京",
    "白云": "广州", "宝安": "深圳", "双流": "成都", "天府": "成都", "江北": "重庆",
    "咸阳": "西安", "萧山": "杭州", "禄口": "南京", "黄花": "长沙", "长水": "昆明",
    "吴圩": "南宁", "美兰": "海口", "凤凰": "三亚", "天河": "武汉", "龙洞堡": "贵阳",
    "关西": "大阪", "伊丹": "大阪", "成田": "东京", "羽田": "东京", "中部": "名古屋",
    "仁川": "首尔", "金浦": "首尔", "樟宜": "新加坡", "桃园": "台北", "松山": "台北",
    "素万那普": "曼谷", "廊曼": "曼谷", "希斯罗": "伦敦", "戴高乐": "巴黎",
    "肯尼迪": "纽约", "纽瓦克": "纽约",
}
_AIRPORT_KEYS = sorted(AIRPORT_CITY, key=len, reverse=True)

_CAL_DATE = re.compile(r"^(\d{1,2})[/.\-](\d{1,2})")


# ── 小工具 ────────────────────────────────────────────────────────────

def _norm(s):
    """归一化地名，用于跨字段配对（viz.route 与 stages.stops 的写法常不一致）。"""
    if not s:
        return ""
    s = re.sub(r"[（(][^）)]*[）)]", "", str(s))
    return s.replace("·", "").replace(" ", "").strip()


def _date_compact(s):
    """'10/1' → '10.01'。不是日历日期（如 'D1'）返回 None —— map-motion 的 dates 要的是日期。"""
    if not s:
        return None
    m = _CAL_DATE.match(str(s).strip())
    if not m:
        return None
    return "%02d.%02d" % (int(m.group(1)), int(m.group(2)))


def _pick_text(*cands):
    for c in cands:
        if c:
            return str(c).strip()
    return ""


def _is_round_trip(names):
    return len(names) >= 3 and _norm(names[0]) == _norm(names[-1])


def _detect_mode(it):
    blob = " ".join(_pick_text(it.get(k)) for k in ("title", "eyebrow", "subtitle", "route_line"))
    scores = {m: sum(blob.count(w) for w in ws) for m, ws in MODE_HINTS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "driving"


def _split_label(raw):
    """把「杭州 · 论坛」「西海镇 → 湖东种羊场」拆成 (显示名, 高德要解析的地名)。

    map-motion 的 trip.stops 接受 {"name": 显示名, "at": 地名}（compile.py:305 已确认）。
    拆不出来就 at 与 name 同值。
    """
    s = str(raw).strip()
    display = s
    target = s
    if "→" in s:                      # 「A → B」：停的是 B
        display = s.split("→")[-1].strip()
        target = display
    if "·" in target:                 # 「城市 · 场馆」：解析城市
        head = target.split("·")[0].strip()
        if head:
            target = head
    return display, target


def _route_nodes(it):
    """取路线节点。viz.route 是唯一真源（SKILL.md 明写）；缺则退到 stages.stops。"""
    route = (it.get("viz") or {}).get("route") or []
    nodes = []
    for r in route:
        raw = _pick_text(r.get("name"))
        if raw:
            disp, target = _split_label(raw)
            nodes.append({"name": disp, "at": target, "km": r.get("km"), "m": r.get("m")})
    if nodes:
        return nodes, "viz.route"

    seen, out = set(), []
    for st in it.get("stages") or []:
        for stop in st.get("stops") or []:
            raw = _pick_text(stop.get("name"))
            if not raw:
                continue
            disp, target = _split_label(raw)
            if _norm(disp) in seen:
                continue
            seen.add(_norm(disp))
            out.append({"name": disp, "at": target, "km": None, "m": None})
    return out, "stages.stops"


def _date_map(it, stop_names):
    """把 stages[].stops[].date 配到站点上。配不上宁可不写，也不猜。"""
    pairs = []
    for st in it.get("stages") or []:
        for stop in st.get("stops") or []:
            nm = _pick_text(stop.get("name"))
            d = _date_compact(stop.get("date"))
            if nm and d:
                disp, target = _split_label(nm)
                pairs.append((_norm(disp), d))
                pairs.append((_norm(target), d))

    out, missing = {}, []
    for name in stop_names:
        n = _norm(name)
        hit = next((d for pn, d in pairs if pn == n), None)
        if hit is None:
            hit = next((d for pn, d in pairs if pn and (pn in n or n in pn)), None)
        if hit:
            out[name] = hit
        else:
            missing.append(name)
    return out, missing


def _extract_city(raw, vocabulary):
    """『厦门高崎 T4 08:05』→ ('厦门', True)。第二项 = 是否来自行程自身词汇（更可信）。"""
    if not raw:
        return None, True
    s = str(raw).strip()
    s = re.sub(r"\s*\d{1,2}:\d{2}(\+\d+)?\s*$", "", s)   # 去时间（含跨天 +1）
    s = re.sub(r"\s*T\d\s*$", "", s).strip()             # 去航站楼
    s = re.sub(r"\s*\d+\s*$", "", s).strip()             # 去孤立数字

    n = _norm(s)
    for v in vocabulary:
        vn = _norm(v)
        if vn and (vn == n or vn in n):
            return v, True

    for k in _AIRPORT_KEYS:
        if s.endswith(k):
            return AIRPORT_CITY[k], False

    return (s[:2] if len(s) >= 2 else s), False


def _ground_nodes(it):
    nodes, _ = _route_nodes(it)
    return nodes


# ── 三个 profile ──────────────────────────────────────────────────────

def build_ground(it, args):
    """地面：title → [globe] → trip → overview。"""
    nodes, source = _route_nodes(it)
    if not nodes:
        return None, [], ["itinerary.json 里既没有 viz.route[] 也没有 stages[].stops[]，无从生成。"]

    names = [n["name"] for n in nodes]
    mode = args.mode or _detect_mode(it)
    style = args.style or STYLE_OF_MODE.get(mode, "amap")

    dates, missing = _date_map(it, names)
    notes = []
    if missing:
        notes.append("这些站点没配到日历日期，spec 里已省略（map-motion 的 dates 键必须与 stops 一字不差）："
                     + "、".join(missing) + "。注意像「D1/D2」这种是日序不是日期，本来就配不上。")

    km_sum, has_km = 0.0, False
    for n in nodes:
        try:
            km_sum += float(n["km"])
            has_km = True
        except (TypeError, ValueError):
            pass
    has_alt = any(n.get("m") is not None for n in nodes)

    shots = []
    if not args.no_title:
        big = it.get("title_lines") or []
        shots.append({"type": "title",
                      "text": _pick_text(*(big[:1] + [it.get("title")])),
                      "sub": _pick_text(it.get("route_line"), it.get("subtitle"), it.get("eyebrow")),
                      "dur": 2.2})

    if args.globe:
        shots.append({"type": "globe", "to": names[0], "dur": 6, "label": names[0],
                      "sub": _pick_text(it.get("eyebrow"), it.get("subtitle")), "hold": 1.2})

    trip = {"type": "trip", "stops": _as_stops(nodes), "mode": mode,
            "vehicle": VEHICLE_OF_MODE.get(mode, "car"),
            "stamp": True, "return": args.return_flag,
            "stay": 1.8 if mode == "bicycling" else 2.6}
    if dates:
        trip["dates"] = dates
    if has_alt:
        trip["elevation"] = True          # viz.route 给了海拔 → 翻山/高原线，海拔剖面有用
    if args.globe:
        trip["overview"] = False          # globe 已交代地点，不重复铺全程
    shots.append(trip)

    tail = {"type": "overview", "dur": 2.6}
    if has_km and km_sum > 0:
        tail["title"] = {"text": "全程 %.0f km" % km_sum,
                         "sub": "按路书里程；map-motion 重算值可能不同", "pos": "bottom"}
    shots.append(tail)

    spec = _wrap(shots, args, style, source)
    return spec, names, notes


def _as_stops(nodes):
    """把节点转成 map-motion 的 stops 项：显示名与解析地名不同就写对象形式。"""
    out = []
    for n in nodes:
        if _norm(n["at"]) == _norm(n["name"]):
            out.append(n["name"])
        else:
            out.append({"name": n["name"], "at": n["at"]})
    return out


def build_flight(it, args):
    """纯航空：title → [globe] → pins(城市) → flight(每段) → overview。"""
    flights = it.get("flights") or []
    if not flights:
        return None, [], ["没有 flights[]，无法走 flight profile。"]
    return _flight_shots(it, args, flights, ground_nodes=[])


def build_mixed(it, args):
    """出境（有航空 + 有地面）：title → [globe] → flight(去程) → trip(地面) → overview。"""
    nodes = _ground_nodes(it)
    flights = it.get("flights") or []
    if not (nodes and flights):
        return None, [], ["mixed profile 需要同时有 flights[] 和地面路线。"]
    return _flight_shots(it, args, flights, ground_nodes=nodes, mixed=True)


def _flight_shots(it, args, flights, ground_nodes, mixed=False):
    vocab = [n["name"] for n in ground_nodes] + [n["at"] for n in ground_nodes]
    vocab += [w.get("city", "") for w in (it.get("weather") or [])]
    vocab += [s.get("name", "") for s in (it.get("stays") or [])]

    legs = flights if args.all_legs else [f for f in flights if str(f.get("leg", "")).find("返") < 0]
    if not legs:
        legs = flights

    cities, flagged, last = [], [], None
    for f in legs:
        for key in ("from", "to"):
            city, certain = _extract_city(f.get(key), vocab)
            if key == "from" and not certain and last:
                # 中转：本段出发地没写出城市（如「浦东 T1 14:45」），沿用上一段的到达城市
                city, certain = last, True
                flagged.append("%s（由上一段到达城市推得）" % city)
            elif not certain:
                flagged.append("%s（原值「%s」，按机场名剥离）" % (city, f.get(key)))
            if city and _norm(city) not in [_norm(c) for c in cities]:
                cities.append(city)
            if city:
                last = city

    if len(cities) < 2:
        return None, cities, ["从 flights[] 里提取到的城市少于 2 个，无法画航线。"]

    style = args.style or ("satellite" if mixed else "satellite")
    shots = []
    if not args.no_title:
        big = it.get("title_lines") or []
        shots.append({"type": "title",
                      "text": _pick_text(*(big[:1] + [it.get("title")])),
                      "sub": _pick_text(it.get("route_line"), it.get("subtitle")), "dur": 2.2})

    if args.globe:
        shots.append({"type": "globe", "to": cities[0], "dur": 6, "label": cities[0],
                      "sub": _pick_text(it.get("subtitle")), "hold": 1.2})

    shots.append({"type": "pins", "places": cities, "dur": 2.8, "zoom": 6, "caption": "行程城市"})

    for a, b in zip(cities, cities[1:]):
        shots.append({"type": "flight", "from": a, "to": b, "dur": 4.5,
                      "caption": {"text": "%s → %s" % (a, b), "sub": "大圆航线 · 示意"}})

    if mixed:
        nodes = ground_nodes
        mode = args.mode or _detect_mode(it)
        dates, _ = _date_map(it, [n["name"] for n in nodes])
        trip = {"type": "trip", "stops": _as_stops(nodes), "mode": mode,
                "vehicle": VEHICLE_OF_MODE.get(mode, "car"), "stamp": True,
                "return": False, "overview": False, "stay": 2.2, "clear": True}
        if dates:
            trip["dates"] = dates
        shots.append(trip)

    shots.append({"type": "overview", "dur": 2.6,
                  "title": {"text": "%d 城 · %d 段" % (len(cities), len(cities) - 1),
                            "sub": "航线为示意，非实际航路", "pos": "bottom"}})

    spec = _wrap(shots, args, style, "flights[]")
    notes = []
    if flagged:
        notes.append("这些城市名是启发式推出来的，务必核对：" + "、".join(flagged))
    if not args.all_legs:
        notes.append("只画了去程航段；要含返程加 --all-legs。")
    notes.append("flight 镜头画的是大圆航线示意，不是实际航路。")
    return spec, cities, notes


def _wrap(shots, args, style, source):
    spec = {"size": args.size, "fps": 30, "style": style, "tail": 0.6,
            "attribution": True, "shots": shots,
            "_bridge": {
                "source": "itinerary-builder/scripts/itinerary_to_motion.py",
                "route_source": source,
                "note": ("里程/路线一律由 map-motion 用自己的高德 REST 通道重算，"
                         "与本路书 HTML 走的高德 MCP 通道可能不一致；两处数字不同时以各自口径为准。"),
            }}
    return spec


# ── 主流程 ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="itinerary.json → map-motion 镜头表")
    ap.add_argument("itinerary")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--mode", choices=list(MODE_HINTS.keys()) + ["line"], default=None)
    ap.add_argument("--style", default=None)
    ap.add_argument("--size", choices=["portrait", "landscape", "square"], default="portrait")
    ap.add_argument("--profile", choices=["auto", "ground", "flight", "mixed"], default="auto")
    ap.add_argument("--globe", action="store_true")
    ap.add_argument("--no-title", action="store_true")
    ap.add_argument("--return", dest="return_flag", action="store_true", default=None)
    ap.add_argument("--no-return", dest="return_flag", action="store_false")
    ap.add_argument("--all-legs", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.itinerary, "r", encoding="utf-8") as fh:
            it = json.load(fh)
    except FileNotFoundError:
        sys.exit("找不到文件：%s" % args.itinerary)
    except json.JSONDecodeError as e:
        sys.exit("不是合法 JSON：%s\n%s" % (args.itinerary, e))

    nodes, _ = _route_nodes(it)
    if args.return_flag is None:
        args.return_flag = _is_round_trip([n["name"] for n in nodes])

    profile = args.profile
    if profile == "auto":
        has_f, has_g = bool(it.get("flights")), bool(nodes)
        profile = "mixed" if (has_f and has_g) else ("flight" if has_f else "ground")

    builder = {"ground": build_ground, "flight": build_flight, "mixed": build_mixed}[profile]
    spec, used, notes = builder(it, args)
    if spec is None:
        sys.exit("生成失败：" + ("；".join(notes) or "未知原因"))

    if args.json:
        print(json.dumps(spec, ensure_ascii=False, indent=1))
        return

    out = args.out or (os.path.splitext(args.itinerary)[0] + ".motion.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("✓ 已写出 %s" % out)
    print("  profile = %s · style = %s · size = %s" % (profile, spec["style"], spec["size"]))
    print("  镜头序列：" + " → ".join(s["type"] for s in spec["shots"]))
    print("  %s（%d）：%s" % ("站点" if profile != "flight" else "城市", len(used), " → ".join(used)))

    print("\n下一步（需要高德 key）：")
    print("  export AMAP_KEY=…   或   mkdir -p ~/.config/map-motion && "
          "echo '你的key' > ~/.config/map-motion/amap_key && chmod 600 ~/.config/map-motion/amap_key")
    print("  ~/Developer/map-motion/scripts/make.sh %s 成片.mp4" % out)
    print("  （先抽静帧看构图：把 成片.mp4 换成 静帧/ 并加 --stills 1,4,9）")

    print("\n⚠️ 必须人工核对 —— 编译时 map-motion 会把下列地名交给高德解析，同名地点会解析错")
    print("   （它自己的坑清单里记着「香格里拉 → 某家酒店」「青海湖 → 乌鲁木齐同名小区」）：")
    for n in used:
        print("     · %s" % n)
    print("   解析不准就改 spec：写成坐标 [lng, lat]（拾取器 lbs.amap.com/tools/picker），")
    print("   或 {\"name\": \"显示名\", \"at\": \"更精确的地名\"}。")

    if notes:
        print("\n其它提醒：")
        for n in notes:
            print("   · %s" % n)


if __name__ == "__main__":
    main()
