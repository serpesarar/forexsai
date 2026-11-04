"""Pine çalışma zamanı: na mantığı, seriler, koleksiyonlar, çizim nesneleri, UDT'ler, yerleşikler, çıktı yakalama."""
from __future__ import annotations

import math
import random as _random
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pine_ta

NA = float("nan")
isna = pine_ta.isna
_UNSET = object()


class PineError(Exception):
    pass


class Unsupported(PineError):
    pass


def T(x) -> bool:
    """Pine doğruluk değeri: na/None → false."""
    if x is True or x is False:                  # sıcak yol: karşılaştırma sonuçları
        return x
    if x is None:
        return False
    if isinstance(x, float):
        return x == x and x != 0.0
    return bool(x)


def DIV(a, b):
    try:
        return a / b                             # na girdi → nan kendiliğinden yayılır
    except (ZeroDivisionError, TypeError):
        return NA


def MOD(a, b):
    try:
        if b == 0 or isna(a) or isna(b):
            return NA
        return math.fmod(a, b)
    except TypeError:
        return NA


def ADD(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return ("" if isna(a) else str(a)) + ("" if isna(b) else str(b))
    try:
        return a + b
    except TypeError:
        return NA


def NUM(x):
    if x is None:
        return NA
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    return x


# ── seriler ─────────────────────────────────────────────────────────────────
class Series:
    __slots__ = ("v", "hist", "touched", "always", "init")

    def __init__(self, always=True):
        self.v, self.hist, self.touched, self.always, self.init = NA, [], False, always, False

    def set(self, v):
        self.v = v
        self.touched = True
        return v

    def h(self, n):
        try:
            n = int(n)
        except (TypeError, ValueError):
            return NA
        if n <= 0:
            return self.v
        return self.hist[-n] if len(self.hist) >= n else NA

    def commit(self):
        if self.always or self.touched:
            self.hist.append(self.v)
            if len(self.hist) > 6000:
                del self.hist[:1000]
        self.touched = False


def TUP(x, n):
    """Tuple açılımı: na/None gelirse n elemanlı na demeti."""
    if isinstance(x, (tuple, list)):
        return x if len(x) >= n else tuple(x) + (NA,) * (n - len(x))
    return (NA,) * n


def HA(arr, b, n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return NA
    i = b - n
    return arr[i] if 0 <= i <= b else NA


def HX(s: Series, val, n):
    s.set(val)
    return s.h(n)


# ── koleksiyonlar ───────────────────────────────────────────────────────────
class PArray(list):
    __slots__ = ("etype",)

    def __init__(self, it=(), etype="float"):
        super().__init__(it)
        self.etype = etype


class PMap(dict):
    pass


class PMatrix:
    def __init__(self, rows=0, cols=0, init=NA):
        self.m = [[init] * int(cols) for _ in range(int(rows))]


def _arr_vals(a):
    return [v for v in a if not isna(v)]


def _idx(i):
    try:
        return int(i)
    except (TypeError, ValueError):
        raise PineError("dizi indeksi na")


ARRAY = {}


def _reg(table, *names):
    def deco(fn):
        for n in names:
            table[n] = fn
        return fn
    return deco


def array_new(size=0, initial_value=NA, etype="float"):
    n = 0 if isna(size) else int(size)
    return PArray([initial_value] * n, etype)


for _t in ("float", "int", "bool", "string", "color", "line", "label", "box", "table", "linefill"):
    ARRAY["new_" + _t] = (lambda t: lambda size=0, initial_value=None: array_new(
        size, (NA if initial_value is None and t in ("float", "int") else
               (False if initial_value is None and t == "bool" else initial_value)), t))(_t)
ARRAY["new"] = lambda size=0, initial_value=NA, **k: array_new(size, initial_value)
ARRAY["from"] = lambda *a, **k: PArray(a)
_reg(ARRAY, "push")(lambda id, value: id.append(value))
_reg(ARRAY, "pop")(lambda id: id.pop() if id else NA)
_reg(ARRAY, "shift")(lambda id: id.pop(0) if id else NA)
_reg(ARRAY, "unshift")(lambda id, value: id.insert(0, value))
_reg(ARRAY, "insert")(lambda id, index, value: id.insert(_idx(index), value))
_reg(ARRAY, "remove")(lambda id, index: id.pop(_idx(index)) if id else NA)
_reg(ARRAY, "get")(lambda id, index: id[index] if type(index) is int else id[_idx(index)])
_reg(ARRAY, "set")(lambda id, index, value: id.__setitem__(_idx(index), value))
_reg(ARRAY, "size")(lambda id: len(id) if id is not None else NA)
_reg(ARRAY, "clear")(lambda id: id.clear())
_reg(ARRAY, "first")(lambda id: id[0] if id else NA)
_reg(ARRAY, "last")(lambda id: id[-1] if id else NA)
_reg(ARRAY, "sum")(lambda id: sum(_arr_vals(id)) if _arr_vals(id) else NA)
_reg(ARRAY, "avg")(lambda id: (sum(_arr_vals(id)) / len(_arr_vals(id))) if _arr_vals(id) else NA)
_reg(ARRAY, "min")(lambda id, nth=0: sorted(_arr_vals(id))[int(nth)] if len(_arr_vals(id)) > int(nth) else NA)
_reg(ARRAY, "max")(lambda id, nth=0: sorted(_arr_vals(id), reverse=True)[int(nth)] if len(_arr_vals(id)) > int(nth) else NA)
_reg(ARRAY, "range")(lambda id: (max(_arr_vals(id)) - min(_arr_vals(id))) if _arr_vals(id) else NA)
_reg(ARRAY, "includes")(lambda id, value: value in id)
_reg(ARRAY, "indexof")(lambda id, value: id.index(value) if value in id else -1)
_reg(ARRAY, "lastindexof")(lambda id, value: len(id) - 1 - id[::-1].index(value) if value in id else -1)
_reg(ARRAY, "copy")(lambda id: PArray(id, getattr(id, "etype", "float")))
_reg(ARRAY, "slice")(lambda id, index_from, index_to: PArray(id[_idx(index_from):_idx(index_to)]))
_reg(ARRAY, "concat")(lambda id1, id2: (id1.extend(id2), id1)[1])
_reg(ARRAY, "reverse")(lambda id: id.reverse())
_reg(ARRAY, "join")(lambda id, separator="": separator.join(str(v) for v in id))


@_reg(ARRAY, "fill")
def _arr_fill(id, value, index_from=0, index_to=None):
    end = len(id) if index_to is None or isna(index_to) else int(index_to)
    for i in range(int(index_from), end):
        id[i] = value


@_reg(ARRAY, "sort")
def _arr_sort(id, order=None, **k):
    rev = order == "order.descending"
    id.sort(key=lambda v: (isna(v), v), reverse=rev)


@_reg(ARRAY, "sort_indices")
def _arr_sort_idx(id, order=None):
    rev = order == "order.descending"
    return PArray(sorted(range(len(id)), key=lambda i: id[i], reverse=rev), "int")


@_reg(ARRAY, "median")
def _arr_median(id):
    v = sorted(_arr_vals(id))
    if not v:
        return NA
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


@_reg(ARRAY, "stdev")
def _arr_stdev(id, biased=True):
    v = _arr_vals(id)
    if len(v) < 1:
        return NA
    m = sum(v) / len(v)
    d = len(v) if biased or len(v) < 2 else len(v) - 1
    return math.sqrt(sum((x - m) ** 2 for x in v) / d)


@_reg(ARRAY, "variance")
def _arr_var(id, biased=True):
    s = _arr_stdev(id, biased)
    return s * s if not isna(s) else NA


@_reg(ARRAY, "percentile_linear_interpolation", "percentile_nearest_rank")
def _arr_pct(id, percentage):
    v = sorted(_arr_vals(id))
    if not v:
        return NA
    pos = (len(v) - 1) * percentage / 100
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


@_reg(ARRAY, "percentrank")
def _arr_prank(id, index):
    v = id[int(index)]
    return 100 * sum(1 for x in id if not isna(x) and x <= v) / max(len(id) - 1, 1)


@_reg(ARRAY, "abs")
def _arr_abs(id):
    return PArray([abs(v) if not isna(v) else v for v in id])


@_reg(ARRAY, "mode")
def _arr_mode(id):
    v = _arr_vals(id)
    return max(set(v), key=v.count) if v else NA


@_reg(ARRAY, "binary_search", "binary_search_leftmost", "binary_search_rightmost")
def _arr_bs(id, val):
    return id.index(val) if val in id else -1


@_reg(ARRAY, "covariance")
def _arr_cov(id1, id2, biased=True):
    a, b = list(id1), list(id2)
    n = min(len(a), len(b))
    if n < 2:
        return NA
    ma, mb = sum(a[:n]) / n, sum(b[:n]) / n
    return sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / (n if biased else n - 1)


@_reg(ARRAY, "standardize")
def _arr_std(id):
    m = ARRAY["avg"](id)
    s = _arr_stdev(id)
    return PArray([(v - m) / s if s else NA for v in id])


_reg(ARRAY, "every")(lambda id: all(T(v) for v in id))
_reg(ARRAY, "some")(lambda id: any(T(v) for v in id))

MAP = {
    "new": lambda *a, **k: PMap(),
    "put": lambda id, key, value: (id.get(key, NA), id.__setitem__(key, value))[0],
    "get": lambda id, key: id.get(key, NA),
    "contains": lambda id, key: key in id,
    "remove": lambda id, key: id.pop(key, NA),
    "keys": lambda id: PArray(list(id.keys())),
    "values": lambda id: PArray(list(id.values())),
    "size": lambda id: len(id),
    "clear": lambda id: id.clear(),
    "copy": lambda id: PMap(id),
    "put_all": lambda id, id2: id.update(id2),
}

MATRIX = {
    "new": lambda rows=0, columns=0, initial_value=NA, **k: PMatrix(rows, columns, initial_value),
    "get": lambda id, row, column: id.m[int(row)][int(column)],
    "set": lambda id, row, column, value: id.m[int(row)].__setitem__(int(column), value),
    "rows": lambda id: len(id.m),
    "columns": lambda id: len(id.m[0]) if id.m else 0,
    "row": lambda id, row: PArray(id.m[int(row)]),
    "col": lambda id, column: PArray([r[int(column)] for r in id.m]),
    "add_row": lambda id, row=None, array_id=None: id.m.insert(len(id.m) if row is None else int(row),
                                                              list(array_id) if array_id is not None else [NA] * (len(id.m[0]) if id.m else 0)),
    "remove_row": lambda id, row=None: id.m.pop(-1 if row is None else int(row)),
    "fill": lambda id, value, *a, **k: [r.__setitem__(slice(None), [value] * len(r)) for r in id.m],
    "copy": lambda id: _mcopy(id),
    "max": lambda id: max((v for r in id.m for v in r if not isna(v)), default=NA),
    "min": lambda id: min((v for r in id.m for v in r if not isna(v)), default=NA),
    "avg": lambda id: (lambda v: sum(v) / len(v) if v else NA)([v for r in id.m for v in r if not isna(v)]),
    "add_col": lambda id, column=None, array_id=None: [r.insert(len(r) if column is None else int(column),
                                                             NA if array_id is None else array_id[i]) for i, r in enumerate(id.m)],
    "remove_col": lambda id, column=None: [r.pop(-1 if column is None else int(column)) for r in id.m],
}


def _np(m):
    import numpy as np
    return np.array([[float("nan") if isna(v) else float(v) for v in r] for r in m.m], dtype=float)


def _from_np(a):
    out = PMatrix()
    out.m = [[NA if v != v else float(v) for v in r] for r in a.tolist()]
    return out


def _mmult(id, id2):
    import numpy as np
    a = _np(id)
    if isinstance(id2, PMatrix):
        return _from_np(a @ _np(id2))
    if isinstance(id2, (list, PArray)):
        return PArray((a @ np.array([float("nan") if isna(v) else float(v) for v in id2])).tolist())
    return _from_np(a * float(id2))


def _minv(id):
    import numpy as np
    try:
        return _from_np(np.linalg.inv(_np(id)))
    except np.linalg.LinAlgError:
        return _from_np(np.full((len(id.m), len(id.m)), np.nan))


def _msort(id, column=0, order="order.ascending"):
    c = int(column)
    rev = str(order).endswith("descending")
    id.m.sort(key=lambda r: (isna(r[c]), r[c] if not isna(r[c]) else 0), reverse=rev)


def _msub(id, from_row=0, to_row=None, from_column=0, to_column=None):
    out = PMatrix()
    rr = id.m[int(from_row):len(id.m) if to_row is None or isna(to_row) else int(to_row)]
    out.m = [list(r[int(from_column):len(r) if to_column is None or isna(to_column) else int(to_column)]) for r in rr]
    return out


def _melem(id, id2, op):
    import numpy as np
    a = _np(id)
    b = _np(id2) if isinstance(id2, PMatrix) else float(id2)
    return _from_np(a + b if op == "+" else a - b)


MATRIX.update({
    "mult": _mmult, "inv": _minv, "pinv": lambda id: _from_np(__import__("numpy").linalg.pinv(_np(id))),
    "det": lambda id: float(__import__("numpy").linalg.det(_np(id))),
    "rank": lambda id: int(__import__("numpy").linalg.matrix_rank(_np(id))),
    "trace": lambda id: float(__import__("numpy").trace(_np(id))),
    "sort": _msort, "submatrix": _msub, "sum": lambda id, id2: _melem(id, id2, "+"),
    "diff": lambda id, id2: _melem(id, id2, "-"),
    "elements_count": lambda id: sum(len(r) for r in id.m),
    "is_square": lambda id: len(id.m) == (len(id.m[0]) if id.m else 0),
    "swap_rows": lambda id, row1, row2: id.m.__setitem__(slice(None), _swap(id.m, int(row1), int(row2))),
    "reverse": lambda id: [r.reverse() for r in id.m] and id.m.reverse(),
    "median": lambda id: (lambda v: sorted(v)[len(v) // 2] if len(v) % 2 else
                          (sorted(v)[len(v) // 2 - 1] + sorted(v)[len(v) // 2]) / 2 if v else NA)(
        [v for r in id.m for v in r if not isna(v)]),
})


def _swap(m, i, j):
    m = list(m)
    m[i], m[j] = m[j], m[i]
    return m


def _mcopy(m):
    out = PMatrix()
    out.m = [list(r) for r in m.m]
    return out


# ── çizim nesneleri (getter'lar mantıkta kullanılır) ────────────────────────
DRAW_MAX = 500
DRAW = {"line": PArray(), "box": PArray(), "label": PArray()}       # RT her koşuda sıfırlar


def draw_reset():
    for k in DRAW:
        DRAW[k] = PArray()
    return DRAW


def _reg_draw(kind, obj, col=None, sty=None, tcol=None):
    obj._col, obj._sty, obj._tcol = col, sty, tcol
    lst = DRAW[kind]
    lst.append(obj)
    if len(lst) > DRAW_MAX:
        del lst[0]
    return obj


def _del_draw(kind, obj):
    lst = DRAW[kind]
    for i in range(len(lst) - 1, -1, -1):
        if lst[i] is obj:
            del lst[i]
            break


class Drawing:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _setter(obj, field, value):
    if isinstance(obj, Drawing):                       # na çizim kimliği: Pine'da sessizce yok sayılır
        setattr(obj, field, value)


class LineObj(Drawing):
    pass


LINE = {
    "new": lambda x1=NA, y1=NA, x2=NA, y2=NA, *a, first_point=None, second_point=None, **k: _reg_draw("line", LineObj(
        x1=getattr(first_point, "index", x1) if first_point else x1, y1=getattr(first_point, "price", y1) if first_point else y1,
        x2=getattr(second_point, "index", x2) if second_point else x2, y2=getattr(second_point, "price", y2) if second_point else y2),
        k.get("color", a[2] if len(a) > 2 else None)),
    "delete": lambda id: _del_draw("line", id),
    "get_x1": lambda id: id.x1 if isinstance(id, Drawing) else NA, "get_y1": lambda id: id.y1 if isinstance(id, Drawing) else NA,
    "get_x2": lambda id: id.x2 if isinstance(id, Drawing) else NA, "get_y2": lambda id: id.y2 if isinstance(id, Drawing) else NA,
    "set_x1": lambda id, x: _setter(id, "x1", x), "set_y1": lambda id, y: _setter(id, "y1", y),
    "set_x2": lambda id, x: _setter(id, "x2", x), "set_y2": lambda id, y: _setter(id, "y2", y),
    "set_xy1": lambda id, x, y: (_setter(id, "x1", x), _setter(id, "y1", y)),
    "set_xy2": lambda id, x, y: (_setter(id, "x2", x), _setter(id, "y2", y)),
    "copy": lambda id: LineObj(**id.__dict__) if isinstance(id, Drawing) else None,
}


def _line_price(id, x):
    if id is None or isna(id.x1) or isna(id.x2) or id.x2 == id.x1:
        return id.y1 if isinstance(id, Drawing) else NA
    return id.y1 + (id.y2 - id.y1) * (x - id.x1) / (id.x2 - id.x1)


LINE["get_price"] = _line_price


class BoxObj(Drawing):
    pass


BOX = {
    "new": lambda left=NA, top=NA, right=NA, bottom=NA, *a, top_left=None, bottom_right=None, **k: _reg_draw("box", BoxObj(
        left=getattr(top_left, "index", left) if top_left else left, top=getattr(top_left, "price", top) if top_left else top,
        right=getattr(bottom_right, "index", right) if bottom_right else right,
        bottom=getattr(bottom_right, "price", bottom) if bottom_right else bottom),
        k.get("bgcolor", a[5] if len(a) > 5 else None), None, k.get("border_color", a[0] if a else None)),
    "delete": lambda id: _del_draw("box", id),
    "get_top": lambda id: id.top if isinstance(id, Drawing) else NA, "get_bottom": lambda id: id.bottom if isinstance(id, Drawing) else NA,
    "get_left": lambda id: id.left if isinstance(id, Drawing) else NA, "get_right": lambda id: id.right if isinstance(id, Drawing) else NA,
    "set_top": lambda id, top: _setter(id, "top", top), "set_bottom": lambda id, bottom: _setter(id, "bottom", bottom),
    "set_left": lambda id, left: _setter(id, "left", left), "set_right": lambda id, right: _setter(id, "right", right),
    "set_lefttop": lambda id, left, top: (_setter(id, "left", left), _setter(id, "top", top)),
    "set_rightbottom": lambda id, right, bottom: (_setter(id, "right", right), _setter(id, "bottom", bottom)),
    "copy": lambda id: BoxObj(**id.__dict__) if isinstance(id, Drawing) else None,
}


class LabelObj(Drawing):
    pass


LABEL = {
    "new": lambda x=NA, y=NA, text="", *a, point=None, **k: _reg_draw("label", LabelObj(
        x=getattr(point, "index", x) if point else x, y=getattr(point, "price", y) if point else y, text=text),
        k.get("color", a[2] if len(a) > 2 else None), k.get("style", a[3] if len(a) > 3 else None),
        k.get("textcolor", a[4] if len(a) > 4 else None)),
    "delete": lambda id: _del_draw("label", id),
    "get_x": lambda id: id.x if isinstance(id, Drawing) else NA, "get_y": lambda id: id.y if isinstance(id, Drawing) else NA,
    "get_text": lambda id: id.text if isinstance(id, Drawing) else "",
    "set_x": lambda id, x: _setter(id, "x", x), "set_y": lambda id, y: _setter(id, "y", y),
    "set_xy": lambda id, x, y: (_setter(id, "x", x), _setter(id, "y", y)),
    "set_text": lambda id, text: _setter(id, "text", text),
    "copy": lambda id: LabelObj(**id.__dict__) if isinstance(id, Drawing) else None,
}

CHART_POINT = {
    "new": lambda time=NA, index=NA, price=NA: Drawing(time=time, index=index, price=price),
    "from_index": lambda index, price: Drawing(time=NA, index=index, price=price),
    "from_time": lambda time, price: Drawing(time=time, index=NA, price=price),
    "now": lambda price=NA: Drawing(time=NA, index=NA, price=price),
    "copy": lambda id: Drawing(**id.__dict__),
}

NOOP_NS = {"table", "polyline", "linefill", "log", "runtime"}


# ── renk → yön sınıfı ──────────────────────────────────────────────────────
NAMED_COLORS = {
    "aqua": "#00BCD4", "black": "#363A45", "blue": "#2196F3", "fuchsia": "#E040FB", "gray": "#787B86",
    "green": "#4CAF50", "lime": "#00E676", "maroon": "#880E4F", "navy": "#311B92", "olive": "#808000",
    "orange": "#FF9800", "purple": "#9C27B0", "red": "#FF5252", "silver": "#B2B5BE", "teal": "#00897B",
    "white": "#FFFFFF", "yellow": "#FFEB3B",
}


def color_rgb(c):
    if not isinstance(c, str):
        return None
    if c.startswith("color."):
        c = NAMED_COLORS.get(c[6:], "")
    m = re.match(r"#([0-9a-fA-F]{6})", c)
    if not m:
        return None
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


_UP_STYLES = ("label_up", "arrowup", "triangleup", "label_lower_left", "label_lower_right")
_DN_STYLES = ("label_down", "arrowdown", "triangledown", "label_upper_left", "label_upper_right")
_BULL_WORDS = re.compile(r"\b(buy|long|bull|bullish|al|alış)\b", re.I)
_BEAR_WORDS = re.compile(r"\b(sell|short|bear|bearish|sat|satış)\b", re.I)
DRAW_NEUTRAL = 2.0


def draw_sign(kind: str, obj) -> float:
    """Çizim olayı kodu: etikette stil (yukarı/aşağı), yoksa metin (buy/sell…) → ±1; diğerleri nötr (2)."""
    if kind != "label":
        return DRAW_NEUTRAL
    sty = str(getattr(obj, "_sty", "") or "")
    if sty.endswith(_UP_STYLES):
        return 1.0
    if sty.endswith(_DN_STYLES):
        return -1.0
    txt = str(getattr(obj, "text", "") or "")
    up, dn = bool(_BULL_WORDS.search(txt)), bool(_BEAR_WORDS.search(txt))
    return 1.0 if up and not dn else (-1.0 if dn and not up else DRAW_NEUTRAL)


def draw_color(obj) -> float:
    """Çizimin renk sınıfı: dolgu/ana renk; o nötr ya da yoksa yazı/kenar rengi."""
    cc = color_class(getattr(obj, "_col", None))
    if cc != cc or cc == 0.0:
        alt = color_class(getattr(obj, "_tcol", None))
        if alt == alt and alt != 0.0:
            return alt
    return cc


def color_class(c) -> float:
    """+1 yeşil tonu, −1 kırmızı tonu, 0 diğer, na renk yok."""
    if c is None or isna(c):
        return NA
    rgb = color_rgb(c)
    if rgb is None:
        return 0.0
    r, g, b = rgb
    if g > r + 30 and g >= b - 20:
        return 1.0
    if r > g + 30 and r >= b - 20:
        return -1.0
    return 0.0


def color_new(color, transp=0):
    rgb = color_rgb(color)
    if rgb is None:
        return color
    a = 255 - int(max(0, min(100, 0 if isna(transp) else transp)) * 2.55)
    return "#%02X%02X%02X%02X" % (*rgb, a)


def color_rgb_fn(red, green, blue, transp=0):
    try:
        return color_new("#%02X%02X%02X" % (int(red), int(green), int(blue)), transp)
    except (TypeError, ValueError):
        return None


def color_gradient(value, bottom_value, top_value, bottom_color, top_color):
    try:
        f = (value - bottom_value) / (top_value - bottom_value)
    except (TypeError, ZeroDivisionError):
        return None
    if isna(f):
        return None
    return top_color if f >= 0.5 else bottom_color


# ── UDT ──────────────────────────────────────────────────────────────────────
class UDTBase:
    __slots__ = ()
    _fields: tuple = ()
    _defaults: tuple = ()

    @classmethod
    def new(cls, *args, **kw):
        obj = cls.__new__(cls)
        for i, f in enumerate(cls._fields):
            if i < len(args):
                v = args[i]
            elif f in kw:
                v = kw[f]
            else:
                v = cls._defaults[i]
            object.__setattr__(obj, f, v)
        return obj

    def copy(self):
        obj = self.__class__.__new__(self.__class__)
        for f in self._fields:
            object.__setattr__(obj, f, getattr(self, f))
        return obj


def make_type(name, fields, defaults):
    return type(name, (UDTBase,), {"__slots__": tuple(fields), "_fields": tuple(fields), "_defaults": tuple(defaults)})


class EnumNS:
    def __init__(self, name, fields):
        self.name = name
        for f in fields:
            setattr(self, f, f"{name}.{f}")


def GA(obj, field):
    if obj is None:
        return NA
    try:
        return getattr(obj, field)
    except AttributeError:
        raise PineError(f"alan yok: {field}")


def SA(obj, field, value):
    if obj is None:
        raise PineError("na nesneye atama")
    setattr(obj, field, value)
    return value


# ── zaman ────────────────────────────────────────────────────────────────────
TF_SECONDS = {"1": 60, "5": 300, "15": 900, "30": 1800, "60": 3600, "240": 14400, "D": 86400, "1D": 86400, "W": 604800, "1W": 604800}


def tf_seconds(tf) -> int:
    if not isinstance(tf, str) or tf == "":
        return 0
    if tf in TF_SECONDS:
        return TF_SECONDS[tf]
    m = re.match(r"^(\d*)([SDWM]?)$", tf)
    if not m:
        return 0
    k = int(m.group(1) or 1)
    u = m.group(2)
    return k * {"": 60, "S": 1, "D": 86400, "W": 604800, "M": 2592000}[u]
