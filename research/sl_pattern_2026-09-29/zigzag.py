"""Zikzak-koşullu başabaş/kilit motoru (numba) + üç veri seti (A bot, B pulse replay, C sentetik).

Birim: R = girişteki SL mesafesi. rr = TP mesafesi / SL mesafesi.
Bölge: KÂR  → fiyat ≥ P  (P = TP yolunun kesri × rr)
       ZARAR→ fiyat ≤ −L (L R cinsinden)
Olay dizisi: bölge değiştikçe kaydedilir (K, Z, K, Z ...). Bar içi sıra: yeşil mum
O→dip→tepe→C, kırmızı mum O→tepe→dip→C.
Kural: n_p'inci (veya sonraki) KÂR ziyaretinde, ilk olay `first` ise (0=fark etmez,
+1=önce kâr, −1=önce zarar) ve yaş ≥ age bar ise TETİKLE:
  action 0 → SL'i lock'a çek (delay bar sonra geçerli)
  action 1 → işlemi o barın kapanışında kapat
Muhafazakâr: aynı barda stop + TP → stop.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from numba import njit

SPREAD = {"USOIL.FOREX": 0.03, "NDX.INDX": 1.5, "GDAXI.INDX": 1.5}
GEOM = {"NDX.INDX": (80.0, 110.0, False), "GDAXI.INDX": (67.0, 119.0, False),
        "USOIL.FOREX": (1.04, 1.49, True)}


@njit(cache=True)
def run_rule(FAV, ADV, OPN, CLS, off, ln, rr, PpR, PaR, LR, first, n_p, lockR, age,
             delay, action):
    N = off.shape[0]
    out = np.empty(N)
    armed_out = np.zeros(N, np.int8)
    vals = np.empty(4)
    for k in range(N):
        o = off[k]; n = ln[k]; tp = rr[k]
        stop = -1.0; last = 0; firstz = 0; pv = 0
        armed = False; act = -1; res = np.nan
        for j in range(n):
            f = FAV[o + j]; a = ADV[o + j]
            if armed and j >= act and lockR[k] > stop:
                stop = lockR[k]
            # Bar stop'un ALTINDA açıldıysa (boşluk / SL taşınırken fiyat zaten
            # kilidin altına inmiş) dolum stop'tan değil AÇILIŞTAN olur — broker
            # fiyatın üstüne SL kabul etmez, bot piyasadan kapatır.
            if OPN[o + j] <= stop:
                res = OPN[o + j]; break
            if a <= stop:
                res = stop; break
            if f >= tp:
                res = tp; break
            # "kapat" eylemi: bot tetikten (delay−1) bar sonra piyasadan kapatır
            if armed and action == 1 and j >= act:
                res = CLS[o + j]; break
            if not armed and n_p < 99:
                op = OPN[o + j]; c = CLS[o + j]
                vals[0] = op
                if c >= op:
                    vals[1] = a; vals[2] = f
                else:
                    vals[1] = f; vals[2] = a
                vals[3] = c
                closed = False
                for q in range(4):
                    v = vals[q]
                    thr = PaR[k] if pv >= n_p - 1 else PpR[k]
                    z = 0
                    if v >= thr:
                        z = 1
                    elif v <= -LR[k]:
                        z = -1
                    if z != 0 and z != last:
                        if firstz == 0:
                            firstz = z
                        last = z
                        if z == 1:
                            pv += 1
                            if pv >= n_p and j >= age and (first == 0 or first == firstz):
                                armed = True; act = j + delay
                                armed_out[k] = 1
                                if action == 1:
                                    act = j + delay - 1
                                    if act <= j:
                                        res = c; closed = True
                                break
                if closed:
                    break
        if np.isnan(res):
            res = CLS[o + n - 1]
        out[k] = res
    return out, armed_out


class DS:
    """Düzleştirilmiş yol veri seti."""

    def __init__(self, paths, rr, meta: pd.DataFrame):
        self.meta = meta.reset_index(drop=True)
        ln = np.array([len(p["fav"]) for p in paths], np.int64)
        off = np.zeros(len(paths), np.int64); off[1:] = np.cumsum(ln)[:-1]
        cat = lambda k: np.concatenate([np.asarray(p[k], float) for p in paths])
        self.FAV, self.ADV, self.OPN, self.CLS = cat("fav"), cat("adv"), cat("opn"), cat("cls")
        self.off, self.ln = off, ln
        self.rr = np.asarray(rr, float)
        self.base = self.run(P=9e9, L=9e9, n_p=999)[0]

    def run(self, P=0.6, Pa=None, L=0.2, first=0, n_p=1, lock=0.0, lock_tp=False,
            age=0, delay=1, action=0):
        rr = self.rr
        PpR = P * rr; PaR = (Pa if Pa is not None else P) * rr
        LR = np.full(len(rr), L)
        lockR = lock * rr if lock_tp else np.full(len(rr), lock)
        return run_rule(self.FAV, self.ADV, self.OPN, self.CLS, self.off, self.ln, rr,
                        PpR, PaR, LR, first, n_p, lockR, age, delay, action)


# ─── veri seti kurucuları ─────────────────────────────────────────────────────

def _bars(sym):
    m = pd.read_pickle(f"fx_{sym}_1m.pkl")[["open", "high", "low", "close"]].astype(float)
    return m


def _path(O, H, L, C, i, n, e, risk, sg, sp):
    seg = slice(i, min(i + n, len(C)))
    if sg > 0:
        return dict(fav=(H[seg] - e) / risk, adv=(L[seg] - e) / risk,
                    opn=(O[seg] - e) / risk, cls=(C[seg] - e) / risk)
    return dict(fav=(e - L[seg] - sp) / risk, adv=(e - H[seg] - sp) / risk,
                opn=(e - O[seg] - sp) / risk, cls=(e - C[seg] - sp) / risk)


def build_A():
    df = pd.read_pickle("paths_stats.pkl")
    df = df[df.exit.isin(["tp", "sl"])].copy()
    paths = [{k: np.asarray(p[k])[1:] for k in ("fav", "adv", "opn", "cls")} for p in df.path]
    meta = pd.DataFrame(dict(t=df.open_utc.values, sym=df.sym.values, dir=df.dir.values,
                             usd_R=(df.risk * df.volume * np.where(df.sym == "USOIL.FOREX", 100.0, 1.0)).values,
                             scope=df.scope.fillna("").values))
    return DS(paths, df.rr.values, meta)


def build_B(horizon=2880):
    """Pulse sinyalleri → botun sabit geometrisiyle broker barlarında (çakışmasız)."""
    from sim import simulate
    src = {"NDX.INDX": ("pl_ndx.pkl", "2026-07-06", "2026-09-30"),
           "GDAXI.INDX": ("pl_dax.pkl", "2026-07-06", "2026-09-30"),
           "USOIL.FOREX": ("pl_usoil.pkl", "2026-06-20", "2026-09-02")}
    paths, rrs, rows = [], [], []
    for sym, (f, a, b) in src.items():
        m = _bars(sym); T = m.index
        O, H, L, C = (m[c].values for c in ("open", "high", "low", "close"))
        tp_v, sl_v, pct = GEOM[sym]; sp = SPREAD[sym]
        pl = pd.read_pickle(f); pl["t"] = pd.to_datetime(pl.created_at)
        pl = pl[(pl.t >= a) & (pl.t < b)].sort_values("t")
        for d in ("BUY", "SELL"):
            sg = 1 if d == "BUY" else -1
            busy = pd.Timestamp("2000-01-01", tz="UTC")
            for s in pl[pl.ml_direction == d].itertuples():
                if s.t < busy:
                    continue
                i = T.searchsorted(s.t.ceil("min"))
                if i + 30 >= len(T) or (T[i] - s.t) > pd.Timedelta(minutes=5):
                    continue
                e = O[i] + (sp if sg > 0 else 0.0)
                risk = e * sl_v / 100 if pct else sl_v
                rr = tp_v / sl_v
                p = _path(O, H, L, C, i, horizon, e, risk, sg, sp)
                R, idx, _ = simulate(p, rr, start=0)
                busy = T[min(i + idx, len(T) - 1)]
                paths.append(p); rrs.append(rr)
                rows.append(dict(t=s.t, sym=sym, dir=d, model=s.model_type))
    return DS(paths, rrs, pd.DataFrame(rows))


def build_C(step=30, horizon=2880):
    """Rastgele (sabit aralıklı) girişler, iki yön, sembol geometrisi."""
    per = {"NDX.INDX": ("2026-07-06", "2026-09-28"), "GDAXI.INDX": ("2026-07-06", "2026-09-28"),
           "USOIL.FOREX": ("2026-06-20", "2026-09-28")}
    paths, rrs, rows = [], [], []
    for sym, (a, b) in per.items():
        m = _bars(sym).loc[a:b]; T = m.index
        O, H, L, C = (m[c].values for c in ("open", "high", "low", "close"))
        tp_v, sl_v, pct = GEOM[sym]; sp = SPREAD[sym]
        for i in range(300, len(T) - horizon, step):
            if (T[i + 60] - T[i]) / np.timedelta64(1, "m") > 90:
                continue
            for sg, d in ((1, "BUY"), (-1, "SELL")):
                e = O[i] + (sp if sg > 0 else 0.0)
                risk = e * sl_v / 100 if pct else sl_v
                paths.append(_path(O, H, L, C, i, horizon, e, risk, sg, sp))
                rrs.append(tp_v / sl_v)
                rows.append(dict(t=T[i], sym=sym, dir=d))
    return DS(paths, rrs, pd.DataFrame(rows))
