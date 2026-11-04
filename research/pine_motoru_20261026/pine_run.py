"""Bir Pine scriptini OHLCV verisinde çalıştır → çıktı kanalları (plot/shape/alert/renk/strateji girişleri).

run_script(source, df, tf, sym) → dict(status, error, outputs, overlay, seconds)
status: ok | parse_error | unsupported | runtime_error | timeout
"""
from __future__ import annotations

import math
import time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import pine_broker
import pine_builtins as PB
import pine_parser as P
import pine_runtime as R
import pine_ta as TAm
import pine_transpile as TR

SYM = {"NDX": ("NAS100", "America/New_York", 0.1, "index"), "DAX": ("GER40", "Europe/Berlin", 0.1, "index"),
       "XAU": ("XAUUSD", "America/New_York", 0.01, "commodity"), "USOIL": ("USOIL", "America/New_York", 0.001, "commodity")}
TF_PINE = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "4h": "240", "1d": "D"}


class Timeout(R.PineError):
    pass


class NeedHTF(Exception):
    def __init__(self, key):
        super().__init__(str(key))
        self.tf = key              # (tür, tf): tür 'chart' | 'ha'


PRIM_TYPES = {"str": ("string", "color"), "float": ("float", "int"), "int": ("int", "float"), "bool": ("bool",)}
LTF_NAME = {"1": "1m", "5": "5m", "15": "15m", "30": "30m", "60": "1h", "240": "4h"}


def norm_tf(tf):
    if tf is None or (isinstance(tf, float) and tf != tf):
        return ""
    if isinstance(tf, float) and tf == int(tf):        # 240.0 → "240"
        tf = int(tf)
    tf = str(tf)
    if tf.endswith(".0") and tf[:-2].isdigit():
        tf = tf[:-2]
    return {"1D": "D", "1W": "W", "1M": "M", "60": "60"}.get(tf, tf)


class RT:
    def __init__(self, df: pd.DataFrame, tf: str, sym: str, deadline: float):
        n = len(df)
        self.n, self.last, self.bar = n, n - 1, 0
        f = lambda c: [float(x) for x in df[c].values]
        self.O, self.H, self.L, self.C = f("open"), f("high"), f("low"), f("close")
        self.V = f("volume") if "volume" in df.columns else [1.0] * n
        ts = pd.to_datetime(df.ts, utc=True)
        ms = (ts.astype("int64") // 1_000_000).astype(float).tolist()
        self.TM = ms
        sec = R.tf_seconds(TF_PINE[tf])
        self.TC = [t + sec * 1000 for t in ms]
        self.HL2 = [(h + l) / 2 for h, l in zip(self.H, self.L)]
        self.HLC3 = [(h + l + c) / 3 for h, l, c in zip(self.H, self.L, self.C)]
        self.OHLC4 = [(o + h + l + c) / 4 for o, h, l, c in zip(self.O, self.H, self.L, self.C)]
        self.HLCC4 = [(h + l + 2 * c) / 4 for h, l, c in zip(self.H, self.L, self.C)]
        ticker, tz, mintick, stype = SYM[sym]
        self.ticker, self.tz, self.mintick, self.symtype = ticker, tz, mintick, stype
        loc = ts.dt.tz_convert(ZoneInfo(tz))
        self.YEAR, self.MONTH, self.DOM = loc.dt.year.tolist(), loc.dt.month.tolist(), loc.dt.day.tolist()
        self.DOW = ((loc.dt.dayofweek + 1) % 7 + 1).tolist()          # Pine: 1=Pazar … 7=Cumartesi
        self.HOUR, self.MINUTE = loc.dt.hour.tolist(), loc.dt.minute.tolist()
        self.WOY = loc.dt.isocalendar().week.astype(int).tolist()
        self.DAYKEY = (loc.dt.year * 10000 + loc.dt.month * 100 + loc.dt.day).tolist()
        self.tf = TF_PINE[tf]
        self.tf_mult = int(self.tf) if self.tf.isdigit() else 1
        self.intraday = self.tf.isdigit()
        self.isdaily = self.tf == "D"
        self.series_all: list = []
        self.states: dict = {}
        self.frames: dict = {}
        self.outputs: dict = {}
        self.methods: dict = {}
        self.pos, self.pos_price = 0.0, R.NA
        self.bk = pine_broker.Broker(self)
        _dr = R.draw_reset()
        self.all_lines, self.all_boxes, self.all_labels = _dr["line"], _dr["box"], _dr["label"]
        self.deadline = deadline
        self.anchors: dict = {}
        self.pass_key = None          # alternatif geçişte (tür, tf)
        self.chart_tf = TF_PINE[tf]
        self.sec_rec: dict = {}       # HTF geçişi: site → değer listesi
        self.sec_maps: dict = {}      # grafik geçişi: tf → {"vals": {site: list}, "idx": list, "last": list}
        self.flags: set = set()

    # durum
    def series(self, always=True):
        s = R.Series(always)
        self.series_all.append(s)
        return s

    def fs(self, ctx, name):
        key = (ctx, name)
        s = self.frames.get(key)
        if s is None:
            s = R.Series(False)
            self.frames[key] = s
            self.series_all.append(s)
        return s

    def st(self, ctx, site, cls):
        key = (ctx, site)
        s = self.states.get(key)
        if s is None:
            s = cls()
            self.states[key] = s
        return s

    def commit(self):
        for s in self.series_all:
            if s.always or s.touched:
                s.commit()
        if self.bk.active and self.bar + 1 < self.n:      # strategy: sonraki barın açılış/bar içi dolumları
            self.bk.process(self.bar + 1)
        if self.bar % 256 == 0 and time.time() > self.deadline:
            raise Timeout("zaman aşımı")

    # çıktılar
    def out(self, site, kind, title, value, color):
        rec = self.outputs.get(site)
        if rec is None:
            rec = self.outputs[site] = {"kind": kind, "title": title, "v": np.full(self.n, np.nan, np.float32),
                                        "c": np.full(self.n, np.nan, np.float32)}
        v = R.NUM(value)
        try:
            rec["v"][self.bar] = float(v) if not isinstance(v, str) else np.nan
        except (TypeError, ValueError):
            pass
        if color is not None:
            rec["c"][self.bar] = R.color_class(color)

    def draw(self, site, kind, obj):
        """label/box/line.new olayı (oluşturulduğu bar = nedensel); nesneyi aynen döndürür."""
        if isinstance(obj, R.Drawing):
            key = f"draw{site}"
            rec = self.outputs.get(key)
            if rec is None:
                title = str(getattr(obj, "text", "") or "")[:30] if kind == "label" else ""
                rec = self.outputs[key] = {"kind": kind, "title": title, "v": np.full(self.n, np.nan, np.float32),
                                           "c": np.full(self.n, np.nan, np.float32)}
            rec["v"][self.bar] = R.draw_sign(kind, obj)
            rec["c"][self.bar] = R.draw_color(obj)
        return obj

    def event(self, site, kind, message):
        self.out(site, kind, str(message)[:60], 1.0, None)

    def entry(self, site, d, id_):
        key = f"entry:{site}"
        rec = self.outputs.get(key)
        if rec is None:
            rec = self.outputs[key] = {"kind": "entry", "title": str(id_)[:60], "v": np.full(self.n, np.nan, np.float32),
                                       "c": np.full(self.n, np.nan, np.float32)}
        rec["v"][self.bar] = d

    # yardımcılar
    def prange(self, start, end, step=None):
        if R.isna(start) or R.isna(end):
            return ()
        start, end = int(start), int(end)
        if step is None or R.isna(step):
            step = 1 if end >= start else -1
        step = int(step) if step else 1
        if (end - start) * step < 0:
            step = -step
        return range(start, end + (1 if step > 0 else -1), step)

    def iter(self, coll):
        if coll is None:
            return ()
        if isinstance(coll, R.PMatrix):
            return [R.PArray(r) for r in coll.m]
        if isinstance(coll, R.PMap):
            return list(coll.keys())
        return list(coll)

    def add_method(self, name, ftype, fn):
        self.methods.setdefault(name, []).append((ftype.split("<")[0].replace("[]", "array"), fn))

    def callm(self, obj, name, ctx, args, kw):
        cands = self.methods.get(name)
        if cands:
            tname = obj.__class__.__name__
            prim = PRIM_TYPES.get(tname, ())
            fn = None
            for ftype, f in cands:
                if ftype == tname or ftype in prim or (isinstance(obj, str) and obj.split(".")[0] == ftype.split(".")[-1]) or (ftype in ("array",) and isinstance(obj, R.PArray)) or \
                        (ftype == "map" and isinstance(obj, R.PMap)) or (ftype in ("line",) and isinstance(obj, R.LineObj)) or \
                        (ftype in ("box",) and isinstance(obj, R.BoxObj)) or (ftype in ("label",) and isinstance(obj, R.LabelObj)) or \
                        (ftype.endswith("." + tname)):
                    fn = f
                    break
            if fn is None and len(cands) == 1 and not isinstance(obj, (R.PArray, R.PMap, R.LineObj, R.BoxObj, R.LabelObj, str, float, int)):
                fn = cands[0][1]
            if fn is not None:
                return fn(ctx, obj, *args, **{"v_" + k: v for k, v in kw.items()})
        if obj is None or (isinstance(obj, float) and obj != obj):
            if name.startswith("get_"):
                return R.NA
            if name in ("delete", "set_xy1", "set_xy2", "set_x1", "set_x2", "set_y1", "set_y2", "set_top", "set_bottom",
                        "set_left", "set_right", "set_text", "set_color", "set_bgcolor", "set_border_color") \
                    or name.startswith("set_"):
                return None
            return R.NA
        table = None
        if isinstance(obj, R.PArray):
            table = R.ARRAY
        elif isinstance(obj, R.PMap):
            table = R.MAP
        elif isinstance(obj, R.PMatrix):
            table = R.MATRIX
        elif isinstance(obj, R.LineObj):
            table = R.LINE
        elif isinstance(obj, R.BoxObj):
            table = R.BOX
        elif isinstance(obj, R.LabelObj):
            table = R.LABEL
        elif isinstance(obj, str):
            fn = PB.STR.get(name)
            if fn:
                return fn(obj, *args, **kw)
        elif isinstance(obj, R.UDTBase) and name == "copy":
            return obj.copy()
        if table is not None:
            fn = table.get(name)
            if fn is not None:
                return fn(obj, *args, **kw)
            if name.startswith("set_") or name in ("delete",):
                return None
        if isinstance(obj, R.Drawing) or obj.__class__.__name__ in ("Drawing",):
            return None
        raise R.Unsupported(f"metot {name} ({obj.__class__.__name__})")

    def library(self, path):
        return load_library(self, path)

    def libcall(self, lib, name, ctx, args, kw):
        if name.endswith(".new") or name.endswith(".copy"):
            t = lib.get("T_" + name.rsplit(".", 1)[0])
            if t is None:
                raise R.Unsupported(f"kütüphane tipi {name}")
            return t.new(*args, **kw) if name.endswith(".new") else args[0].copy()
        f = lib.get("f_" + name)
        if f is not None and ("f_" + name + "__1") in lib:     # aşırı yükleme: argüman sayısına uyan
            k, given = 1, len(args) + len(kw) + 1               # +1: ctx
            cands = [f]
            while f"f_{name}__{k}" in lib:
                cands.append(lib[f"f_{name}__{k}"])
                k += 1
            for c in cands:
                co = c.__code__
                if co.co_argcount - len(c.__defaults__ or ()) <= given <= co.co_argcount:
                    f = c
                    break
        if f is None:
            if "." in name:
                raise R.Unsupported(f"kütüphane üyesi {name}")
            v = lib.get("v_" + name)
            if v is not None:
                return v
            raise R.Unsupported(f"kütüphane fonksiyonu {name}")
        return f(ctx, *args, **{"v_" + k: v for k, v in kw.items()})

    def _key(self, symbol, timeframe):
        kind = "chart"
        if isinstance(symbol, str) and symbol.startswith("HA:"):
            kind = "ha"
        elif isinstance(symbol, str) and symbol not in (self.ticker, "") and ":" + self.ticker not in symbol \
                and not symbol.endswith(self.ticker):
            raise R.Unsupported("request.security başka sembol")
        tf = norm_tf(timeframe)
        if tf == "":
            tf = norm_tf(self.chart_tf)
        return (kind, tf)

    def _record(self, site, fn):
        v = fn()
        rec = self.sec_rec.get(site)
        if rec is None:
            rec = self.sec_rec[site] = [R.NA] * self.n
        rec[self.bar] = v
        return v

    def sec(self, site, symbol, timeframe, fn, lookahead):
        key = self._key(symbol, timeframe)
        if key == ("chart", norm_tf(self.chart_tf)):
            return fn()
        if self.pass_key is not None:
            if key == self.pass_key:
                return self._record(site, fn)
            self.flags.add("coklu_gecis")
            return R.NA
        m = self.sec_maps.get(key)
        if m is None:
            raise NeedHTF(key)
        vals = m["vals"].get(site)
        if vals is None:
            return R.NA
        if m["rel"] == "ltf":
            js = m["groups"][self.bar]
            return vals[js[-1]] if js else R.NA
        j = m["idx"][self.bar]
        if m["rel"] == "same":
            return vals[j]
        on = lookahead == "barmerge.lookahead_on" or lookahead is True
        if on:
            self.flags.add("lookahead_on")
        k = j if (on or m["last"][self.bar]) else j - 1
        return vals[k] if 0 <= k < len(vals) else R.NA

    def sec_ltf(self, site, symbol, timeframe, fn, arity=0):
        key = self._key(symbol, timeframe)
        if self.pass_key is not None:
            rows = [self._record(site, fn)] if key == self.pass_key else []
        else:
            m = self.sec_maps.get(key)
            if m is None:
                raise NeedHTF(key)
            vals = m["vals"].get(site)
            rows = [] if vals is None or m["rel"] != "ltf" else [vals[j] for j in m["groups"][self.bar]]
        if arity or (rows and isinstance(rows[0], tuple)):
            # Pine: demet ifadesi → her eleman için ayrı dizi (dizi demeti), demet dizisi değil
            k = arity or len(rows[0])
            return tuple(R.PArray([r[i] if isinstance(r, tuple) and i < len(r) else R.NA for r in rows])
                         for i in range(k))
        return R.PArray(rows)

    def anchor_key(self, ctx, anchor):
        k = self.anchors.get(ctx, 0)
        if R.T(anchor):
            k += 1
            self.anchors[ctx] = k
        return k

    def timepart(self, name, time_=None, timezone=None, *a, **k):
        if time_ is None or R.isna(time_):
            return R.NA
        ts = pd.Timestamp(int(time_), unit="ms", tz="UTC").tz_convert(ZoneInfo(timezone or self.tz))
        return {"hour": ts.hour, "minute": ts.minute, "dayofweek": (ts.dayofweek + 1) % 7 + 1, "dayofmonth": ts.day,
                "month": ts.month, "year": ts.year, "weekofyear": ts.isocalendar()[1], "second": ts.second}[name]

    def tf_seconds(self, tf=None):
        return R.tf_seconds(tf if tf else self.tf)

    def tf_bucket(self, tf):
        sec = R.tf_seconds(tf) or 86400
        return int(self.TM[self.bar] // (sec * 1000))


_DATA = __import__("pathlib").Path(__file__).resolve().parent / "data"
LIB_INDEX_PATH = _DATA / "lib_index_v2.json" if (_DATA / "lib_index_v2.json").exists() else _DATA / "lib_index.json"
_LIB_INDEX: dict | None = None
_LIB_CODE: dict = {}


def lib_index() -> dict:
    """(yazar, kütüphane adı) → kaynak; indirilen kaynaklardan bir kez kurulur."""
    global _LIB_INDEX
    if _LIB_INDEX is None:
        import json
        import re
        if LIB_INDEX_PATH.exists():
            _LIB_INDEX = json.loads(LIB_INDEX_PATH.read_text())
        else:
            import pine_src
            idx = {}
            for r in pine_src.iter_sources(True):
                src = r["source"]
                m = re.search(r'^\s*library\(\s*(?:title\s*=\s*)?["\']([^"\']+)["\']', src, re.M)
                if m and r.get("author"):
                    idx[f"{r['author'].lower()}/{m.group(1).lower()}"] = src
            _LIB_INDEX = idx
    return _LIB_INDEX


def load_library(rt, path: str):
    parts = path.split("/")
    if len(parts) < 2:
        raise R.Unsupported(f"kütüphane yolu {path}")
    key = f"{parts[0].lower()}/{parts[1].lower()}"
    src = lib_index().get(key)
    if src is None:                                    # yayıncı adı değişmiş olabilir: yalnız kütüphane adıyla
        alt = sorted(k for k in lib_index() if k.split("/", 1)[1] == parts[1].lower())
        if alt:
            key, src = alt[0], lib_index()[alt[0]]
    if src is None:
        raise R.Unsupported(f"kütüphane bulunamadı {key}")
    if key not in _LIB_CODE:
        try:
            code = TR.transpile_library(P.parse(src), P.version_of(src))
            ns: dict = {}
            exec(compile(code, f"<lib {key}>", "exec"), ns)
            _LIB_CODE[key] = ns["__lib"]
        except R.Unsupported as e:
            raise R.Unsupported(f"kütüphane {key}: {e}")
        except P.PineSyntaxError as e:
            raise R.Unsupported(f"kütüphane {key} ayrıştırma: {e}")
    return _LIB_CODE[key](rt, PB, R, PB.FUNCS, PB.TA, PB.NEED_RT)


def compile_script(source: str):
    prog = P.parse(source)
    code, overlay = TR.transpile(prog, P.version_of(source))
    ns: dict = {}
    exec(compile(code, "<pine>", "exec"), ns)
    return ns["__run"], overlay, code


def htf_frame(df: pd.DataFrame, htf: str, tz: str):
    """Grafik barlarını borsa saatine göre üst TF'ye topla → (htf_df, idx, last)."""
    loc = pd.to_datetime(df.ts, utc=True).dt.tz_convert(ZoneInfo(tz)).dt.tz_localize(None)
    if htf == "D":
        key = loc.dt.floor("D")
    elif htf == "W":
        key = (loc - pd.to_timedelta(loc.dt.dayofweek, unit="D")).dt.floor("D")
    elif htf == "M":
        key = loc.dt.to_period("M").dt.start_time
    else:
        sec = R.tf_seconds(htf)
        key = loc.dt.floor(f"{sec}s")
    grp = (key != key.shift()).cumsum() - 1
    agg = {"ts": "first", "open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in df.columns:
        agg["volume"] = "sum"
    h = df.groupby(grp.values).agg(agg).reset_index(drop=True)
    idx = grp.values.tolist()
    last = (grp.values != np.r_[grp.values[1:], -1]).tolist()
    return h, idx, last


def run_script(source: str, df: pd.DataFrame, tf: str, sym: str, timeout_s: float = 120.0) -> dict:
    """HTF gerektiren scriptlerde: grafik geçişi NeedHTF ile durur → HTF geçişi → grafik geçişi yeniden."""
    t0 = time.time()
    try:
        fn, overlay, _ = compile_script(source)
    except P.PineSyntaxError as e:
        return {"status": "parse_error", "error": str(e)[:200], "outputs": {}, "overlay": False, "seconds": 0.0, "flags": []}
    except R.Unsupported as e:
        return {"status": "unsupported", "error": str(e)[:200], "outputs": {}, "overlay": False, "seconds": 0.0, "flags": []}
    except Exception as e:
        return {"status": "transpile_error", "error": f"{type(e).__name__}: {e}"[:200], "outputs": {}, "overlay": False,
                "seconds": 0.0, "flags": []}
    maps: dict = {}
    for _ in range(8):
        res = _execute(fn, df, tf, sym, t0 + timeout_s, maps, None)
        if res.get("need_htf") is None:
            res["overlay"] = overlay
            res["seconds"] = round(time.time() - t0, 2)
            return res
        key = res["need_htf"]
        try:
            pdf, mp = pass_frame(df, tf, sym, key)
        except R.Unsupported as e:
            return {"status": "unsupported", "error": str(e), "outputs": {}, "overlay": overlay,
                    "seconds": round(time.time() - t0, 2), "flags": []}
        hres = _execute(fn, pdf, tf, sym, t0 + timeout_s, {}, key)
        if hres["status"] != "ok":
            hres["error"] = f"geçiş {key}: {hres['error']}"
            hres["seconds"] = round(time.time() - t0, 2)
            return hres
        mp["vals"] = hres["sec_rec"]
        maps[key] = mp
    return {"status": "unsupported", "error": "çok fazla geçiş", "outputs": {}, "overlay": overlay, "seconds": 0.0, "flags": []}


_LTF_CACHE: dict = {}


def heikin(df: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c = (df[k].values.astype(float) for k in ("open", "high", "low", "close"))
    hc = (o + h + l + c) / 4
    ho = np.empty(len(o))
    ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(o)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    out = df.copy()
    out["open"], out["close"] = ho, hc
    out["high"], out["low"] = np.maximum(h, np.maximum(ho, hc)), np.minimum(l, np.minimum(ho, hc))
    return out


def _from_1m(gdata, sym: str, p_s: int) -> pd.DataFrame:
    """1m barlarını p_s saniyelik barlara topla (UTC ızgarası; dakika katı alt TF'ler)."""
    try:
        m1 = gdata.load(sym, "1m")
    except KeyError:
        raise R.Unsupported(f"alt TF {p_s // 60}m verisi yok")
    ts = pd.to_datetime(m1.ts, utc=True)
    key = ts.dt.floor(f"{p_s}s")
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in m1.columns:
        agg["volume"] = "sum"
    out = m1.groupby(key.values).agg(agg)
    out.insert(0, "ts", out.index)
    return out.reset_index(drop=True)


def pass_frame(df: pd.DataFrame, tf: str, sym: str, key):
    """Alternatif geçiş verisi + grafik barlarına eşleme."""
    kind, ptf = key
    chart_s, p_s = R.tf_seconds(TF_PINE[tf]), R.tf_seconds(ptf)
    if not p_s:
        raise R.Unsupported(f"bilinmeyen TF {ptf}")
    tz = SYM[sym][1]
    if p_s == chart_s:
        pdf = df
        mp = {"rel": "same", "idx": list(range(len(df)))}
    elif p_s > chart_s:
        pdf, idx, last = htf_frame(df, ptf, tz)
        mp = {"rel": "htf", "idx": idx, "last": last}
    else:
        name = LTF_NAME.get(ptf)
        if name is None and p_s % 60:
            raise R.Unsupported(f"alt TF {ptf} verisi yok")      # saniye TF'leri: tik verisi yok
        name = name or f"{p_s // 60}m"
        ck = (sym, name)
        if ck not in _LTF_CACHE:
            import data as gdata  # GÇM veri katmanı
            try:
                _LTF_CACHE[ck] = gdata.load(sym, name)
            except KeyError:
                _LTF_CACHE[ck] = _from_1m(gdata, sym, p_s)      # 1m barlarından türet
        ldf = _LTF_CACHE[ck]
        t_open = pd.to_datetime(df.ts, utc=True).values
        t_close = t_open + np.timedelta64(chart_s, "s")
        # alt TF barı, KAPANIŞI grafik barının (açılış, kapanış] aralığına düşen grafik barına aittir (EK-P6).
        # Açılışa göre gruplamak, grafik TF'ini tam bölmeyen alt TF'lerde (45m/1h) kapanıştan sonrasını gösteriyordu.
        lc = pd.to_datetime(ldf.ts, utc=True).values + np.timedelta64(p_s, "s")
        a, b_ = np.searchsorted(lc, t_open[0], "right"), np.searchsorted(lc, t_close[-1], "right")
        pdf = ldf.iloc[a:b_].reset_index(drop=True)
        lc = lc[a:b_]
        lo, hi = np.searchsorted(lc, t_open, "right"), np.searchsorted(lc, t_close, "right")
        mp = {"rel": "ltf", "groups": [list(range(x, y)) for x, y in zip(lo, hi)]}
        if len(pdf) == 0:
            raise R.Unsupported("alt TF verisi bu dönemde yok")
    if kind == "ha":
        pdf = heikin(pdf)
    return pdf, mp


def _execute(fn, df, tf, sym, deadline, maps, pass_key) -> dict:
    res = {"status": "ok", "error": None, "outputs": {}, "flags": [], "need_htf": None, "sec_rec": {}}
    rt = RT(df, tf, sym, deadline)
    rt.sec_maps, rt.pass_key = maps, pass_key
    if pass_key is not None:
        rt.tf = pass_key[1]
        rt.tf_mult = int(rt.tf) if rt.tf.isdigit() else 1
        rt.intraday, rt.isdaily = rt.tf.isdigit(), rt.tf == "D"
    try:
        fn(rt, PB, R, PB.FUNCS, PB.TA, PB.NEED_RT)
    except NeedHTF as e:
        res["need_htf"] = e.tf
        return res
    except Timeout:
        res.update(status="timeout", error=f"bar {rt.bar}")
    except R.Unsupported as e:
        res.update(status="unsupported", error=str(e)[:200])
    except Exception as e:
        res.update(status="runtime_error", error=f"{type(e).__name__}: {e} @bar {rt.bar}"[:200])
    res["outputs"] = rt.outputs
    res["sec_rec"] = rt.sec_rec
    res["flags"] = sorted(rt.flags)
    return res


def _run_script_single(source: str, df: pd.DataFrame, tf: str, sym: str, timeout_s: float = 120.0) -> dict:
    t0 = time.time()
    res = {"status": "ok", "error": None, "outputs": {}, "overlay": False, "seconds": 0.0}
    try:
        fn, overlay, _ = compile_script(source)
        res["overlay"] = overlay
    except P.PineSyntaxError as e:
        res.update(status="parse_error", error=str(e)[:200])
        return res
    except R.Unsupported as e:
        res.update(status="unsupported", error=str(e)[:200])
        return res
    except Exception as e:  # çevirmen/derleme hatası
        res.update(status="transpile_error", error=f"{type(e).__name__}: {e}"[:200])
        return res
    rt = RT(df, tf, sym, t0 + timeout_s)
    try:
        fn(rt, PB, R, PB.FUNCS, PB.TA, PB.NEED_RT)
    except Timeout:
        res.update(status="timeout", error=f"bar {rt.bar}")
    except R.Unsupported as e:
        res.update(status="unsupported", error=str(e)[:200])
    except Exception as e:
        res.update(status="runtime_error", error=f"{type(e).__name__}: {e} @bar {rt.bar}"[:200])
    res["outputs"] = rt.outputs
    res["seconds"] = round(time.time() - t0, 2)
    return res
