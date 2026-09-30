"""USOIL BUY laboratuvarı — çıkış taktiği (TP çarpanı, koştur, zikzak kilidi) × rejim.

Veri:
  L  : 17 ay SpotCrude M5 (kutudan, broker saati) → sentetik BUY girişleri (her 30 dk)
  A  : botun USOIL BUY işlemleri (1m, BREAKOUT hariç = canlı aile)
  B  : pulse USOIL BUY sinyalleri 2026-06-20→09-02 (1m, 15 dk tekilleştirme, çakışmaya izin)
Geometri: config USOIL BUY — TP %1.04, SL %1.49 (R = SL mesafesi).
Rejim (giriş anından ÖNCEKİ veriyle): d1 = son 24 saatlik getiri / 24s ATR-benzeri oynaklık;
  trend = fiyatın 3 günlük EMA'sına göre konumu + EMA eğimi.
Motor muhafazakâr: aynı barda stop+TP → stop; stop taşıma 1 bar sonra; açılış stop altındaysa
dolum açılıştan.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from numba import njit

TP_PCT, SL_PCT, SPREAD = 1.04, 1.49, 0.025


@njit(cache=True)
def run2(FAV, ADV, OPN, CLS, off, ln, tpR, P, L, first, lockR, delay, act, trail, maxbars):
    """act: 0=zikzak kilidi yok; 1=kilit (SL→lockR); 2=kapat.
    trail>0 → TP'ye değince kapatma, stop = tepe − trail (koştur).
    first: 0 klasik (ilk kâr ziyareti), −1 önce zarar sonra kâr."""
    N = off.shape[0]
    out = np.empty(N)
    vals = np.empty(4)
    for k in range(N):
        o = off[k]; n = min(ln[k], maxbars); tp = tpR[k]
        stop = -1.0; last = 0; fz = 0; armed = False; at = -1; res = np.nan
        run = False; peak = -1e9
        for j in range(n):
            f = FAV[o + j]; a = ADV[o + j]; op = OPN[o + j]; c = CLS[o + j]
            if armed and act == 1 and j >= at and lockR[k] > stop:
                stop = lockR[k]
            if op <= stop:
                res = op; break
            if a <= stop:
                res = stop; break
            if armed and act == 2 and j >= at:
                res = c; break
            if f >= tp:
                if trail <= 0:
                    res = tp; break
                if not run:
                    run = True
                    peak = f
                    if tp - trail > stop:
                        stop = tp - trail
                    if a <= stop:            # aynı barda geri dönüş → muhafazakâr
                        res = stop; break
                    continue
            if run:
                if f > peak:
                    peak = f
                if peak - trail > stop:
                    stop = peak - trail
                continue
            if act > 0 and not armed:
                vals[0] = op
                if c >= op:
                    vals[1] = a; vals[2] = f
                else:
                    vals[1] = f; vals[2] = a
                vals[3] = c
                for q in range(4):
                    v = vals[q]
                    z = 1 if v >= P[k] else (-1 if v <= -L else 0)
                    if z != 0 and z != last:
                        if fz == 0:
                            fz = z
                        last = z
                        if z == 1 and (first == 0 or fz == first):
                            armed = True; at = j + delay
                            if act == 2 and delay <= 0:
                                res = c
                            break
                if armed and act == 2 and delay <= 0:
                    break
        if np.isnan(res):
            res = CLS[o + n - 1] if not run else max(stop, CLS[o + n - 1])
        out[k] = res
    return out


class Set:
    def __init__(self, paths, meta, bar_min):
        self.meta = meta.reset_index(drop=True); self.bar_min = bar_min
        ln = np.array([len(p["fav"]) for p in paths], np.int64)
        off = np.zeros(len(paths), np.int64); off[1:] = np.cumsum(ln)[:-1]
        cat = lambda key: np.concatenate([np.asarray(p[key], float) for p in paths])
        self.FAV, self.ADV, self.OPN, self.CLS = cat("fav"), cat("adv"), cat("opn"), cat("cls")
        self.off, self.ln = off, ln
        self.rr = np.full(len(paths), TP_PCT / SL_PCT)
        self.base = self.run()

    def run(self, tp_mult=1.0, P=0.6, L=0.3, first=-1, lock=0.5, act=0, trail=0.0,
            delay_min=2, max_hours=48):
        tpR = self.rr * tp_mult
        Pr = P * self.rr                       # tetik: ORİJİNAL TP yolunun kesri
        lockR = lock * self.rr
        d = max(1, int(np.ceil(delay_min / self.bar_min)))
        return run2(self.FAV, self.ADV, self.OPN, self.CLS, self.off, self.ln, tpR, Pr, L, first,
                    lockR, d, act, trail, int(max_hours * 60 / self.bar_min))


def _path(O, H, L, C, i, n, e, risk):
    s = slice(i, min(i + n, len(C)))
    return dict(fav=(H[s] - e) / risk, adv=(L[s] - e) / risk, opn=(O[s] - e) / risk, cls=(C[s] - e) / risk)


def regime(closes: np.ndarray, i: int, bars_per_day: int) -> tuple[float, float, float]:
    """(24s getiri %, 3g EMA'ya uzaklık %, 3g EMA'nın 1 günlük eğimi %) — i'den ÖNCEKİ barlarla."""
    lo = max(0, i - 4 * bars_per_day)
    x = closes[lo:i]
    if len(x) < 3 * bars_per_day:
        return np.nan, np.nan, np.nan
    alpha = 2 / (3 * bars_per_day + 1)
    ema = np.empty(len(x)); ema[0] = x[0]
    for t in range(1, len(x)):
        ema[t] = ema[t - 1] + alpha * (x[t] - ema[t - 1])
    r24 = (x[-1] / x[-bars_per_day] - 1) * 100
    dist = (x[-1] / ema[-1] - 1) * 100
    slope = (ema[-1] / ema[-bars_per_day] - 1) * 100
    return r24, dist, slope


def build_L(step_min=30, horizon_h=48):
    z = np.load("spotcrude_m5.npz")
    t = pd.to_datetime(z["t"], unit="s")          # broker saati (UTC+2/+3) — göreli kullanım
    O, H, Lo, C = z["o"], z["h"], z["l"], z["c"]
    step = step_min // 5; hz = horizon_h * 12
    ema = causal_ema(C, 3 * 288)
    paths, rows = [], []
    for i in range(4 * 288, len(C) - hz, step):
        if (t[i + 12] - t[i]) > pd.Timedelta(minutes=90):
            continue                                 # kapanış/boşluk
        e = O[i] + SPREAD; risk = e * SL_PCT / 100
        paths.append(_path(O, H, Lo, C, i, hz, e, risk))
        r24, dist, slope = regime_at(C, ema, i, 288)
        rows.append(dict(t=t[i], r24=r24, dist=dist, slope=slope))
    return Set(paths, pd.DataFrame(rows), 5)


def causal_ema(x: np.ndarray, span: int) -> np.ndarray:
    a = 2 / (span + 1); e = np.empty(len(x)); e[0] = x[0]
    for t in range(1, len(x)):
        e[t] = e[t - 1] + a * (x[t] - e[t - 1])
    return e


def regime_at(C, ema, i, bpd):
    """Giriş barı i'den ÖNCE kapanmış son bar (i−1) ile rejim."""
    j = i - 1
    return ((C[j] / C[j - bpd] - 1) * 100, (C[j] / ema[j] - 1) * 100, (ema[j] / ema[j - bpd] - 1) * 100)
