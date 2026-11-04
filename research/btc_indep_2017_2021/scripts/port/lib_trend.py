"""fam_trend ortak motor: 1m yol çözümü (binary lifting), maliyet/swap, indikatörler, metrikler.

Zaman birimi: UTC dakika (int64, epoch'tan). Bar `ts` = açılış; karar = açılış + TF.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/data")
CACHE = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_indep_2017_2021/cache")
CACHE.mkdir(exist_ok=True)

SPREAD_BASE = 0.000185      # gidiş-dönüş, fiyat oranı
SPREAD_STRESS = 0.00028
SPREAD_ABS = 15.0           # $ gidiş-dönüş
SWAP_LONG = -0.14 / 365     # gecelik, nominal oranı
SWAP_SHORT = 0.02 / 365
MAX_ENTRY_DELAY = 10        # dk

EX0 = int(pd.Timestamp("2023-03-24 11:28", tz="UTC").value // 60_000_000_000)
EX1 = int(pd.Timestamp("2023-03-24 14:00", tz="UTC").value // 60_000_000_000)


def tmin(s) -> np.ndarray:
    """datetime64[ns, UTC] serisi → epoch dakika int64."""
    return (pd.to_datetime(s).astype("int64") // 60_000_000_000).to_numpy(np.int64)


def m(ts: str) -> int:
    return int(pd.Timestamp(ts, tz="UTC").value // 60_000_000_000)


SPLITS = {
    "A": (m("2017-08-17"), m("2020-01-11")),
    "PERP": (m("2020-01-11"), m("2021-06-01")),
}


def split_of(dec: np.ndarray) -> np.ndarray:
    out = np.full(len(dec), "", dtype=object)
    for k, (a, b) in SPLITS.items():
        out[(dec >= a) & (dec < b)] = k
    return out


# ───────────────────────── 1m veri + seyrek tablolar ─────────────────────────
class M1:
    def __init__(self, levels: int = 16):
        f = CACHE / "m1.npz"
        if f.exists():
            z = np.load(f)
            T, O, H, L, C = z["T"], z["O"], z["H"], z["L"], z["C"]
        else:
            d = pd.read_parquet(DATA / "btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
            T = tmin(d["ts"])
            keep = ~((T >= EX0) & (T < EX1))
            T, O, H, L, C = (T[keep], d["open"].to_numpy()[keep], d["high"].to_numpy()[keep],
                             d["low"].to_numpy()[keep], d["close"].to_numpy()[keep])
            np.savez(f, T=T, O=O, H=H, L=L, C=C)
        self.T, self.O, self.H, self.L, self.C = T, O, H, L, C
        self.N = len(T)
        self.levels = levels
        pad = (1 << levels) + 2
        lo = np.concatenate([L, np.full(pad, np.inf)])
        hi = np.concatenate([H, np.full(pad, -np.inf)])
        self.mn, self.mx = [lo], [hi]
        for lv in range(1, levels):
            s = 1 << (lv - 1)
            a, b = self.mn[-1], self.mx[-1]
            self.mn.append(np.minimum(a, np.concatenate([a[s:], np.full(s, np.inf)])))
            self.mx.append(np.maximum(b, np.concatenate([b[s:], np.full(s, -np.inf)])))
        # rollover anları: 17:00 New York → UTC dakika
        days = pd.date_range("2017-08-01", "2021-07-01", freq="D")
        ro = pd.DatetimeIndex([pd.Timestamp(f"{x.date()} 17:00", tz="America/New_York") for x in days])
        self.RO = tmin(pd.Series(ro.tz_convert("UTC")))

    def _first(self, k, e, thr, below: bool):
        """[k,e] içinde ilk j: low[j] ≤ thr (below) / high[j] ≥ thr. Yoksa e+1."""
        pos = k.copy()
        if len(pos) == 0:
            return pos
        maxlen = int(np.max(e - k + 1))
        L = max(0, int(np.ceil(np.log2(maxlen + 1))))
        if L >= self.levels:
            raise ValueError("tutuş seyrek tablodan uzun")
        tab = self.mn if below else self.mx
        for lv in range(L, -1, -1):
            step = 1 << lv
            okb = pos + step - 1 <= e
            v = tab[lv][pos]
            adv = okb & ((v > thr) if below else (v < thr))
            pos = pos + step * adv
        return pos

    def simulate(self, dec, dirn, sl_d, tp_d, end, sig_close, spread=SPREAD_BASE,
                 spread_abs=None, optimistic=False) -> dict:
        dec = np.asarray(dec, np.int64)
        dirn = np.asarray(dirn, np.int64)
        sl_d = np.asarray(sl_d, float)
        tp_d = np.asarray(tp_d, float)
        end = np.asarray(end, np.int64)
        n = len(dec)
        T, O, C = self.T, self.O, self.C
        k = np.searchsorted(T, dec, "left")
        ok = k < self.N
        kk = np.minimum(k, self.N - 1)
        ok &= (T[kk] - dec) <= MAX_ENTRY_DELAY
        e = np.searchsorted(T, end, "left") - 1
        ok &= e >= kk
        ok &= np.isfinite(sl_d) & (sl_d > 0)
        censored_end = end > T[-1] + 1
        ok_idx = np.where(ok)[0]
        R = np.full(n, np.nan)
        pct = np.full(n, np.nan)
        typ = np.full(n, -1, np.int8)  # 0 SL, 1 TP, 2 zaman
        ent_t = np.full(n, -1, np.int64)
        ex_t = np.full(n, np.nan)
        if len(ok_idx):
            k1, e1 = kk[ok_idx], e[ok_idx]
            dd, sl1, tp1 = dirn[ok_idx], sl_d[ok_idx], tp_d[ok_idx]
            op = O[k1]
            if optimistic:
                h = np.zeros(len(k1))
                entry = np.asarray(sig_close, float)[ok_idx]
            else:
                h = (spread_abs / 2.0) * np.ones(len(k1)) if spread_abs is not None else op * spread / 2.0
                entry = op + dd * h
            SL = entry - dd * sl1
            TP = entry + dd * tp1
            jsl = np.full(len(k1), np.iinfo(np.int64).max // 4)
            jtp = jsl.copy()
            for sgn in (1, -1):
                s = dd == sgn
                if not s.any():
                    continue
                if sgn == 1:
                    jsl[s] = self._first(k1[s], e1[s], SL[s] + h[s], below=True)
                else:
                    jsl[s] = self._first(k1[s], e1[s], SL[s] - h[s], below=False)
                st = s & np.isfinite(TP)
                if st.any():
                    if sgn == 1:
                        jtp[st] = self._first(k1[st], e1[st], TP[st] + h[st], below=False)
                    else:
                        jtp[st] = self._first(k1[st], e1[st], TP[st] - h[st], below=True)
            hsl = jsl <= e1
            htp = jtp <= e1
            slf = hsl & (~htp | (jsl <= jtp))
            tpf = htp & ~slf
            tim = ~slf & ~tpf
            exitp = np.empty(len(k1))
            jj = np.where(slf, jsl, 0)
            exitp[slf] = np.where(dd[slf] == 1, np.minimum(SL[slf], O[jj[slf]] - h[slf]),
                                  np.maximum(SL[slf], O[jj[slf]] + h[slf]))
            exitp[tpf] = TP[tpf]
            exitp[tim] = C[e1[tim]] - dd[tim] * h[tim]
            jx = np.where(slf, jsl, np.where(tpf, jtp, e1))
            ext = np.where(tim, T[e1] + 1.0, T[np.minimum(jx, self.N - 1)] + 0.5)
            et = T[k1]
            nights = np.searchsorted(self.RO, ext, "left") - np.searchsorted(self.RO, et, "right")
            rate = np.where(dd == 1, SWAP_LONG, SWAP_SHORT)
            swap = nights * rate * entry
            pnl = dd * (exitp - entry) + swap
            r = pnl / sl1
            pc = pnl / entry * 100.0
            # zaman çıkışı veri sonunu aşıyorsa (sansürlü) at
            bad = tim & censored_end[ok_idx]
            r[bad] = np.nan
            R[ok_idx], pct[ok_idx] = r, pc
            typ[ok_idx] = np.where(slf, 0, np.where(tpf, 1, 2))
            ent_t[ok_idx] = et
            ex_t[ok_idx] = ext
        return dict(R=R, pct=pct, typ=typ, ent=ent_t, ext=ex_t)


# ───────────────────────── indikatörler ─────────────────────────
def atr_wilder(h, l, c, n=14) -> np.ndarray:
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    a = pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().to_numpy()
    a[: n - 1] = np.nan
    return a


def ema(c, n) -> np.ndarray:
    a = pd.Series(c).ewm(span=n, adjust=False).mean().to_numpy()
    a[: n - 1] = np.nan
    return a


def prev_max(x, n) -> np.ndarray:
    """önceki n barın maksimumu (bu bar hariç)."""
    return pd.Series(x).rolling(n).max().shift(1).to_numpy()


def prev_min(x, n) -> np.ndarray:
    return pd.Series(x).rolling(n).min().shift(1).to_numpy()


def psar(h, l, af0=0.02, step=0.02, afmax=0.2) -> np.ndarray:
    n = len(h)
    sar = np.full(n, np.nan)
    if n < 3:
        return sar
    up = h[1] >= h[0]
    ep = h[1] if up else l[1]
    s = l[0] if up else h[0]
    af = af0
    sar[1] = s
    for i in range(2, n):
        s = s + af * (ep - s)
        if up:
            s = min(s, l[i - 1], l[i - 2])
            if l[i] < s:
                up, s, ep, af = False, ep, l[i], af0
            elif h[i] > ep:
                ep, af = h[i], min(af + step, afmax)
        else:
            s = max(s, h[i - 1], h[i - 2])
            if h[i] > s:
                up, s, ep, af = True, ep, h[i], af0
            elif l[i] < ep:
                ep, af = l[i], min(af + step, afmax)
        sar[i] = s
    return sar


def load_tf(name: str, tf_min: int) -> pd.DataFrame:
    d = pd.read_parquet(DATA / f"btc_{name}.parquet")
    d["om"] = tmin(d["ts"])
    d["dec"] = d["om"] + tf_min
    d["excl"] = (d["om"] < EX1) & (d["dec"] > EX0)
    d["atr"] = atr_wilder(d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy())
    return d.reset_index(drop=True)


def asof(left_dec: np.ndarray, right: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """sağ çerçevenin karar (kapanış) anı ≤ sol karar anı olan son satırı."""
    r = right[["dec"] + cols].rename(columns={"dec": "rdec"}).sort_values("rdec")
    lft = pd.DataFrame({"dec": left_dec})
    out = pd.merge_asof(lft, r, left_on="dec", right_on="rdec", direction="backward")
    return out[cols]


# ───────────────────────── metrikler ─────────────────────────
RNG = np.random.default_rng(20261021)


def day_boot(R, day, B=2000, rng=None):
    rng = rng or np.random.default_rng(7)
    if len(R) < 2:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=R)
    nn = np.bincount(inv).astype(float)
    D = len(u)
    W = rng.multinomial(D, np.full(D, 1.0 / D), size=B).astype(float)
    means = (W @ S) / (W @ nn)
    return float(np.mean(means > 0)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def cluster_z(R, day):
    if len(R) < 3:
        return np.nan
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=R)
    nn = np.bincount(inv).astype(float)
    mu = S.sum() / nn.sum()
    D = len(u)
    if D < 3:
        return np.nan
    se = np.sqrt(np.sum((S - nn * mu) ** 2) * D / (D - 1)) / nn.sum()
    return float(mu / se) if se > 0 else np.nan


def single_position(ent, ext) -> np.ndarray:
    """zaman sıralı; önceki çıkıştan önce girilen olay atlanır. seçilen indeksleri döndürür."""
    o = np.argsort(ent, kind="stable")
    keep = []
    last = -np.inf
    for i in o:
        if ent[i] >= last:
            keep.append(i)
            last = ext[i]
    return np.array(keep, dtype=int)


def be_wr(R):
    w, ls = R[R > 0], R[R <= 0]
    if len(w) == 0 or len(ls) == 0:
        return np.nan
    a, b = w.mean(), -ls.mean()
    return float(b / (a + b))
