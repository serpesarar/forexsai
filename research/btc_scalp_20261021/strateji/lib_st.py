"""Strateji inşası ortak motoru (prereg.md §2).

- 1m yol + ilk-dokunuş: research/btc_5y_20261021/fam_trend/lib_trend.M1 (kaba-döngüyle doğrulanmış binary lifting).
- Bu modül üstüne: SL kayması (1 bp / sıcak dakikada 5 bp), limit giriş (≥1 bp içinden geçme), maliyet varyantları, swap.
- Zaman birimi: epoch dakika (int64). Dense ızgara indeksi (feasibility/lib.py) = epoch − T0M.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel/research")
sys.path.insert(0, str(ROOT / "btc_5y_20261021" / "fam_trend"))
sys.path.insert(0, str(ROOT / "btc_scalp_20261021" / "feasibility"))
import lib_trend as lt  # noqa: E402

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
RES.mkdir(exist_ok=True)

SPREAD = {"base": 0.000185, "stress": 0.0002775}
SPREAD_ABS = 15.0
SWAP_LONG = -0.14 / 365
SWAP_SHORT = 0.02 / 365
SLIP_BP, SLIP_HOT_BP = 1.0, 5.0
LIMIT_THROUGH_BP = 1.0
MAX_DELAY = 10
T0M = int(pd.Timestamp("2021-06-01", tz="UTC").value // 60_000_000_000)


def em(ts: str) -> int:
    return lt.m(ts)


SPLITS = {"DISC": (em("2021-06-01"), em("2024-01-01")),
          "OOS": (em("2024-01-11"), em("2025-07-01")),
          "BLIND": (em("2025-07-01"), em("2026-10-21"))}


def split_of(t: np.ndarray) -> np.ndarray:
    out = np.full(len(t), "", dtype=object)
    for k, (a, b) in SPLITS.items():
        out[(t >= a) & (t < b)] = k
    return out


class Engine:
    def __init__(self) -> None:
        self.m1 = lt.M1()
        m = self.m1
        self.T, self.O, self.H, self.L, self.C = m.T, m.O, m.H, m.L, m.C
        self.N = m.N
        lc = np.log(self.C)
        ar = np.abs(np.diff(lc, prepend=np.nan)) * 1e4
        a, b = SPLITS["DISC"]
        msk = (self.T >= a) & (self.T < b)
        self.hot_thr = float(np.nanpercentile(ar[msk], 99))
        self.hot = ar > self.hot_thr
        self.RO = m.RO

    # ------------------------------------------------------------------ yardımcı
    def row_at_or_after(self, t: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.T, np.asarray(t, np.int64), "left")

    def last_row_before(self, t: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.T, np.asarray(t, np.int64), "left") - 1

    def _half(self, px: np.ndarray, mode: str) -> np.ndarray:
        if mode == "opt":
            return np.zeros(len(px))
        if mode == "abs":
            return np.full(len(px), SPREAD_ABS / 2.0)
        return px * SPREAD[mode] / 2.0

    # ------------------------------------------------------------------ ana simülasyon
    def simulate(self, ent, dirn, sl_d, tp_d, end, sig_close=None, mode: str = "base", slip: bool = True,
                 limit_k=None, limit_W: int = 0, limit_fallback: str = "skip") -> pd.DataFrame:
        """ent: hedef giriş dakikası (epoch; o dakikanın açılışında gir). end: çıkış = T<end olan son barın kapanışı.
        sl_d/tp_d: fiyat mesafesi (tp_d NaN = TP yok). limit_k: None → piyasa; aksi hâlde k×ATR (fiyat, dizi) limit derinliği.
        Dönüş: olay başına satır (geçersizler dahil, R=NaN)."""
        ent = np.asarray(ent, np.int64)
        dd = np.asarray(dirn, np.int64)
        sl_d = np.asarray(sl_d, float)
        tp_d = np.asarray(tp_d, float)
        end = np.asarray(end, np.int64)
        n = len(ent)
        T, O, C = self.T, self.O, self.C
        k = self.row_at_or_after(ent)
        kc = np.minimum(k, self.N - 1)
        ok = (k < self.N) & ((T[kc] - ent) <= MAX_DELAY)
        e_last = self.last_row_before(end)
        ok &= e_last >= kc
        ok &= np.isfinite(sl_d) & (sl_d > 0)
        ok &= ~(end > T[-1] + 1)
        filled = np.ones(n, bool)
        fill_row = kc.copy()
        if mode == "opt":
            sc = np.asarray(sig_close, float)
            h = np.zeros(n)
            entry = sc.copy()
        else:
            h = self._half(O[kc], mode)
            entry = O[kc] + dd * h
        if limit_k is not None:
            depth = np.asarray(limit_k, float)
            ok &= np.isfinite(depth)
            refa = O[kc] + dd * self._half(O[kc], mode if mode != "opt" else "base")
            Lp = refa - dd * depth
            hh = self._half(Lp, mode if mode != "opt" else "base")
            thr_mid = Lp - dd * (hh + LIMIT_THROUGH_BP * 1e-4 * Lp)
            wend = self.last_row_before(T[kc] + limit_W)
            wend = np.minimum(wend, e_last)
            f = np.full(n, self.N + 5, np.int64)
            for sg in (1, -1):
                s = ok & (dd == sg) & (wend >= kc)
                if s.any():
                    f[s] = self.m1._first(kc[s], wend[s], thr_mid[s], below=(sg == 1))
            filled = ok & (f <= wend)
            fill_row = np.where(filled, f, kc)
            if mode == "opt":
                entry = np.where(filled, Lp, entry)
            else:
                entry = np.where(filled, Lp, entry)
            # dolmayan: skip veya W sonunda piyasa
            nf = ok & ~filled
            if limit_fallback == "skip":
                ok &= filled
            else:
                km = self.row_at_or_after(T[kc] + limit_W)
                kmc = np.minimum(km, self.N - 1)
                okm = (km < self.N) & ((T[kmc] - (T[kc] + limit_W)) <= MAX_DELAY) & (kmc <= e_last)
                ok &= ~(nf & ~okm)
                fill_row = np.where(nf, kmc, fill_row)
                if mode == "opt":
                    entry = np.where(nf, C[np.maximum(kmc - 1, 0)], entry)
                else:
                    hm = self._half(O[kmc], mode)
                    entry = np.where(nf, O[kmc] + dd * hm, entry)
                    h = np.where(nf, hm, h)
            h = np.where(filled, hh if mode != "opt" else 0.0, h)
        SL = entry - dd * sl_d
        TP = entry + dd * tp_d
        idx = np.where(ok)[0]
        out = dict(R=np.full(n, np.nan), bp=np.full(n, np.nan), typ=np.full(n, -1, np.int8),
                   ent_t=np.full(n, -1, np.int64), ext_t=np.full(n, -1.0), samebar=np.zeros(n, bool),
                   filled=filled & ok, entry=entry, nights=np.zeros(n, np.int64))
        if len(idx):
            r0 = fill_row[idx]
            e1 = e_last[idx]
            d1, h1, sl1, tp1 = dd[idx], h[idx], SL[idx], TP[idx]
            lim = (limit_k is not None) & filled[idx] if limit_k is not None else np.zeros(len(idx), bool)
            jsl = np.full(len(idx), np.iinfo(np.int64).max // 4)
            jtp = jsl.copy()
            for sg in (1, -1):
                s = d1 == sg
                if not s.any():
                    continue
                if sg == 1:
                    jsl[s] = self.m1._first(r0[s], e1[s], sl1[s] + h1[s], below=True)
                else:
                    jsl[s] = self.m1._first(r0[s], e1[s], sl1[s] - h1[s], below=False)
                st = s & np.isfinite(tp1)
                if st.any():
                    tstart = r0[st] + lim[st].astype(np.int64)  # limit dolum dakikasında TP yok
                    okst = tstart <= e1[st]
                    tmp = np.full(int(st.sum()), np.iinfo(np.int64).max // 4)
                    if okst.any():
                        ss = np.where(st)[0][okst]
                        if sg == 1:
                            tmp[okst] = self.m1._first(tstart[okst], e1[ss], tp1[ss] + h1[ss], below=False)
                        else:
                            tmp[okst] = self.m1._first(tstart[okst], e1[ss], tp1[ss] - h1[ss], below=True)
                    jtp[st] = tmp
            hsl = jsl <= e1
            htp = jtp <= e1
            slf = hsl & (~htp | (jsl <= jtp))
            tpf = htp & ~slf
            tim = ~slf & ~tpf
            same = hsl & htp & (jsl == jtp)
            ex = np.empty(len(idx))
            jj = np.where(slf, jsl, 0)
            if mode == "opt" or not slip:
                sp = np.zeros(len(idx))
            else:
                sp = np.where(self.hot[jj], SLIP_HOT_BP, SLIP_BP) * 1e-4 * sl1
            gapf = np.where(d1 == 1, np.minimum(sl1, O[jj] - h1), np.maximum(sl1, O[jj] + h1))
            ex[slf] = (gapf - d1 * sp)[slf]
            ex[tpf] = tp1[tpf]
            ex[tim] = (C[e1] - d1 * h1)[tim]
            jx = np.where(slf, jsl, np.where(tpf, jtp, e1))
            ext = np.where(tim, T[e1] + 1.0, T[np.minimum(jx, self.N - 1)] + 0.5)
            et = T[r0]
            nights = np.searchsorted(self.RO, ext, "left") - np.searchsorted(self.RO, et, "right")
            en = entry[idx]
            swap = nights * np.where(d1 == 1, SWAP_LONG, SWAP_SHORT) * en
            pnl = d1 * (ex - en) + swap
            out["R"][idx] = pnl / sl_d[idx]
            out["bp"][idx] = pnl / en * 1e4
            out["typ"][idx] = np.where(slf, 0, np.where(tpf, 1, 2))
            out["ent_t"][idx] = et
            out["ext_t"][idx] = ext
            out["samebar"][idx] = same
            out["nights"][idx] = nights
        return pd.DataFrame(out)


# ---------------------------------------------------------------------- kaba döngü (doğrulama)
def brute(E: Engine, ent, d, sl_d, tp_d, end, mode="base", slip=True, limit_k=None, limit_W=0, fb="skip"):
    T, O, H, L, C = E.T, E.O, E.H, E.L, E.C
    k = int(np.searchsorted(T, ent))
    if k >= E.N or T[k] - ent > MAX_DELAY:
        return np.nan
    e1 = int(np.searchsorted(T, end)) - 1
    if e1 < k or end > T[-1] + 1:
        return np.nan

    def half(px):
        return SPREAD_ABS / 2 if mode == "abs" else px * SPREAD[mode] / 2

    h = half(O[k])
    entry = O[k] + d * h
    r0 = k
    lim = False
    if limit_k is not None:
        Lp = entry - d * limit_k
        hh = half(Lp)
        thr = Lp - d * (hh + 1e-4 * Lp)
        wend = min(int(np.searchsorted(T, T[k] + limit_W)) - 1, e1)
        f = None
        for j in range(k, wend + 1):
            if (d == 1 and L[j] <= thr) or (d == -1 and H[j] >= thr):
                f = j
                break
        if f is not None:
            entry, r0, h, lim = Lp, f, hh, True
        elif fb == "skip":
            return np.nan
        else:
            km = int(np.searchsorted(T, T[k] + limit_W))
            if km >= E.N or T[km] - (T[k] + limit_W) > MAX_DELAY or km > e1:
                return np.nan
            h = half(O[km])
            entry = O[km] + d * h
            r0 = km
    SL = entry - d * sl_d
    TP = entry + d * tp_d
    ex = None
    jx = None
    for j in range(r0, e1 + 1):
        slhit = (L[j] - h <= SL) if d == 1 else (H[j] + h >= SL)
        tphit = False
        if np.isfinite(tp_d) and not (lim and j == r0):
            tphit = (H[j] - h >= TP) if d == 1 else (L[j] + h <= TP)
        if slhit:
            sp = (SLIP_HOT_BP if E.hot[j] else SLIP_BP) * 1e-4 * SL if slip else 0.0
            gf = min(SL, O[j] - h) if d == 1 else max(SL, O[j] + h)
            ex, jx = gf - d * sp, T[j] + 0.5
            break
        if tphit:
            ex, jx = TP, T[j] + 0.5
            break
    if ex is None:
        ex, jx = C[e1] - d * h, T[e1] + 1.0
    nights = np.searchsorted(E.RO, jx, "left") - np.searchsorted(E.RO, T[r0], "right")
    pnl = d * (ex - entry) + nights * (SWAP_LONG if d == 1 else SWAP_SHORT) * entry
    return pnl / sl_d


# ---------------------------------------------------------------------- istatistik
def day_boot(R, day, B=5000, seed=7):
    R = np.asarray(R, float)
    if len(R) < 2:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=R)
    nn = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    D = len(u)
    pick = rng.integers(0, D, size=(B, D))
    means = S[pick].sum(1) / nn[pick].sum(1)
    return float(np.mean(means > 0)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def single_position(ent, ext) -> np.ndarray:
    o = np.argsort(ent, kind="stable")
    keep, last = [], -np.inf
    for i in o:
        if ent[i] >= last:
            keep.append(i)
            last = ext[i]
    return np.array(keep, dtype=int)


def max_dd_R(R_sorted: np.ndarray) -> float:
    cs = np.concatenate([[0.0], np.cumsum(R_sorted)])
    return float(np.max(np.maximum.accumulate(cs) - cs))
