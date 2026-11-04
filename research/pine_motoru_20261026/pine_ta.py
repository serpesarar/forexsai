"""Pine `ta.*` fonksiyonlarının artımlı (bar bar) karşılıkları.

Her çağrı yeri × örnek (ctx) için bir durum nesnesi tutulur; `u(...)` o barın değerini döndürür. na = float('nan').
TradingView'ın belgelenen tanımlarına uyulur (RMA = Wilder, EMA = 2/(n+1), stdev = popülasyon).
"""
from __future__ import annotations

import math
from collections import deque

NA = float("nan")


def isna(x) -> bool:
    if type(x) is float:                         # sıcak yol: düz float
        return x != x
    return x is None or (isinstance(x, float) and x != x)


def _len(n, default=1):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return default
    return max(n, 1)


class Window:
    """Son n değerin penceresi (n bar bar değişebilir)."""
    __slots__ = ("q",)

    def __init__(self):
        self.q = deque()

    def push(self, x, n):
        self.q.append(x)
        while len(self.q) > n:
            self.q.popleft()
        return len(self.q) >= n


class SMA:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        full = self.w.push(x, n)
        if not full:
            return NA
        s = 0.0
        for v in self.w.q:
            if isna(v):
                return NA
            s += v
        return s / n


class EMA:
    __slots__ = ("v", "seed")

    def __init__(self):
        self.v, self.seed = NA, []

    def u(self, x, n, alpha=None):
        n = _len(n)
        a = alpha if alpha is not None else 2.0 / (n + 1)
        if isna(x):
            return self.v
        if isna(self.v):
            self.seed.append(x)
            if len(self.seed) >= n:
                self.v = sum(self.seed[-n:]) / n
                self.seed = []
            return self.v
        self.v = a * x + (1 - a) * self.v
        return self.v


class RMA(EMA):
    def u(self, x, n, alpha=None):
        n = _len(n)
        return EMA.u(self, x, n, 1.0 / n)


class WMA:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        num = den = 0.0
        for i, v in enumerate(self.w.q, 1):
            if isna(v):
                return NA
            num += v * i
            den += i
        return num / den


class SWMA:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x):
        if not self.w.push(x, 4):
            return NA
        a, b, c, d = self.w.q
        return a / 6 + b * 2 / 6 + c * 2 / 6 + d / 6


class VWMA:
    __slots__ = ("a", "b")

    def __init__(self):
        self.a, self.b = SMA(), SMA()

    def u(self, x, n, vol):
        return _div(self.a.u(x * vol, n), self.b.u(vol, n))


class HMA:
    __slots__ = ("w1", "w2", "w3")

    def __init__(self):
        self.w1, self.w2, self.w3 = WMA(), WMA(), WMA()

    def u(self, x, n):
        n = _len(n)
        a = self.w1.u(x, max(n // 2, 1))
        b = self.w2.u(x, n)
        return self.w3.u(2 * a - b, max(int(math.floor(math.sqrt(n))), 1))


class ALMA:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n, offset=0.85, sigma=6.0, floor=False):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        m = math.floor(offset * (n - 1)) if floor else offset * (n - 1)
        s = n / sigma
        num = den = 0.0
        for i, v in enumerate(self.w.q):
            w = math.exp(-((i - m) ** 2) / (2 * s * s))
            num += v * w
            den += w
        return num / den


def _div(a, b):
    try:
        if isna(a) or isna(b) or b == 0:
            return NA
        return a / b
    except TypeError:
        return NA


class Highest:
    __slots__ = ("w", "mode")

    def __init__(self, mode="max"):
        self.w, self.mode = Window(), mode

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        vals = [v for v in self.w.q if not isna(v)]
        if not vals:
            return NA
        return max(vals) if self.mode == "max" else min(vals)


class Lowest(Highest):
    def __init__(self):
        Highest.__init__(self, "min")


class HighestBars:
    __slots__ = ("w", "mode")

    def __init__(self, mode="max"):
        self.w, self.mode = Window(), mode

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        q = list(self.w.q)
        best, bi = None, 0
        for i, v in enumerate(q):
            if isna(v):
                continue
            if best is None or (v >= best if self.mode == "max" else v <= best):
                best, bi = v, i
        return -(len(q) - 1 - bi)


class LowestBars(HighestBars):
    def __init__(self):
        HighestBars.__init__(self, "min")


class Stdev:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n, biased=True):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        vals = list(self.w.q)
        if any(isna(v) for v in vals):
            return NA
        m = sum(vals) / n
        var = sum((v - m) ** 2 for v in vals) / (n if biased or n < 2 else n - 1)
        return math.sqrt(var)


class Variance(Stdev):
    def u(self, x, n, biased=True):
        s = Stdev.u(self, x, n, biased)
        return s * s if not isna(s) else NA


class Dev:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        vals = list(self.w.q)
        if any(isna(v) for v in vals):
            return NA
        m = sum(vals) / n
        return sum(abs(v - m) for v in vals) / n


class Hist:
    """Bir değerin önceki bar değeri (change, mom, cross için)."""
    __slots__ = ("q",)

    def __init__(self):
        self.q = deque(maxlen=512)

    def u(self, x, k=1):
        k = _len(k)
        prev = self.q[-k] if len(self.q) >= k else NA
        self.q.append(x)
        return prev


class Change:
    __slots__ = ("h",)

    def __init__(self):
        self.h = Hist()

    def u(self, x, k=1):
        prev = self.h.u(x, k)
        if isinstance(x, bool) or isinstance(prev, bool):
            return x != prev
        return NA if isna(prev) or isna(x) else x - prev


class ROC(Change):
    def u(self, x, k=1):
        prev = self.h.u(x, k)
        return NA if isna(prev) or isna(x) or prev == 0 else 100 * (x - prev) / prev


class Cross:
    __slots__ = ("pa", "pb", "mode")

    def __init__(self, mode="over"):
        self.pa, self.pb, self.mode = NA, NA, mode

    def u(self, a, b):
        pa, pb = self.pa, self.pb
        self.pa, self.pb = a, b
        if isna(pa) or isna(pb) or isna(a) or isna(b):
            return False
        try:
            up = a > b and pa <= pb
            dn = a < b and pa >= pb
        except TypeError:
            return False
        return up if self.mode == "over" else (dn if self.mode == "under" else up or dn)


class Crossunder(Cross):
    def __init__(self):
        Cross.__init__(self, "under")


class CrossAny(Cross):
    def __init__(self):
        Cross.__init__(self, "any")


class RSI:
    __slots__ = ("h", "up", "dn")

    def __init__(self):
        self.h, self.up, self.dn = Hist(), RMA(), RMA()

    def u(self, x, n):
        prev = self.h.u(x)
        if isna(prev) or isna(x):
            return NA
        d = x - prev
        u = self.up.u(max(d, 0.0), n)
        dd = self.dn.u(max(-d, 0.0), n)
        if isna(u) or isna(dd):
            return NA
        if dd == 0:
            return 100.0
        if u == 0:
            return 0.0
        return 100 - 100 / (1 + u / dd)


class TR:
    __slots__ = ("pc",)

    def __init__(self):
        self.pc = NA

    def u(self, h, l, c, handle_na=False):
        pc, self.pc = self.pc, c
        if isna(pc):
            return h - l if handle_na else NA
        return max(h - l, abs(h - pc), abs(l - pc))


class ATR:
    __slots__ = ("tr", "rma")

    def __init__(self):
        self.tr, self.rma = TR(), RMA()

    def u(self, n, h, l, c):
        return self.rma.u(self.tr.u(h, l, c, True), n)


class Stoch:
    __slots__ = ("hh", "ll")

    def __init__(self):
        self.hh, self.ll = Highest(), Lowest()

    def u(self, src, hi, lo, n):
        h = self.hh.u(hi, n)
        l = self.ll.u(lo, n)
        return NA if isna(h) or isna(l) else 100 * _div(src - l, h - l)


class MACD:
    __slots__ = ("f", "s", "g")

    def __init__(self):
        self.f, self.s, self.g = EMA(), EMA(), EMA()

    def u(self, x, fast, slow, sig):
        m = self.f.u(x, fast) - self.s.u(x, slow)
        sg = self.g.u(m, sig)
        return (m, sg, m - sg)


class BB:
    __slots__ = ("m", "s")

    def __init__(self):
        self.m, self.s = SMA(), Stdev()

    def u(self, x, n, mult):
        m = self.m.u(x, n)
        s = self.s.u(x, n)
        return (m, m + mult * s, m - mult * s)


class BBW(BB):
    def u(self, x, n, mult):
        m, up, lo = BB.u(self, x, n, mult)
        return _div(up - lo, m) * 100 if not isna(m) else NA


class KC:
    __slots__ = ("e", "r", "tr")

    def __init__(self):
        self.e, self.r, self.tr = EMA(), EMA(), TR()

    def u(self, x, n, mult, h, l, c, use_tr=True):
        m = self.e.u(x, n)
        rng = self.tr.u(h, l, c, True) if use_tr else h - l
        r = self.r.u(rng, n)
        return (m, m + mult * r, m - mult * r)


class KCW(KC):
    def u(self, x, n, mult, h, l, c, use_tr=True):
        m, up, lo = KC.u(self, x, n, mult, h, l, c, use_tr)
        return _div(up - lo, m)


class CCI:
    __slots__ = ("m", "d")

    def __init__(self):
        self.m, self.d = SMA(), Dev()

    def u(self, x, n):
        return _div(x - self.m.u(x, n), 0.015 * self.d.u(x, n))


class MFI:
    __slots__ = ("h", "up", "dn")

    def __init__(self):
        self.h, self.up, self.dn = Hist(), Window(), Window()

    def u(self, x, n, vol):
        prev = self.h.u(x)
        d = 0 if isna(prev) else x - prev
        self.up.push(vol * x if d > 0 else 0.0, _len(n))
        full = self.dn.push(vol * x if d < 0 else 0.0, _len(n))
        if not full:
            return NA
        u, dd = sum(self.up.q), sum(self.dn.q)
        return 100.0 if dd == 0 else 100 - 100 / (1 + u / dd)


class DMI:
    __slots__ = ("ph", "pl", "tr", "rp", "rm", "rt", "adx")

    def __init__(self):
        self.ph, self.pl, self.tr = NA, NA, TR()
        self.rp, self.rm, self.rt, self.adx = RMA(), RMA(), RMA(), RMA()

    def u(self, dilen, adxlen, h, l, c):
        up = NA if isna(self.ph) else h - self.ph
        dn = NA if isna(self.pl) else self.pl - l
        self.ph, self.pl = h, l
        tr = self.tr.u(h, l, c, True)
        if isna(up):
            return (NA, NA, NA)
        pdm = up if up > dn and up > 0 else 0.0
        mdm = dn if dn > up and dn > 0 else 0.0
        t = self.rt.u(tr, dilen)
        p = 100 * _div(self.rp.u(pdm, dilen), t)
        m = 100 * _div(self.rm.u(mdm, dilen), t)
        s = p + m
        adx = self.adx.u(100 * abs(p - m) / (s if s != 0 else 1), adxlen) if not isna(s) else NA
        return (p, m, adx)


class SAR:
    __slots__ = ("bull", "af", "ep", "sar", "ph", "pl", "ph2", "pl2", "n")

    def __init__(self):
        self.bull, self.af, self.ep, self.sar = True, 0.02, NA, NA
        self.ph = self.pl = self.ph2 = self.pl2 = NA
        self.n = 0

    def u(self, start, inc, mx, h, l):
        self.n += 1
        if self.n == 1:
            self.sar, self.ep, self.af = l, h, start
            self.ph, self.pl = h, l
            return NA
        sar = self.sar + self.af * (self.ep - self.sar)
        if self.bull:
            sar = min(sar, self.pl, self.pl2 if not isna(self.pl2) else self.pl)
            if l < sar:
                self.bull, sar, self.ep, self.af = False, self.ep, l, start
            elif h > self.ep:
                self.ep, self.af = h, min(self.af + inc, mx)
        else:
            sar = max(sar, self.ph, self.ph2 if not isna(self.ph2) else self.ph)
            if h > sar:
                self.bull, sar, self.ep, self.af = True, self.ep, h, start
            elif l < self.ep:
                self.ep, self.af = l, min(self.af + inc, mx)
        self.sar = sar
        self.ph2, self.pl2, self.ph, self.pl = self.ph, self.pl, h, l
        return sar


class Supertrend:
    __slots__ = ("atr", "up", "dn", "dir", "pc")

    def __init__(self):
        self.atr, self.up, self.dn, self.dir, self.pc = ATR(), NA, NA, 1, NA

    def u(self, factor, n, h, l, c):
        a = self.atr.u(n, h, l, c)
        if isna(a):
            self.pc = c
            return (NA, NA)
        src = (h + l) / 2
        up, dn = src - factor * a, src + factor * a
        pu, pd = self.up, self.dn
        if not isna(pu) and not isna(self.pc):
            up = max(up, pu) if self.pc > pu else up
            dn = min(dn, pd) if self.pc < pd else dn
        if isna(pu):
            d = 1
        elif self.dir == -1 and c > pd:
            d = 1
        elif self.dir == 1 and c < pu:
            d = -1
        else:
            d = self.dir
        self.up, self.dn, self.dir, self.pc = up, dn, d, c
        # Pine ta.supertrend yönü: -1 yükseliş (çizgi altta), +1 düşüş
        return (up if d == 1 else dn, -d)


class Linreg:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n, offset=0):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        ys = list(self.w.q)
        if any(isna(v) for v in ys):
            return NA
        sx = n * (n - 1) / 2
        sxx = (n - 1) * n * (2 * n - 1) / 6
        sy = sum(ys)
        sxy = sum(i * v for i, v in enumerate(ys))
        den = n * sxx - sx * sx
        b = (n * sxy - sx * sy) / den if den else 0.0
        a = (sy - b * sx) / n
        return a + b * (n - 1 - offset)


class Correlation:
    __slots__ = ("a", "b")

    def __init__(self):
        self.a, self.b = Window(), Window()

    def u(self, x, y, n):
        n = _len(n)
        self.a.push(x, n)
        if not self.b.push(y, n):
            return NA
        xs, ys = list(self.a.q), list(self.b.q)
        if any(isna(v) for v in xs + ys):
            return NA
        mx, my = sum(xs) / n, sum(ys) / n
        cov = sum((p - mx) * (q - my) for p, q in zip(xs, ys))
        vx = sum((p - mx) ** 2 for p in xs)
        vy = sum((q - my) ** 2 for q in ys)
        return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else NA


class Percentrank:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n + 1):
            return NA
        q = list(self.w.q)
        cur = q[-1]
        return 100 * sum(1 for v in q[:-1] if not isna(v) and v <= cur) / n


class Percentile:
    __slots__ = ("w", "mode")

    def __init__(self, mode="lin"):
        self.w, self.mode = Window(), mode

    def u(self, x, n, p):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        vals = sorted(v for v in self.w.q if not isna(v))
        if not vals:
            return NA
        if self.mode == "near":
            k = max(int(math.ceil(p / 100 * len(vals))) - 1, 0)
            return vals[min(k, len(vals) - 1)]
        pos = (len(vals) - 1) * p / 100
        lo = int(math.floor(pos))
        hi = min(lo + 1, len(vals) - 1)
        return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


class PercentileNear(Percentile):
    def __init__(self):
        Percentile.__init__(self, "near")


class Median(Percentile):
    def u(self, x, n):
        return Percentile.u(self, x, n, 50)


class Mode:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        if not self.w.push(x, _len(n)):
            return NA
        vals = [v for v in self.w.q if not isna(v)]
        if not vals:
            return NA
        cnt = {}
        for v in vals:
            cnt[v] = cnt.get(v, 0) + 1
        best = max(cnt.values())
        return min(v for v, k in cnt.items() if k == best)


class Range:
    __slots__ = ("h", "l")

    def __init__(self):
        self.h, self.l = Highest(), Lowest()

    def u(self, x, n):
        return self.h.u(x, n) - self.l.u(x, n)


class Cum:
    __slots__ = ("s",)

    def __init__(self):
        self.s = 0.0

    def u(self, x):
        if not isna(x):
            self.s += x
        return self.s


class Rising:
    __slots__ = ("w", "mode")

    def __init__(self, mode="up"):
        self.w, self.mode = Window(), mode

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n + 1):
            return False
        q = list(self.w.q)
        cur = q[-1]
        if isna(cur):
            return False
        prev = [v for v in q[:-1] if not isna(v)]
        return all(cur > v for v in prev) if self.mode == "up" else all(cur < v for v in prev)


class Falling(Rising):
    def __init__(self):
        Rising.__init__(self, "down")


class Pivot:
    """ta.pivothigh/pivotlow(left, right): sağ kanat kapanınca onaylı; değer pivot barının değeri."""
    __slots__ = ("w", "mode")

    def __init__(self, mode="high"):
        self.w, self.mode = deque(), mode

    def u(self, x, left, right):
        left, right = _len(left, 1), _len(right, 1)
        n = left + right + 1
        self.w.append(x)
        while len(self.w) > n:
            self.w.popleft()
        if len(self.w) < n:
            return NA
        q = list(self.w)
        c = q[left]
        if isna(c):
            return NA
        others = q[:left] + q[left + 1:]
        if self.mode == "high":
            ok = all(isna(v) or c > v for v in q[:left]) and all(isna(v) or c >= v for v in q[left + 1:])
        else:
            ok = all(isna(v) or c < v for v in q[:left]) and all(isna(v) or c <= v for v in q[left + 1:])
        return c if ok and others else NA


class PivotLow(Pivot):
    def __init__(self):
        Pivot.__init__(self, "low")


class BarsSince:
    __slots__ = ("n",)

    def __init__(self):
        self.n = None

    def u(self, cond):
        if cond is True or (not isna(cond) and cond and cond is not False):
            self.n = 0
        elif self.n is not None:
            self.n += 1
        return NA if self.n is None else self.n


class ValueWhen:
    __slots__ = ("vals",)

    def __init__(self):
        self.vals = deque(maxlen=64)

    def u(self, cond, src, occ=0):
        if cond is True or (not isna(cond) and cond and cond is not False):
            self.vals.append(src)
        occ = int(occ) if not isna(occ) else 0
        return self.vals[-1 - occ] if len(self.vals) > occ else NA


class OBV:
    __slots__ = ("pc", "s")

    def __init__(self):
        self.pc, self.s = NA, 0.0

    def u(self, c, v):
        if not isna(self.pc) and not isna(v):
            self.s += v if c > self.pc else (-v if c < self.pc else 0)
        self.pc = c
        return self.s


class AccDist:
    __slots__ = ("s",)

    def __init__(self):
        self.s = 0.0

    def u(self, h, l, c, v):
        mf = _div((c - l) - (h - c), h - l)
        if not isna(mf) and not isna(v):
            self.s += mf * v
        return self.s


class PVT:
    __slots__ = ("pc", "s")

    def __init__(self):
        self.pc, self.s = NA, 0.0

    def u(self, c, v):
        if not isna(self.pc) and self.pc != 0 and not isna(v):
            self.s += (c - self.pc) / self.pc * v
        self.pc = c
        return self.s


class TSI:
    __slots__ = ("h", "a1", "a2", "b1", "b2")

    def __init__(self):
        self.h, self.a1, self.a2, self.b1, self.b2 = Hist(), EMA(), EMA(), EMA(), EMA()

    def u(self, x, s, l):
        prev = self.h.u(x)
        d = 0.0 if isna(prev) else x - prev
        return _div(self.a2.u(self.a1.u(d, l), s), self.b2.u(self.b1.u(abs(d), l), s))


class CMO:
    __slots__ = ("h", "u_", "d_")

    def __init__(self):
        self.h, self.u_, self.d_ = Hist(), Window(), Window()

    def u(self, x, n):
        prev = self.h.u(x)
        d = 0.0 if isna(prev) else x - prev
        self.u_.push(max(d, 0), _len(n))
        if not self.d_.push(max(-d, 0), _len(n)):
            return NA
        a, b = sum(self.u_.q), sum(self.d_.q)
        return 100 * _div(a - b, a + b)


class WPR:
    __slots__ = ("hh", "ll")

    def __init__(self):
        self.hh, self.ll = Highest(), Lowest()

    def u(self, n, h, l, c):
        hh, ll = self.hh.u(h, n), self.ll.u(l, n)
        return 100 * _div(c - hh, hh - ll)


class COG:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        q = list(self.w.q)[::-1]
        s = sum(q)
        return -sum(v * (i + 1) for i, v in enumerate(q)) / s if s else NA


class VWAP:
    __slots__ = ("pv", "v", "pv2", "anchor")

    def __init__(self):
        self.pv = self.v = self.pv2 = 0.0
        self.anchor = None

    def u(self, src, anchor_key, vol, stdev_mult=None):
        if anchor_key != self.anchor:
            self.anchor, self.pv, self.v, self.pv2 = anchor_key, 0.0, 0.0, 0.0
        vol = 1.0 if isna(vol) else vol
        self.pv += src * vol
        self.v += vol
        self.pv2 += src * src * vol
        m = _div(self.pv, self.v)
        if stdev_mult is None:
            return m
        sd = math.sqrt(max(_div(self.pv2, self.v) - m * m, 0)) if not isna(m) else NA
        return (m, m + stdev_mult * sd, m - stdev_mult * sd)


class RCI:
    __slots__ = ("w",)

    def __init__(self):
        self.w = Window()

    def u(self, x, n):
        n = _len(n)
        if not self.w.push(x, n):
            return NA
        q = list(self.w.q)
        order = sorted(range(n), key=lambda i: -q[i])
        rank = {i: r + 1 for r, i in enumerate(order)}
        d2 = sum(((n - i) - rank[i]) ** 2 for i in range(n))
        return (1 - 6 * d2 / (n * (n * n - 1))) * 100


class Fixnan:
    __slots__ = ("last",)

    def __init__(self):
        self.last = NA

    def u(self, x):
        if not isna(x):
            self.last = x
        return self.last


TA_CLASSES = {
    "sma": SMA, "ema": EMA, "rma": RMA, "wma": WMA, "swma": SWMA, "vwma": VWMA, "hma": HMA, "alma": ALMA,
    "highest": Highest, "lowest": Lowest, "highestbars": HighestBars, "lowestbars": LowestBars,
    "stdev": Stdev, "variance": Variance, "dev": Dev, "change": Change, "mom": Change, "roc": ROC,
    "crossover": Cross, "crossunder": Crossunder, "cross": CrossAny, "rsi": RSI, "tr": TR, "atr": ATR,
    "stoch": Stoch, "macd": MACD, "bb": BB, "bbw": BBW, "kc": KC, "kcw": KCW, "cci": CCI, "mfi": MFI,
    "dmi": DMI, "sar": SAR, "supertrend": Supertrend, "linreg": Linreg, "correlation": Correlation,
    "percentrank": Percentrank, "percentile_linear_interpolation": Percentile,
    "percentile_nearest_rank": PercentileNear, "median": Median, "mode": Mode, "range": Range, "cum": Cum,
    "rising": Rising, "falling": Falling, "pivothigh": Pivot, "pivotlow": PivotLow, "barssince": BarsSince,
    "valuewhen": ValueWhen, "obv": OBV, "accdist": AccDist, "pvt": PVT, "tsi": TSI, "cmo": CMO, "wpr": WPR,
    "cog": COG, "vwap": VWAP, "rci": RCI, "fixnan": Fixnan,
}
