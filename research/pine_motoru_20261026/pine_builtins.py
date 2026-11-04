"""Pine yerleşikleri: ad alanı fonksiyonları, sabitler, çıktı yakalama, zaman. Çevirmen buradaki FUNCS / CONSTS'u kullanır."""
from __future__ import annotations

import math
import random as _random

import pine_runtime as R
import pine_ta as TAm
from pine_runtime import (ARRAY, BOX, CHART_POINT, LABEL, LINE, MAP, MATRIX, NA, PArray, PineError, PMap, PMatrix,
                          T, Unsupported, color_class, isna)

TA = dict(TAm.TA_CLASSES)


class Sum:
    __slots__ = ("w",)

    def __init__(self):
        self.w = TAm.Window()

    def u(self, x, n):
        if not self.w.push(x, TAm._len(n)):
            return NA
        vals = list(self.w.q)
        return NA if any(isna(v) for v in vals) else sum(vals)


TA["math_sum"] = Sum


class CumExt:
    __slots__ = ("v", "mode")

    def __init__(self, mode="max"):
        self.v, self.mode = NA, mode

    def u(self, x):
        if not isna(x):
            self.v = x if isna(self.v) else (max(self.v, x) if self.mode == "max" else min(self.v, x))
        return self.v


TA["cum_max"] = CumExt
TA["cum_min"] = lambda: CumExt("min")


def _mT(m):
    out = PMatrix()
    out.m = [list(r) for r in zip(*m.m)] if m.m else []
    return out


def _msum(a, b):
    if b is None:
        return sum(v for r in a.m for v in r)
    out = PMatrix()
    out.m = [[x + (y if not isinstance(b, PMatrix) else b.m[i][j]) for j, x in enumerate(r)] for i, r in enumerate(a.m)] \
        if isinstance(b, PMatrix) else [[x + b for x in r] for r in a.m]
    return out


def nz(source, replacement=0):
    return replacement if isna(source) else source


def na(x):
    return isna(x)


def _num(x):
    return NA if x is None else x


def to_int(x):
    if isna(x):
        return NA
    try:
        return int(x)
    except (TypeError, ValueError):
        return NA


def to_float(x):
    return NA if isna(x) else float(x)


def to_bool(x):
    return T(x)


def math_round(number, precision=None):
    if isna(number):
        return NA
    if precision is None or isna(precision):
        return math.floor(number + 0.5)
    p = 10 ** int(precision)
    return math.floor(number * p + 0.5) / p


def _m1(fn):
    def w(*a, **k):
        x = a[0] if a else next(iter(k.values()))
        if isna(x):
            return NA
        try:
            return fn(x)
        except (ValueError, OverflowError, ZeroDivisionError):
            return NA
    return w


def math_max(*a, **k):
    if len(a) == 2:                              # sıcak yol: iki argüman
        x, y = a
        if x is None or y is None or x != x or y != y:
            return NA
        return max(x, y)
    vals = [v for v in a if not isna(v)]
    return max(vals) if len(vals) == len(a) and vals else NA


def math_min(*a, **k):
    if len(a) == 2:
        x, y = a
        if x is None or y is None or x != x or y != y:
            return NA
        return min(x, y)
    vals = [v for v in a if not isna(v)]
    return min(vals) if len(vals) == len(a) and vals else NA


def math_avg(*a, **k):
    return NA if any(isna(v) for v in a) else sum(a) / len(a)


def math_pow(base, exponent):
    try:
        return NA if isna(base) or isna(exponent) else float(base) ** exponent
    except (OverflowError, ZeroDivisionError, ValueError):
        return NA
    except TypeError:
        return NA


def math_sign(x):
    return NA if isna(x) else (1.0 if x > 0 else (-1.0 if x < 0 else 0.0))


def math_log(x):
    if type(x) is float and x > 0.0:                   # sıcak yol
        return math.log(x)
    return NA if isna(x) or x <= 0 else math.log(x)


_abs_slow = None


def math_abs(*a, **k):
    if len(a) == 1:
        x = a[0]
        t = type(x)
        if t is float or t is int:                     # sıcak yol (nan → nan)
            return abs(x)
    return _abs_slow(*a, **k)


def math_log10(x):
    return NA if isna(x) or x <= 0 else math.log10(x)


def math_random(min=0, max=1, seed=None):
    return _random.uniform(min, max)


def str_tostring(value, format=None):
    if isna(value):
        return "NaN"
    if isinstance(value, float) and format and str(format).startswith("#"):
        dec = len(str(format).split(".")[1]) if "." in str(format) else 0
        return f"{value:.{dec}f}"
    return str(value)


def str_format(formatString, *args):
    out = formatString
    for i, a in enumerate(args):
        out = out.replace("{" + str(i) + "}", str(a))
    return out


STR = {
    "tostring": str_tostring, "format": str_format, "length": lambda string: len(string),
    "contains": lambda source, str: str in source, "replace_all": lambda source, target, replacement: source.replace(target, replacement),
    "replace": lambda source, target, replacement, occurrence=0: source.replace(target, replacement, 1),
    "lower": lambda source: source.lower(), "upper": lambda source: source.upper(),
    "split": lambda string, separator: PArray(string.split(separator)),
    "substring": lambda source, begin_pos, end_pos=None: source[int(begin_pos):None if end_pos is None else int(end_pos)],
    "tonumber": lambda string: _tonum(string), "startswith": lambda source, str: source.startswith(str),
    "endswith": lambda source, str: source.endswith(str), "pos": lambda source, str: source.find(str),
    "trim": lambda source: source.strip(), "repeat": lambda source, repeat, separator="": separator.join([source] * int(repeat)),
    "match": lambda source, regex: "", "format_time": lambda time, format=None, timezone=None: str(time),
}


def _tonum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return NA


# ── girdiler: varsayılan değer ─────────────────────────────────────────────
def input_any(*a, **k):
    return k["defval"] if "defval" in k else (a[0] if a else NA)


# ── çıktılar ────────────────────────────────────────────────────────────────
def plot(rt, site, series=NA, title=None, color=None, *a, **k):
    rt.out(site, "plot", title, series, k.get("color", color))
    return site


def plotshape(rt, site, series=NA, title=None, *a, **k):
    rt.out(site, "shape", title, series, k.get("color"))
    return site


def plotchar(rt, site, series=NA, title=None, *a, **k):
    rt.out(site, "shape", title, series, k.get("color"))
    return site


def plotarrow(rt, site, series=NA, title=None, *a, **k):
    rt.out(site, "arrow", title, series, None)
    return site


def bgcolor(rt, site, color=None, *a, **k):
    rt.out(site, "bgcolor", k.get("title"), 0 if color is None else 1, color)


def barcolor(rt, site, color=None, *a, **k):
    rt.out(site, "barcolor", k.get("title"), 0 if color is None else 1, color)


def alertcondition(rt, site, condition=False, title=None, message=None, *a, **k):
    rt.out(site, "alert", title, condition, None)


def alert(rt, site, message="", freq=None, *a, **k):
    rt.event(site, "alertcall", message)


def strategy_entry(rt, site, id="", direction=None, qty=None, limit=None, stop=None, *a, when=True, _kind="entry",
                   **k):
    if direction is None and "long" in k:              # v2–v4: strategy.entry(id, long=true)
        direction = k["long"]
    if T(when):
        d = 1 if str(direction).endswith("long") or direction is True else (-1 if str(direction).endswith("short") else 0)
        rt.entry(site, d, id)
        rt.bk.entry(id, direction, qty, limit, stop, kind=_kind)


def strategy_order(rt, site, id="", direction=None, qty=None, limit=None, stop=None, *a, when=True, **k):
    strategy_entry(rt, site, id, direction, qty, limit, stop, when=when, _kind="order", **k)


def strategy_close(rt, site, id="", *a, when=True, **k):
    if T(when):
        rt.entry(site, 0, id)
        rt.bk.close(id, k.get("qty", a[1] if len(a) > 1 else None))


def strategy_close_all(rt, site, *a, when=True, **k):
    if T(when):
        rt.entry(site, 0, "all")
        rt.bk.close(all_=True)


def strategy_exit(rt, site, id="", from_entry="", qty=None, qty_percent=None, profit=None, limit=None, loss=None,
                  stop=None, trail_price=None, trail_points=None, trail_offset=None, *a, when=True, **k):
    if T(when):
        rt.bk.exit(id, from_entry, qty, qty_percent, profit, limit, loss, stop, trail_price, trail_points, trail_offset)


def strategy_cancel(rt, site, id="", *a, when=True, **k):
    if T(when):
        rt.bk.cancel(id)


def strategy_cancel_all(rt, site, *a, when=True, **k):
    if T(when):
        rt.bk.cancel()


def noop(*a, **k):
    return None


# ── zaman fonksiyonları ─────────────────────────────────────────────────────
def in_session(rt, b, session):
    if not isinstance(session, str) or "-" not in session:
        return True
    try:
        rng = session.split(":")[0]
        a, c = rng.split("-")[:2]
        s = int(a[:2]) * 60 + int(a[2:4])
        e = int(c[:2]) * 60 + int(c[2:4])
    except (ValueError, IndexError):
        return True
    m = rt.HOUR[b] * 60 + rt.MINUTE[b]
    return (s <= m < e) if s <= e else (m >= s or m < e)


def time_fn(rt, b, timeframe=None, session=None, timezone=None, *a, **k):
    if session is not None and not in_session(rt, b, session):
        return NA
    return rt.TM[b]


def timeframe_change(rt, ctx, site, timeframe):
    key = rt.tf_bucket(timeframe)
    st = rt.st(ctx, site, TAm.Hist)
    prev = st.u(key)
    return not isna(prev) and prev != key


# ── v4 → v5 ad eşlemesi ─────────────────────────────────────────────────────
V4_EXTRA = {"round_to_mintick": "math.round_to_mintick"}
V4 = {n: "ta." + n for n in (
    "sma ema rma wma swma vwma hma alma highest lowest highestbars lowestbars stdev variance dev change mom roc "
    "crossover crossunder cross rsi atr stoch cci mfi dmi sar supertrend linreg correlation percentrank median "
    "mode range cum rising falling pivothigh pivotlow barssince valuewhen tsi cmo wpr cog bb bbw kc kcw macd "
    "percentile_linear_interpolation percentile_nearest_rank").split()}
V4.update({"tr": "ta.tr", "obv": "ta.obv", "accdist": "ta.accdist", "pvt": "ta.pvt", "vwap": "ta.vwap",
           "abs": "math.abs", "max": "math.max", "min": "math.min", "round": "math.round", "pow": "math.pow",
           "sqrt": "math.sqrt", "log": "math.log", "log10": "math.log10", "exp": "math.exp", "sign": "math.sign",
           "avg": "math.avg", "ceil": "math.ceil", "floor": "math.floor", "sum": "math.sum", "atan": "math.atan",
           "sin": "math.sin", "cos": "math.cos", "tan": "math.tan", "asin": "math.asin", "acos": "math.acos",
           "tostring": "str.tostring", "tonumber": "str.tonumber", "security": "request.security",
           "study": "indicator", "iff": "iff", "fixnan": "fixnan", "input": "input", "timestamp": "timestamp",
           "valuewhen": "ta.valuewhen", "offset": "offset_fn", "nz": "nz", "na": "na", "color": "color_fn",
           "linebreak": "linebreak", "heikinashi": "heikinashi", "renko": "renko", "kagi": "kagi", "pointfigure": "pointfigure"})

FUNCS = {
    "nz": nz, "na": na, "int": to_int, "float": to_float, "bool": to_bool, "string": str,
    "iff": lambda condition, then, _else: then if T(condition) else _else,
    "math.abs": math_abs, "math.max": math_max, "math.min": math_min, "math.avg": math_avg,
    "math.round": math_round, "math.floor": _m1(math.floor), "math.ceil": _m1(math.ceil), "math.sqrt": _m1(lambda x: math.sqrt(x) if x >= 0 else NA),
    "math.pow": math_pow, "math.log": math_log, "math.log10": math_log10, "math.exp": _m1(math.exp),
    "math.sign": math_sign, "math.sin": _m1(math.sin), "math.cos": _m1(math.cos), "math.tan": _m1(math.tan),
    "math.asin": _m1(math.asin), "math.acos": _m1(math.acos), "math.atan": _m1(math.atan),
    "math.todegrees": _m1(math.degrees), "math.toradians": _m1(math.radians), "math.random": math_random,
    "math.round_to_mintick": lambda number: number,
    "color.new": R.color_new, "color.rgb": R.color_rgb_fn, "color.from_gradient": R.color_gradient,
    "color.r": lambda color: (R.color_rgb(color) or (NA,))[0], "color.g": lambda color: (R.color_rgb(color) or (NA, NA))[1],
    "color.b": lambda color: (R.color_rgb(color) or (NA, NA, NA))[2], "color.t": lambda color: 0,
    "color_fn": lambda *a, **k: a[0] if a else None,
    "input": input_any, "timestamp": lambda *a, **k: NA,
    "runtime.error": lambda message="": (_ for _ in ()).throw(PineError("runtime.error: " + str(message))),
    "max_bars_back": noop, "fill": noop, "hline": noop, "plotcandle": noop, "plotbar": noop,
    "indicator": noop, "strategy": noop, "library": noop, "linebreak": noop,
    "str.tostring": str_tostring,
}
for _k, _v in STR.items():
    FUNCS["str." + _k] = _v
for _ns, _tbl in (("array", ARRAY), ("map", MAP), ("matrix", MATRIX), ("line", LINE), ("box", BOX),
                  ("label", LABEL), ("chart.point", CHART_POINT)):
    for _k, _v in _tbl.items():
        FUNCS[f"{_ns}.{_k}"] = _v
for _n in ("color", "line", "label", "box", "table", "linefill", "polyline", "chart.point"):
    FUNCS.setdefault(_n, lambda x=None, *a, **k: x)            # tip dönüşümü: color(na), line(na)…
FUNCS["timeframe.from_seconds"] = lambda seconds: (str(int(seconds) // 60) if seconds < 86400 else "D")
FUNCS["matrix.transpose"] = lambda id: _mT(id)
FUNCS["matrix.max"] = lambda id: max(v for r in id.m for v in r) if id.m else NA
FUNCS["matrix.min"] = lambda id: min(v for r in id.m for v in r) if id.m else NA
FUNCS["matrix.sum"] = lambda id1, id2=None: _msum(id1, id2)
for _n in ("int", "float", "bool", "string", "color", "source", "timeframe", "session", "symbol", "price",
           "time", "text_area", "enum"):
    FUNCS["input." + _n] = input_any

# rt ve çağrı yeri isteyen yerleşikler
NEED_RT = {"plot": plot, "plotshape": plotshape, "plotchar": plotchar, "plotarrow": plotarrow, "bgcolor": bgcolor,
           "barcolor": barcolor, "alertcondition": alertcondition, "alert": alert, "strategy.entry": strategy_entry,
           "strategy.order": strategy_order, "strategy.close": strategy_close, "strategy.close_all": strategy_close_all,
           "strategy.exit": strategy_exit, "strategy.cancel": strategy_cancel, "strategy.cancel_all": strategy_cancel_all}

NOOP_PREFIX = ("table.", "polyline.", "linefill.", "log.", "strategy.risk.",
               "label.set_", "line.set_color", "line.set_width", "line.set_style", "line.set_extend",
               "box.set_bgcolor", "box.set_border", "box.set_text", "box.set_extend", "label.set_color",
               "label.set_style", "label.set_size", "label.set_textcolor", "label.set_tooltip", "line.set_xloc",
               "box.set_", "line.set_first_point", "line.set_second_point")

# ad alanı sabitleri (öznitelik erişimi, çağrı değil)
NAMED = {f"color.{k}": f"color.{k}" for k in R.NAMED_COLORS}
CONST_NS = {"shape", "location", "size", "plot", "xloc", "yloc", "extend", "position", "display", "format",
            "barmerge", "order", "currency", "session", "hline", "font", "scale", "adjustment", "alert",
            "dividends", "earnings", "splits", "text", "line", "label", "box", "table", "settlement_as_close",
            "backadjustment", "chart", "math", "color", "dayofweek", "strategy", "syminfo", "timeframe",
            "barstate", "ta", "request", "ticker", "str", "array", "map", "matrix", "input", "polyline",
            "linefill", "runtime", "log", "time", "earnings"}

V4.update(V4_EXTRA)

_abs_slow = _m1(abs)
