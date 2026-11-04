"""Pine AST → Python kaynak kodu (bar bar çalışan tek fonksiyon).

Üretilen kod:  def __run(rt, B): <hoist> <fonksiyonlar> for b in range(rt.n): <deyimler>; rt.commit()
Desteklenmeyen yapılar Unsupported ile işaretlenir (sessizce yanlış hesaplanmaz).
"""
from __future__ import annotations

import keyword

import pine_builtins as PB
from pine_parser import Node
from pine_runtime import Unsupported

BUILTIN_SERIES = {
    "open": "O[b]", "high": "H[b]", "low": "L[b]", "close": "C[b]", "volume": "V[b]", "time": "TM[b]",
    "time_close": "TC[b]", "hl2": "HL2[b]", "hlc3": "HLC3[b]", "ohlc4": "OHLC4[b]", "hlcc4": "HLCC4[b]",
    "bar_index": "b", "last_bar_index": "rt.last", "year": "YEAR[b]", "month": "MONTH[b]",
    "weekofyear": "WOY[b]", "dayofmonth": "DOM[b]", "dayofweek": "DOW[b]", "hour": "HOUR[b]",
    "minute": "MINUTE[b]", "second": "0", "timenow": "TM[-1]", "last_bar_time": "TM[-1]", "time_tradingday": "TM[b]",
}
BUILTIN_ARRAYS = {"open": "O", "high": "H", "low": "L", "close": "C", "volume": "V", "time": "TM", "time_close": "TC",
                  "hl2": "HL2", "hlc3": "HLC3", "ohlc4": "OHLC4", "hlcc4": "HLCC4"}
ATTR_VARS = {
    "barstate.isfirst": "(b == 0)", "barstate.islast": "(b == rt.last)", "barstate.isconfirmed": "True",
    "barstate.isrealtime": "False", "barstate.isnew": "True", "barstate.ishistory": "True",
    "barstate.islastconfirmedhistory": "(b == rt.last)",
    "syminfo.mintick": "rt.mintick", "syminfo.tickerid": "rt.ticker", "syminfo.ticker": "rt.ticker",
    "syminfo.prefix": "'BROKER'", "syminfo.root": "rt.ticker", "syminfo.description": "rt.ticker",
    "syminfo.currency": "'USD'", "syminfo.basecurrency": "'USD'", "syminfo.type": "rt.symtype",
    "syminfo.session": "'regular'", "syminfo.timezone": "rt.tz", "syminfo.pointvalue": "1.0",
    "syminfo.volumetype": "'tick'", "syminfo.mincontract": "1.0",
    "timeframe.period": "rt.tf", "timeframe.main_period": "rt.tf", "timeframe.multiplier": "rt.tf_mult",
    "timeframe.isintraday": "rt.intraday", "timeframe.isdaily": "rt.isdaily", "timeframe.isweekly": "False",
    "timeframe.ismonthly": "False", "timeframe.isminutes": "rt.intraday", "timeframe.isseconds": "False",
    "timeframe.isdwm": "(not rt.intraday)", "timeframe.isticks": "False",
    "strategy.position_size": "rt.pos", "strategy.long": "'strategy.long'", "strategy.short": "'strategy.short'",
    "strategy.equity": "(100000.0 + rt.bk.netprofit + rt.bk.openprofit())", "strategy.initial_capital": "100000.0",
    "strategy.netprofit": "rt.bk.netprofit", "strategy.openprofit": "rt.bk.openprofit()",
    "strategy.opentrades": "len(rt.bk.open)", "strategy.closedtrades": "len(rt.bk.closed)",
    "strategy.position_avg_price": "rt.pos_price", "strategy.wintrades": "rt.bk.stat('wintrades')",
    "strategy.losstrades": "rt.bk.stat('losstrades')", "strategy.eventrades": "rt.bk.stat('eventrades')",
    "strategy.grossprofit": "rt.bk.stat('grossprofit')", "strategy.grossloss": "rt.bk.stat('grossloss')",
    "strategy.position_entry_name": "rt.bk.stat('position_entry_name')",
    "math.pi": "3.141592653589793", "math.e": "2.718281828459045", "math.phi": "1.618033988749895",
    "math.rphi": "0.618033988749895",
    "line.all": "rt.all_lines", "box.all": "rt.all_boxes", "label.all": "rt.all_labels",
    "chart.bg_color": "'#131722'", "chart.fg_color": "'#D1D4DC'", "chart.is_standard": "True",
    "chart.left_visible_bar_time": "TM[0]", "chart.right_visible_bar_time": "TM[-1]",
}
for i, d in enumerate(("none", "pane", "data_window", "price_scale", "status_line", "pine_screener")):
    ATTR_VARS[f"display.{d}"] = str(0 if i == 0 else 1 << (i - 1))
ATTR_VARS["display.all"] = "31"
for i, d in enumerate(("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"), 1):
    ATTR_VARS[f"dayofweek.{d}"] = str(i)
TA_VARS = {"ta.tr": ("tr", "H[b], L[b], C[b]"), "ta.obv": ("obv", "C[b], V[b]"), "ta.accdist": ("accdist", "H[b], L[b], C[b], V[b]"),
           "ta.pvt": ("pvt", "C[b], V[b]"), "ta.vwap": ("vwap", "HLC3[b], DAYKEY[b], V[b]")}

# ta.* parametre listeleri (Pine sırası) ve u() argüman şablonu
TA_SPEC = {
    "sma": (["source", "length"], "{source}, {length}"), "ema": (["source", "length"], "{source}, {length}"),
    "rma": (["source", "length"], "{source}, {length}"), "wma": (["source", "length"], "{source}, {length}"),
    "hma": (["source", "length"], "{source}, {length}"), "swma": (["source"], "{source}"),
    "vwma": (["source", "length"], "{source}, {length}, V[b]"),
    "alma": (["series", "length", "offset", "sigma", "floor"], "{series}, {length}, {offset}, {sigma}, {floor}"),
    "stdev": (["source", "length", "biased"], "{source}, {length}, {biased}"),
    "variance": (["source", "length", "biased"], "{source}, {length}, {biased}"),
    "dev": (["source", "length"], "{source}, {length}"),
    "change": (["source", "length"], "{source}, {length}"), "mom": (["source", "length"], "{source}, {length}"),
    "roc": (["source", "length"], "{source}, {length}"),
    "crossover": (["source1", "source2"], "{source1}, {source2}"), "crossunder": (["source1", "source2"], "{source1}, {source2}"),
    "cross": (["source1", "source2"], "{source1}, {source2}"), "rsi": (["source", "length"], "{source}, {length}"),
    "atr": (["length"], "{length}, H[b], L[b], C[b]"), "tr": (["handle_na"], "H[b], L[b], C[b], {handle_na}"),
    "stoch": (["source", "high", "low", "length"], "{source}, {high}, {low}, {length}"),
    "macd": (["source", "fastlen", "slowlen", "siglen"], "{source}, {fastlen}, {slowlen}, {siglen}"),
    "bb": (["series", "length", "mult"], "{series}, {length}, {mult}"), "bbw": (["series", "length", "mult"], "{series}, {length}, {mult}"),
    "kc": (["series", "length", "mult", "useTrueRange"], "{series}, {length}, {mult}, H[b], L[b], C[b], {useTrueRange}"),
    "kcw": (["series", "length", "mult", "useTrueRange"], "{series}, {length}, {mult}, H[b], L[b], C[b], {useTrueRange}"),
    "cci": (["source", "length"], "{source}, {length}"), "mfi": (["series", "length"], "{series}, {length}, V[b]"),
    "dmi": (["diLength", "adxSmoothing"], "{diLength}, {adxSmoothing}, H[b], L[b], C[b]"),
    "sar": (["start", "inc", "max"], "{start}, {inc}, {max}, H[b], L[b]"),
    "supertrend": (["factor", "atrPeriod"], "{factor}, {atrPeriod}, H[b], L[b], C[b]"),
    "linreg": (["source", "length", "offset"], "{source}, {length}, {offset}"),
    "correlation": (["source1", "source2", "length"], "{source1}, {source2}, {length}"),
    "percentrank": (["source", "length"], "{source}, {length}"),
    "percentile_linear_interpolation": (["source", "length", "percentage"], "{source}, {length}, {percentage}"),
    "percentile_nearest_rank": (["source", "length", "percentage"], "{source}, {length}, {percentage}"),
    "median": (["source", "length"], "{source}, {length}"), "mode": (["source", "length"], "{source}, {length}"),
    "range": (["source", "length"], "{source}, {length}"), "cum": (["source"], "{source}"),
    "rising": (["source", "length"], "{source}, {length}"), "falling": (["source", "length"], "{source}, {length}"),
    "barssince": (["condition"], "{condition}"),
    "valuewhen": (["condition", "source", "occurrence"], "{condition}, {source}, {occurrence}"),
    "tsi": (["source", "short_length", "long_length"], "{source}, {short_length}, {long_length}"),
    "cmo": (["series", "length"], "{series}, {length}"), "wpr": (["length"], "{length}, H[b], L[b], C[b]"),
    "cog": (["source", "length"], "{source}, {length}"), "rci": (["source", "length"], "{source}, {length}"),
    "fixnan": (["source"], "{source}"), "obv": ([], "C[b], V[b]"), "accdist": ([], "H[b], L[b], C[b], V[b]"),
    "pvt": ([], "C[b], V[b]"),
}
TA_DEFAULTS = {"length": "1", "biased": "True", "offset": "0", "sigma": "6.0", "floor": "False", "occurrence": "0",
               "useTrueRange": "True", "handle_na": "False"}
TA_DEFAULT_BY_FN = {("alma", "offset"): "0.85", ("change", "length"): "1", ("mom", "length"): "1", ("roc", "length"): "1"}
SRC_DEFAULT = {"highest": "H[b]", "highestbars": "H[b]", "lowest": "L[b]", "lowestbars": "L[b]",
               "pivothigh": "H[b]", "pivotlow": "L[b]"}


V3_CONSTS = {"integer", "float", "bool", "string", "source", "resolution", "session", "symbol", "line", "stepline",
             "histogram", "cross", "area", "columns", "circles", "solid", "dotted", "dashed", "linebr", "areabr",
             "barmerge", "lookahead_on", "lookahead_off", "gaps_on", "gaps_off"}


def py(name: str) -> str:
    return "v_" + name


class FuncInfo:
    def __init__(self, node: Node, pyname: str):
        self.node, self.pyname = node, pyname
        self.params = [p[0] for p in node.params]


class Scope:
    """Fonksiyon kapsamı: yerel adlar ve çerçeve serileri."""
    def __init__(self, fn: FuncInfo | None):
        self.fn = fn
        self.locals: set[str] = set(fn.params) if fn else set()
        self.frame: set[str] = set()


_LIB_EXPORTS: dict = {}


def lib_exports(path: str) -> set:
    """İmport edilen kütüphanenin dışa aktardığı fonksiyon adları (kaynaktan; bulunamazsa boş küme)."""
    if path not in _LIB_EXPORTS:
        import re
        import pine_run                                   # döngüsel import: yalnız çağrı anında
        parts = path.split("/")
        idx = pine_run.lib_index()
        src = idx.get(f"{parts[0].lower()}/{parts[1].lower()}") if len(parts) > 1 else None
        if src is None and len(parts) > 1:
            alt = sorted(k for k in idx if k.split("/", 1)[1] == parts[1].lower())
            src = idx[alt[0]] if alt else None
        _LIB_EXPORTS[path] = set(re.findall(r"^\s*export\s+(?:method\s+)?(?:[\w.<>\[\]]+\s+)?(\w+)\s*\(", src or "",
                                            re.M)) if src else set()
    return _LIB_EXPORTS[path]


BUILTIN_NS = {k.split(".")[0] for k in PB.FUNCS if "." in k} | {
    "ta", "request", "ticker", "timeframe", "strategy", "syminfo", "chart", "polyline", "linefill", "table", "log",
    "runtime", "str", "math", "color"}
V3_DAYS = {"sunday": 1, "monday": 2, "tuesday": 3, "wednesday": 4, "thursday": 5, "friday": 6, "saturday": 7}
BOOL_OPS = ("<", ">", "<=", ">=", "==", "!=", "and", "or")


class Gen:
    def __init__(self, prog: Node, version: int, lib: bool = False):
        self.prog, self.version, self.lib = prog, version, lib
        self.out: list[str] = []
        self.ind = 0
        self.site = 0
        self.tmp = 0
        self.hoist: list[str] = []
        self.post: list[str] = []
        self.funcs: dict[str, FuncInfo] = {}
        self.overloads: dict[str, list] = {}
        self.dsite = 0                                  # çizim olayı sayacı (plot site'larından ayrı)
        self.methods: dict[str, list] = {}
        self.types: dict[str, Node] = {}
        self.enums: dict[str, Node] = {}
        self.imports: dict[str, str] = {}
        self.gvars: set[str] = set()
        self.gvar_mode: dict[str, str | None] = {}
        self.ghist: set[str] = set()
        self.scope: Scope | None = None
        self.loop_vars: list[str] = []
        self.overlay = False
        self.fn_hist: dict[str, set] = {}

    # ── yardımcılar ──
    def emit(self, line: str):
        self.out.append("    " * self.ind + line)

    def new_site(self) -> int:
        self.site += 1
        return self.site

    def new_tmp(self) -> str:
        self.tmp += 1
        return f"_t{self.tmp}"

    def ctx_expr(self, site: int) -> str:
        return f"(ctx + ({site},))" if self.scope else f"({site},)"

    # ── ön tarama ──
    def collect(self):
        for st in self.prog.body:
            if st.kind == "func":
                if st.method:
                    ftype = (st.params[0][1] or "") if st.params else ""
                    pyname = f"m_{st.name}_{len(self.methods.get(st.name, []))}"
                    self.methods.setdefault(st.name, []).append((ftype, pyname, st))
                elif st.name in self.funcs:                  # aşırı yükleme: aynı ad, farklı parametreler
                    ov = self.overloads.setdefault(st.name, [self.funcs[st.name]])
                    ov.append(FuncInfo(st, f"f_{st.name}__{len(ov)}"))
                else:
                    self.funcs[st.name] = FuncInfo(st, "f_" + st.name)
            elif st.kind == "type":
                self.types[st.name] = st
            elif st.kind == "enum":
                self.enums[st.name] = st
            elif st.kind == "import":
                self.imports[st.alias] = st.path
        for st in self.prog.body:
            if st.kind != "func":
                self._collect_globals(st)
        for st in self.prog.body:
            if st.kind == "func":
                hist = set()
                self._walk_hist(st, hist)
                self.fn_hist.setdefault(st.name + ("#m" if st.method else ""), set()).update(hist)
                self.ghist |= hist
            else:
                self._walk_hist(st, self.ghist)

    def _collect_globals(self, node):
        if not isinstance(node, Node):
            return
        if node.kind == "decl":
            self.gvars.add(node.name)
            if node.mode:
                self.gvar_mode[node.name] = node.mode
        elif node.kind == "tuple_decl":
            self.gvars.update(node.names)
        elif node.kind in ("for", "forin"):
            self.gvars.add(node.var)
            if node.kind == "forin" and node.idx:
                self.gvars.add(node.idx)
        for v in node.a.values():
            self._walk_any(v, self._collect_globals)

    def _walk_any(self, v, fn):
        if isinstance(v, Node):
            fn(v)
        elif isinstance(v, (list, tuple)):
            for x in v:
                self._walk_any(x, fn)
        elif isinstance(v, dict):
            for x in v.values():
                self._walk_any(x, fn)

    def _walk_hist(self, node, acc: set):
        if not isinstance(node, Node):
            self._walk_any(node, lambda n: self._walk_hist(n, acc))
            return
        if node.kind == "hist" and node.x.kind == "name":
            acc.add(node.x.id)
        for v in node.a.values():
            self._walk_any(v, lambda n: self._walk_hist(n, acc))

    # ── üretim ──
    def generate(self) -> str:
        self.collect()
        body_out = self.out
        self.out = []
        self.ind = 1
        for st in self.prog.body:
            if st.kind == "type":
                self.gen_type(st)
            elif st.kind == "enum":
                fields = [f[0] for f in st.fields]
                self.hoist.append(f"E_{st.name} = R.EnumNS({st.name!r}, {fields!r})")
            elif st.kind == "import":
                self.hoist.append(f"L_{st.alias} = rt.library({st.path!r})")
        for name in sorted(self.gvars):
            mode = self.gvar_mode.get(name)
            if name in self.ghist:
                self.hoist.append(f"S_{name} = rt.series(True)")
            else:
                self.hoist.append(f"{py(name)} = {'_U' if mode else 'NA'}")
        fn_code = []
        for st in self.prog.body:
            if st.kind == "func":
                self.out = []
                self.ind = 1
                self.gen_func(st)
                fn_code += self.out
        self.out = []
        self.ind = 2
        for st in self.prog.body:
            if st.kind in ("func", "type", "enum", "import"):
                continue
            if st.kind == "expr" and st.value.kind == "call" and self._path(st.value.fn) in ("indicator", "study", "strategy", "library"):
                if self._path(st.value.fn) == "strategy":
                    cfg = {k: self.expr(v) for k, v in st.value.kwargs.items()
                           if k in ("pyramiding", "process_orders_on_close", "default_qty_value")
                           and v.kind in ("num", "bool")}                 # yalnız sabitler (girdi değil)
                    self.hoist.append("rt.bk.config(" + ", ".join(f"{k}={v}" for k, v in cfg.items()) + ")")
                ov = st.value.kwargs.get("overlay")
                if ov is not None and ov.kind == "bool":
                    self.overlay = ov.v
                elif len(st.value.args) >= 3 and st.value.args[2].kind == "bool":
                    self.overlay = st.value.args[2].v
                continue
            start = len(self.out)
            self.gen_stmt(st)
            if self.lib:                                     # bir deyimin hatası importu düşürmesin
                body = self.out[start:]
                del self.out[start:]
                self.emit("try:")
                self.out += ["    " + ln for ln in body]
                self.emit("except Exception:")
                self.emit("    pass")
        loop = self.out
        head = ["def __run(rt, B, R, F, TA, NR):",
                "    NA = R.NA; T = R.T; DIV = R.DIV; MOD = R.MOD; ADD = R.ADD; HA = R.HA; HX = R.HX; GA = R.GA; SA = R.SA",
                "    _U = R._UNSET; PR = rt.prange",
                "    O, H, L, C, V, TM, TC = rt.O, rt.H, rt.L, rt.C, rt.V, rt.TM, rt.TC",
                "    HL2, HLC3, OHLC4, HLCC4, DAYKEY = rt.HL2, rt.HLC3, rt.OHLC4, rt.HLCC4, rt.DAYKEY",
                "    YEAR, MONTH, WOY, DOM, DOW, HOUR, MINUTE = rt.YEAR, rt.MONTH, rt.WOY, rt.DOM, rt.DOW, rt.HOUR, rt.MINUTE",
                "    b = 0"]
        head += ["    " + h for h in self.hoist]
        post = ["    " + p for p in self.post]
        if self.lib:
            head[0] = "def __lib(rt, B, R, F, TA, NR):"
            once = [f"    {py(g)} = NA" for g in sorted(self.gvars) if not self._is_series(g)]   # hata hâlinde tanımlı kalsın
            once += [ln[4:] for ln in loop]                      # global deyimler yüklemede bir kez
            exports = [f"'f_{n}': {fi.pyname}" for n, fi in self.funcs.items()]
            exports += [f"'f_{n}__{i}': {fi.pyname}" for n, ov in self.overloads.items() for i, fi in enumerate(ov) if i]
            exports += [f"'T_{n}': T_{n}" for n in self.types] + [f"'E_{n}': E_{n}" for n in self.enums]
            exports += [f"'v_{n}': {self.name_read(n)}" for n in sorted(self.gvars)]
            ret = ["    return {" + ", ".join(exports) + "}"]
            return "\n".join(head + fn_code + post + once + ret) + "\n"
        tail = ["    for b in range(rt.n):", "        rt.bar = b"] + (loop or ["        pass"]) + ["        rt.commit()"]
        return "\n".join(head + fn_code + post + tail) + "\n"

    def gen_type(self, st):
        fields = [f[0] for f in st.fields]
        defaults = [self.expr(f[2]) if f[2] is not None else ("NA" if (f[1] or "") in ("float", "int") else "None")
                    for f in st.fields]
        self.hoist.append(f"T_{st.name} = R.make_type({st.name!r}, {fields!r}, [{', '.join(defaults)}])")

    # ── fonksiyonlar ──
    def gen_func(self, st: Node):
        info = FuncInfo(st, "")
        if st.method:
            ftype, pyname, _ = next(m for m in self.methods[st.name] if m[2] is st)
            info.pyname = pyname
        else:
            info.pyname = next((fi.pyname for fi in self.overloads.get(st.name, []) if fi.node is st),
                               self.funcs[st.name].pyname)
        prev_scope = self.scope
        self.scope = Scope(info)
        hist = self.fn_hist.get(st.name + ("#m" if st.method else ""), set())
        locals_ = set(info.params)
        self._collect_locals(st.body, locals_)
        self.scope.locals = locals_
        self.scope.frame = {n for n in locals_ if n in hist} | self._var_locals(st.body)
        params = []
        defaults = []
        for pname, ptype, default in st.params:
            if default is not None:
                params.append(f"{py(pname)}=_U")
                defaults.append((pname, default))
            elif defaults:                                   # varsayılanlıdan sonra: Python sırası için na varsayılan
                params.append(f"{py(pname)}=_U")
                defaults.append((pname, None))
            else:
                params.append(py(pname))
        self.emit(f"def {info.pyname}(ctx, {', '.join(params)}):")
        self.ind += 1
        if self.lib:
            self.emit("b = rt.bar")
        for pname, default in defaults:
            self.emit(f"if {py(pname)} is _U: {py(pname)} = {'NA' if default is None else self.expr(default)}")
        for name in sorted(self.scope.frame):
            self.emit(f"S_{name} = rt.fs(ctx, {name!r})")
        for pname in info.params:
            if pname in self.scope.frame:
                self.emit(f"S_{pname}.set({py(pname)})")
        res = self.gen_block_value(st.body)
        self.emit(f"return {res}")
        self.ind -= 1
        if st.method:
            self.post.append(f"rt.add_method({st.name!r}, {ftype_of(st)!r}, {info.pyname})")
        self.scope = prev_scope

    def _collect_locals(self, body, acc: set):
        def walk(n):
            if not isinstance(n, Node):
                self._walk_any(n, walk)
                return
            if n.kind == "decl":
                acc.add(n.name)
            elif n.kind == "tuple_decl":
                acc.update(n.names)
            elif n.kind in ("for", "forin"):
                acc.add(n.var)
                if n.kind == "forin" and n.idx:
                    acc.add(n.idx)
            for v in n.a.values():
                self._walk_any(v, walk)
        self._walk_any(body, walk)

    def _var_locals(self, body) -> set:
        acc = set()

        def walk(n):
            if not isinstance(n, Node):
                self._walk_any(n, walk)
                return
            if n.kind == "decl" and n.mode:
                acc.add(n.name)
            for v in n.a.values():
                self._walk_any(v, walk)
        self._walk_any(body, walk)
        return acc

    # ── değer üreten bloklar ──
    def gen_block_value(self, body: list) -> str:
        """Bloğu üret, son deyimin değerini taşıyan ifadeyi döndür."""
        if not body:
            return "NA"
        for st in body[:-1]:
            self.gen_stmt(st)
        last = body[-1]
        if last.kind in ("if", "switch", "for", "forin", "while"):
            tmp = self.new_tmp()
            self.gen_valued(last, tmp)
            return tmp
        if last.kind == "expr":
            v = last.value
            if v.kind in ("if", "switch", "for", "forin", "while"):
                tmp = self.new_tmp()
                self.gen_valued(v, tmp)
                return tmp
            tmp = self.new_tmp()
            self.emit(f"{tmp} = {self.expr(v)}")
            return tmp
        if last.kind == "decl":
            self.gen_stmt(last)
            return self.name_read(last.name)
        if last.kind == "tuple_decl":
            self.gen_stmt(last)
            return "(" + ", ".join(self.name_read(n) for n in last.names) + ",)"
        if last.kind == "assign" and last.target.kind == "name":
            self.gen_stmt(last)
            return self.name_read(last.target.id)
        self.gen_stmt(last)
        return "NA"

    def gen_valued(self, node: Node, target: str):
        self.emit(f"{target} = NA")
        if node.kind == "if":
            self.emit(f"if {self.truth(node.cond)}:")
            self._valued_branch(node.body, target)
            if node.orelse:
                self.emit("else:")
                self._valued_branch(node.orelse, target)
        elif node.kind == "switch":
            self._gen_switch(node, target)
        elif node.kind in ("for", "forin", "while"):
            self.gen_loop(node, target)
        else:
            self.emit(f"{target} = {self.expr(node)}")

    def _valued_branch(self, body, target):
        self.ind += 1
        v = self.gen_block_value(body)
        self.emit(f"{target} = {v}")
        self.ind -= 1

    # ── deyimler ──
    def gen_block(self, body):
        self.ind += 1
        n0 = len(self.out)
        for st in body:
            self.gen_stmt(st)
        if len(self.out) == n0:
            self.emit("pass")
        self.ind -= 1

    def gen_stmt(self, st: Node):
        k = st.kind
        if k == "decl":
            self.gen_decl(st.name, st.mode, st.value)
        elif k == "tuple_decl":
            tmp = self.new_tmp()
            self.gen_value_into(st.value, tmp)
            self.emit(f"{tmp} = R.TUP({tmp}, {len(st.names)})")
            for i, n in enumerate(st.names):
                self.name_write(n, f"{tmp}[{i}]")
        elif k == "assign":
            self.gen_assign(st)
        elif k == "expr":
            v = st.value
            if v.kind == "if":
                self.gen_if(v)
            elif v.kind == "switch":
                self._gen_switch(v, None)
            elif v.kind in ("for", "forin", "while"):
                self.gen_loop(v, None)
            else:
                self.emit(self.expr(v))
        elif k == "if":
            self.gen_if(st)
        elif k == "switch":
            self._gen_switch(st, None)
        elif k in ("for", "forin", "while"):
            self.gen_loop(st, None)
        elif k == "break":
            self.emit("break")
        elif k == "continue":
            self.emit("continue")
        elif k in ("func", "type", "enum", "import"):
            raise Unsupported(f"iç içe {k}")
        else:
            raise Unsupported(f"deyim {k}")

    def gen_value_into(self, value: Node, tmp: str):
        if value.kind in ("if", "switch", "for", "forin", "while"):
            self.gen_valued(value, tmp)
        else:
            self.emit(f"{tmp} = {self.expr(value)}")

    def gen_decl(self, name, mode, value):
        if value.kind in ("if", "switch", "for", "forin", "while"):
            tmp = self.new_tmp()
            if mode:
                guard = self._var_guard(name)
                self.emit(f"if {guard}:")
                self.ind += 1
                self.gen_valued(value, tmp)
                self.name_write(name, tmp, init=True)
                self.ind -= 1
                self._var_keep(name)
                return
            self.gen_valued(value, tmp)
            self.name_write(name, tmp)
            return
        if mode:
            guard = self._var_guard(name)
            self.emit(f"if {guard}:")
            self.ind += 1
            self.name_write(name, self.expr(value), init=True)
            self.ind -= 1
            self._var_keep(name)
            return
        self.name_write(name, self.expr(value))

    def _is_series(self, name) -> bool:
        if self.scope and name in self.scope.locals:
            return name in self.scope.frame
        return name in self.ghist and name in self.gvars

    def _var_guard(self, name) -> str:
        if self._is_series(name):
            return f"not S_{name}.init"
        return f"{py(name)} is _U"

    def _var_keep(self, name):
        if self._is_series(name):
            self.emit(f"S_{name}.touched = True")

    def name_write(self, name, value_expr, init=False):
        if self._is_series(name):
            self.emit(f"S_{name}.set({value_expr})")
            if init:
                self.emit(f"S_{name}.init = True")
        else:
            self.emit(f"{py(name)} = {value_expr}")

    def name_read(self, name) -> str:
        if self._is_series(name):
            return f"S_{name}.v"
        return py(name)

    def gen_assign(self, st):
        tgt, op = st.target, st.op
        if st.value.kind in ("if", "switch", "for", "forin", "while"):
            tmp = self.new_tmp()
            self.gen_valued(st.value, tmp)
            val = tmp
        else:
            val = self.expr(st.value)
        if tgt.kind == "name":
            cur = self.name_read(tgt.id)
            new = self._compound(cur, op, val)
            self.name_write(tgt.id, new)
        elif tgt.kind == "attr":
            obj = self.expr(tgt.obj)
            cur = f"GA({obj}, {tgt.name!r})"
            self.emit(f"SA({obj}, {tgt.name!r}, {self._compound(cur, op, val)})")
        elif tgt.kind == "tuple":
            tmp = self.new_tmp()
            self.emit(f"{tmp} = {val}")
            for i, it in enumerate(tgt.items):
                self.name_write(it.id, f"{tmp}[{i}]")
        else:
            raise Unsupported("atama hedefi")

    @staticmethod
    def _compound(cur, op, val):
        return {":=": val, "+=": f"ADD({cur}, {val})", "-=": f"({cur} - {val})", "*=": f"({cur} * {val})",
                "/=": f"DIV({cur}, {val})", "%=": f"MOD({cur}, {val})"}[op]

    def gen_if(self, node):
        self.emit(f"if {self.truth(node.cond)}:")
        self.gen_block(node.body)
        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and orelse[0].kind == "if":
                nxt = orelse[0]
                self.emit(f"elif {self.truth(nxt.cond)}:")
                self.gen_block(nxt.body)
                orelse = nxt.orelse
            else:
                self.emit("else:")
                self.gen_block(orelse)
                break

    def _gen_switch(self, node, target):
        subj = None
        if node.subject is not None:
            subj = self.new_tmp()
            self.emit(f"{subj} = {self.expr(node.subject)}")
        first = True
        for key, body in node.cases:
            if key is None:
                if first:
                    self.emit("if True:")
                else:
                    self.emit("else:")
            else:
                cond = f"({subj} == {self.expr(key)})" if subj else self.truth(key)
                self.emit(f"{'if' if first else 'elif'} {cond}:")
            if target:
                self._valued_branch(body, target)
            else:
                self.gen_block(body)
            first = False

    def gen_loop(self, node, target):
        if target:
            self.emit(f"{target} = NA")
        if node.kind == "for":
            step = self.expr(node.step) if node.step is not None else "None"
            self.emit(f"for {self.loop_target(node.var)} in PR({self.expr(node.start)}, {self.expr(node.end)}, {step}):")
        elif node.kind == "forin":
            coll = self.expr(node.coll)
            if node.idx:
                self.emit(f"for {self.loop_target(node.idx)}, {self.loop_target(node.var)} in enumerate(rt.iter({coll})):")
            else:
                self.emit(f"for {self.loop_target(node.var)} in rt.iter({coll}):")
        else:
            g = self.new_tmp()
            self.emit(f"{g} = 0")
            self.emit(f"while {self.truth(node.cond)}:")
            self.ind += 1
            self.emit(f"{g} += 1")
            self.emit(f"if {g} > 200000: raise R.PineError('sonsuz döngü')")
            self.ind -= 1
        if target:
            self._valued_branch(node.body, target)
        else:
            self.gen_block(node.body)
        if node.kind != "while":
            pass

    def loop_target(self, name) -> str:
        if self._is_series(name):
            raise Unsupported("seri döngü değişkeni")
        return py(name)

    # ── ifadeler ──
    def _path(self, n: Node) -> str | None:
        if n.kind == "name":
            return n.id
        if n.kind == "attr":
            p = self._path(n.obj)
            return None if p is None else p + "." + n.name
        return None

    def truth(self, n: Node) -> str:
        """Pine doğruluk değeri; sonucu zaten bool olan ifadelerde T() sarmalı atlanır (sıcak yol)."""
        x = self.expr(n)
        if n.kind == "bool" or (n.kind == "bin" and n.op in BOOL_OPS) or (n.kind == "unary" and n.op == "not"):
            return x
        return f"T({x})"

    def expr(self, n: Node) -> str:
        k = n.kind
        if k == "num":
            return repr(n.v)
        if k == "str":
            return repr(n.v)
        if k == "bool":
            return "True" if n.v else "False"
        if k == "na":
            return "NA"
        if k == "color":
            return repr(n.v)
        if k == "name":
            return self.resolve_name(n.id)
        if k == "hist":
            return self.resolve_hist(n)
        if k == "bin":
            return self.binop(n)
        if k == "unary":
            if n.op == "not":
                return f"(not {self.truth(n.x)})"
            x = self.expr(n.x)
            return f"(-{x})" if n.op == "-" else x
        if k == "ternary":
            return f"({self.expr(n.t)} if {self.truth(n.cond)} else {self.expr(n.f)})"
        if k == "tuple":
            return "(" + ", ".join(self.expr(i) for i in n.items) + ",)"
        if k == "call":
            return self.call(n)
        if k == "attr":
            return self.attr(n)
        raise Unsupported(f"ifade içinde {k}")

    def binop(self, n):
        op = n.op
        if op in ("and", "or"):
            return f"({self.truth(n.l)} {op} {self.truth(n.r)})"
        a, b = self.expr(n.l), self.expr(n.r)
        if op == "/":
            return f"DIV({a}, {b})"
        if op == "%":
            return f"MOD({a}, {b})"
        if op == "+":
            if n.l.kind == "str" or n.r.kind == "str":
                return f"ADD({a}, {b})"
            return f"({a} + {b})"
        return f"({a} {op} {b})"

    def resolve_name(self, name: str) -> str:
        if self.scope and name in self.scope.locals:
            return self.name_read(name)
        if name in self.gvars:
            return self.name_read(name)
        if name in BUILTIN_SERIES:
            return BUILTIN_SERIES[name]
        if name in self.funcs:
            raise Unsupported("fonksiyon değer olarak")
        if name in ("ta", "math"):
            raise Unsupported(f"çıplak ad alanı {name}")
        if self.version < 4 and name in PB.R.NAMED_COLORS:
            return repr(PB.R.NAMED_COLORS[name])
        if self.version < 4 and name == "n":
            return "b"
        if name in V3_CONSTS:
            return repr(name)
        if name in ("bid", "ask"):
            return "C[b]"
        if name in ("tickerid", "ticker"):
            return "rt.ticker"
        if self.version < 5 and "timeframe." + name in ATTR_VARS:     # isintraday, isdaily, ismonthly …
            return ATTR_VARS["timeframe." + name]
        if self.version < 5 and name in V3_DAYS:
            return str(V3_DAYS[name])
        if name == "period":
            return "rt.tf"
        if name == "interval":
            return "rt.tf_mult"
        if self.version < 5 and name in PB.V4 and name in ("tr", "obv", "accdist", "pvt", "vwap"):
            return self.ta_var("ta." + name)
        raise Unsupported(f"bilinmeyen ad {name}")

    def resolve_hist(self, n: Node) -> str:
        x = n.x
        idx = self.expr(n.n)
        if x.kind == "name":
            name = x.id
            local = self.scope and name in self.scope.locals
            if (local or name in self.gvars) and self._is_series(name):
                return f"S_{name}.h({idx})"
            if not local and name not in self.gvars:
                if name in BUILTIN_ARRAYS:
                    return f"HA({BUILTIN_ARRAYS[name]}, b, {idx})"
                if name == "bar_index":
                    return f"(b - {idx})"
        site = self.new_site()
        sname = f"HS{site}"
        val = self.expr(x)
        if self.scope:
            return f"HX(rt.fs(ctx, {sname!r}), {val}, {idx})"
        self.hoist.append(f"{sname} = rt.series(False)")
        return f"HX({sname}, {val}, {idx})"

    def attr(self, n: Node) -> str:
        path = self._path(n)
        if path is not None:
            root = path.split(".")[0]
            local = self.scope and root in self.scope.locals
            shadow_ns = root in PB.CONST_NS and path.count(".") == 1 and (path in ATTR_VARS or root not in ("line", "box", "label", "table", "map", "array", "matrix", "chart"))
            if (not local and root not in self.gvars) or shadow_ns:
                if path in ATTR_VARS:
                    return ATTR_VARS[path]
                if path in TA_VARS:
                    return self.ta_var(path)
                if root in self.enums:
                    return repr(path)
                if root in self.imports:
                    if path.count(".") >= 2:                 # kütüphane enum üyesi: ut.Theme.DARK → 'Theme.DARK'
                        return repr(path.split(".", 1)[1])
                    return f"GA(L_{root}, {n.name!r})"
                if path.startswith("color.") and path[6:] in PB.R.NAMED_COLORS:
                    return repr(PB.R.NAMED_COLORS[path[6:]])
                if root in PB.CONST_NS or root in ("currency",):
                    return repr(path)
        return f"GA({self.expr(n.obj)}, {n.name!r})"

    def ta_var(self, path):
        fname, args = TA_VARS[path]
        return f"{self.ta_state(fname)}.u({args})"

    def ta_state(self, fname: str, cls_key: str | None = None) -> str:
        site = self.new_site()
        key = cls_key or fname
        if self.scope:
            return f"rt.st(ctx, {site}, TA[{key!r}])"
        self.hoist.append(f"TS{site} = TA[{key!r}]()")
        return f"TS{site}"

    def _bind(self, params: list[str], n: Node, defaults: dict) -> dict:
        vals = {}
        for i, a in enumerate(n.args):
            if i < len(params):
                vals[params[i]] = self.expr(a)
        for k, v in n.kwargs.items():
            vals[k] = self.expr(v)
        for p in params:
            if p not in vals:
                if p in defaults:
                    vals[p] = defaults[p]
                else:
                    raise Unsupported(f"eksik argüman {p}")
        return vals

    def call(self, n: Node) -> str:
        if n.fn.kind == "na":                              # na(x) — 'na' anahtar kelime olarak ayrıştırılır
            return f"R.isna({self.expr(n.args[0])})" if n.args else "NA"
        path = self._path(n.fn)
        if n.fn.kind == "name":
            return self.call_path(path, n)                 # fonksiyonlar değişkenlerden ayrı ad alanında
        if path is not None:
            root = path.split(".")[0]
            local = self.scope and root in self.scope.locals
            if (not local and root not in self.gvars) or path in PB.FUNCS or \
                    (root in BUILTIN_NS and n.fn.name not in self.methods):
                return self.call_path(path, n)             # yerleşik ad alanı, aynı adlı değişkene baskın
        # yöntem çağrısı obj.m(...)
        if n.fn.kind == "attr":
            obj = self.expr(n.fn.obj)
            site = self.new_site()
            args = ", ".join(self.expr(a) for a in n.args)
            kw = ", ".join(f"{k!r}: {self.expr(v)}" for k, v in n.kwargs.items())
            return f"rt.callm({obj}, {n.fn.name!r}, {self.ctx_expr(site)}, ({args}{',' if args else ''}), {{{kw}}})"
        raise Unsupported("çağrılabilir olmayan ifade")

    def _args(self, n: Node, pre: str = "") -> str:
        parts = [pre] if pre else []
        parts += [self.expr(a) for a in n.args]
        for k, v in n.kwargs.items():
            kk = k if not keyword.iskeyword(k) else k + "_"
            parts.append(f"{kk}={self.expr(v)}")
        return ", ".join(parts)

    def _overload(self, path: str, n: Node) -> FuncInfo:
        """Aşırı yüklemeyi argüman sayısıyla seç (tam eşleşme > varsayılanlarla sığan > ilk)."""
        k = len(n.args) + len(n.kwargs)
        ovs = self.overloads[path]
        exact = [fi for fi in ovs if len(fi.params) == k]
        if exact:
            return exact[0]
        fits = [fi for fi in ovs if sum(1 for p in fi.node.params if p[2] is None) <= k <= len(fi.params)]
        return fits[0] if fits else ovs[0]

    def call_path(self, path: str, n: Node) -> str:
        if path in self.funcs:
            site = self.new_site()
            info = self._overload(path, n) if path in self.overloads else self.funcs[path]
            args = [self.expr(a) for a in n.args] + [f"{py(k)}={self.expr(v)}" for k, v in n.kwargs.items()]
            return f"{info.pyname}({', '.join([self.ctx_expr(site)] + args)})"
        root = path.split(".")[0]
        if root in self.types and path.count(".") == 1:
            meth = path.split(".")[1]
            if meth == "new":
                return f"T_{root}.new({self._args(n)})"
            if meth == "copy":
                return f"({self.expr(n.args[0])}).copy()"
        if root in self.imports and not (root in BUILTIN_NS and path.count(".") == 1
                                          and (path in PB.FUNCS or (root == "ta" and path[3:] in TA_SPEC))
                                          and path.split(".")[1] not in lib_exports(self.imports[root])):
            site = self.new_site()
            return f"rt.libcall(L_{root}, {path.split('.', 1)[1]!r}, {self.ctx_expr(site)}, ({', '.join(self.expr(a) for a in n.args)}{',' if n.args else ''}), {{{', '.join(f'{k!r}: {self.expr(v)}' for k, v in n.kwargs.items())}}})"
        if path in self.methods and n.args:              # metot fonksiyon biçiminde: m(x, ...) ≡ x.m(...)
            site = self.new_site()
            obj = self.expr(n.args[0])
            args = ", ".join(self.expr(a) for a in n.args[1:])
            kw = ", ".join(f"{k!r}: {self.expr(v)}" for k, v in n.kwargs.items())
            return f"rt.callm({obj}, {path!r}, {self.ctx_expr(site)}, ({args}{',' if args else ''}), {{{kw}}})"
        if self.version < 5 and path in PB.V4:
            path = PB.V4[path]
        if path.startswith("ta."):
            return self.ta_call(path[3:], n)
        if path in ("math.sum",):
            vals = self._bind(["source", "length"], n, {})
            return f"{self.ta_state('math_sum')}.u({vals['source']}, {vals['length']})"
        if path == "fixnan":
            vals = self._bind(["source"], n, {})
            return f"{self.ta_state('fixnan')}.u({vals['source']})"
        if path in ("request.security", "security"):
            if "resolution" in n.kwargs:                   # v3/v4 argüman adı
                n.kwargs["timeframe"] = n.kwargs.pop("resolution")
            vals = self._bind(["symbol", "timeframe", "expression", "gaps", "lookahead"], n,
                              {"gaps": "None", "lookahead": "None"})
            site = self.new_site()
            return f"rt.sec({site}, {vals['symbol']}, {vals['timeframe']}, (lambda: {vals['expression']}), {vals['lookahead']})"
        if path == "request.security_lower_tf":
            vals = self._bind(["symbol", "timeframe", "expression"], n, {})
            site = self.new_site()
            en = n.args[2] if len(n.args) > 2 else n.kwargs.get("expression")
            arity = len(en.items) if en is not None and en.kind == "tuple" else 0      # [a, b] → dizi demeti
            return (f"rt.sec_ltf({site}, {vals['symbol']}, {vals['timeframe']}, (lambda: {vals['expression']}), "
                    f"{arity})")
        if path in ("ticker.heikinashi", "heikinashi"):
            return "'HA:' + rt.ticker"
        if path in ("ticker.new", "ticker.modify", "ticker.standard", "ticker.inherit"):
            for a in n.args:
                self.expr(a)
            return "rt.ticker"
        if path in ("request.earnings", "request.financial", "request.dividends", "request.splits", "financial",
                    "earnings", "dividends", "splits"):
            for a in n.args:
                self.expr(a)
            return "NA"                                     # NDX/DAX/XAU/USOIL hisse değil → veri yok (na)
        if path == "request.currency_rate":
            vals = self._bind(["from", "to"], n, {})
            return f"(1.0 if {vals['from']} == {vals['to']} else NA)"
        if path in ("tickerid", "heikenashi"):
            for a in n.args:
                self.expr(a)
            return "rt.ticker" if path == "tickerid" else "'HA:' + rt.ticker"
        if path.startswith("request.") or path.startswith("ticker."):
            raise Unsupported(path)
        if path in ("renko", "kagi", "linebreak", "pointfigure"):
            raise Unsupported(path)
        if path in ("time", "time_close"):
            return f"B.time_fn(rt, b, {self._args(n)})" if n.args or n.kwargs else ("TM[b]" if path == "time" else "TC[b]")
        if path in ("hour", "minute", "dayofweek", "dayofmonth", "month", "year", "weekofyear", "second"):
            return f"rt.timepart({path!r}, {self._args(n)})"
        if path == "timeframe.change":
            site = self.new_site()
            return f"B.timeframe_change(rt, {self.ctx_expr(site) if self.scope else '()'}, {site}, {self._args(n)})"
        if path == "timeframe.in_seconds":
            return f"rt.tf_seconds({self._args(n)})"
        if path in ("na", "nz") and len(n.args) == 1 and not n.kwargs and path == "na":
            return f"R.isna({self.expr(n.args[0])})"
        if path in ("line.new", "box.new", "label.new"):
            self.dsite += 1
            dsite = f"'L{self.dsite}'" if self.lib else str(self.dsite)
            return f"rt.draw({dsite}, {path.split('.')[0]!r}, F[{path!r}]({self._args(n)}))"
        if path in PB.NEED_RT:
            site = self.new_site()
            return f"NR[{path!r}]({self._args(n, f'rt, {site}')})"
        if path in PB.FUNCS:
            return f"F[{path!r}]({self._args(n)})"
        if path.startswith("array.new") or path.startswith("matrix.new") or path.startswith("map.new"):
            base = path.split("<")[0]
            if base in PB.FUNCS:
                return f"F[{base!r}]({self._args(n)})"
        if any(path.startswith(p) for p in PB.NOOP_PREFIX) or path.split(".")[0] in ("table", "polyline", "linefill", "log"):
            for a in n.args:
                self.expr(a)
            return "None"
        if path in ("line.new", "box.new", "label.new"):
            return f"F[{path!r}]({self._args(n)})"
        if path.startswith(("line.all.", "box.all.", "label.all.")) and path.count(".") == 2:
            site = self.new_site()
            coll = ATTR_VARS[path.rsplit(".", 1)[0]]
            args = ", ".join(self.expr(a) for a in n.args)
            return f"rt.callm({coll}, {path.rsplit('.', 1)[1]!r}, {self.ctx_expr(site)}, ({args}{',' if args else ''}), {{}})"
        if path.startswith(("strategy.opentrades.", "strategy.closedtrades.")) and path.count(".") == 2:
            return f"rt.bk.trade_fn({path!r}, {self._args(n) or '0'})"
        raise Unsupported(f"bilinmeyen fonksiyon {path}")

    def ta_call(self, fname: str, n: Node) -> str:
        if fname == "vwap":
            vals = self._bind(["source", "anchor", "stdev_mult"], n, {"anchor": "None", "stdev_mult": "None"})
            site = self.new_site()
            key = f"rt.anchor_key({self.ctx_expr(site)}, {vals['anchor']})" if vals["anchor"] != "None" else "DAYKEY[b]"
            sm = "" if vals["stdev_mult"] == "None" else f", {vals['stdev_mult']}"
            return f"{self.ta_state('vwap')}.u({vals['source']}, {key}, V[b]{sm})"
        if fname in ("max", "min"):
            vals = self._bind(["source"], n, {})
            return f"{self.ta_state('cum_' + fname)}.u({vals['source']})"
        if fname not in TA_SPEC and fname not in SRC_DEFAULT:
            raise Unsupported(f"ta.{fname}")
        if fname in SRC_DEFAULT:
            if fname.startswith("pivot"):
                params = ["source", "leftbars", "rightbars"]
                if len(n.args) + len(n.kwargs) == 2 and "source" not in n.kwargs:
                    vals = {"source": SRC_DEFAULT[fname]}
                    vals.update(self._bind(["leftbars", "rightbars"], n, {}))
                else:
                    vals = self._bind(params, n, {})
                return f"{self.ta_state(fname)}.u({vals['source']}, {vals['leftbars']}, {vals['rightbars']})"
            if len(n.args) + len(n.kwargs) == 1 and "source" not in n.kwargs:
                vals = {"source": SRC_DEFAULT[fname], "length": self.expr(n.args[0]) if n.args else self.expr(n.kwargs["length"])}
            else:
                vals = self._bind(["source", "length"], n, {})
            return f"{self.ta_state(fname)}.u({vals['source']}, {vals['length']})"
        params, tmpl = TA_SPEC[fname]
        defaults = {p: TA_DEFAULT_BY_FN.get((fname, p), TA_DEFAULTS.get(p)) for p in params}
        defaults = {k: v for k, v in defaults.items() if v is not None}
        if fname == "vwap" or (fname == "tr" and not n.args and not n.kwargs):
            pass
        vals = self._bind(params, n, defaults)
        return f"{self.ta_state(fname)}.u({tmpl.format(**vals)})"


def ftype_of(st: Node) -> str:
    return (st.params[0][1] or "") if st.params else ""


def transpile_library(prog: Node, version: int) -> str:
    return Gen(prog, version, lib=True).generate()


def transpile(prog: Node, version: int) -> tuple[str, bool]:
    g = Gen(prog, version)
    code = g.generate()
    return code, g.overlay
