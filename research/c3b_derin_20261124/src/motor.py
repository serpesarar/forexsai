"""motor.py — C3b varyant motoru (PROTOCOL.md): ortak simülatör, dozlar, ölçüler.

Panel arayüzü: days (tarih), S (karar fiyatı), pnl(i, j, entry) → net bp, stres (bool dizi). RSI2 ve z5 S'ten hesaplanır.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

RSI_TH = 10.0
MAX_HOLD = 5
Z5_TH = -1.072
VIX_TH = 18.4
OPEX_MULT = 0.5
CANDS = ("BASE", "D1", "D2", "D3", "X1", "X2", "K1", "K2")
CANDS2 = ("BASE", "V1", "E16", "V1K2")
CANDS3 = ("BASE", "Y1", "Y2", "Y3")
VIX_EXIT = 1.10


def rsi2(x: np.ndarray) -> np.ndarray:
    """Wilder RSI(2), rules.rsi2 / c3b_shadow ile aynı özyineleme."""
    out = np.full(len(x), np.nan)
    up = dn = 0.0
    for i in range(1, len(x)):
        g = x[i] - x[i - 1]
        if i == 1:
            up, dn = max(g, 0.0), max(-g, 0.0)
        else:
            up = 0.5 * max(g, 0.0) + 0.5 * up
            dn = 0.5 * max(-g, 0.0) + 0.5 * dn
        out[i] = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
    return out


def z5_of(S: np.ndarray) -> np.ndarray:
    """z5 = (S_d/S_{d−5} − 1)/(dvol·√5), dvol = son 20 getirinin std'si, d−1'e kadar (kd_ortak._multi)."""
    s = pd.Series(S)
    dvol = s.pct_change().rolling(20).std().shift(1)
    return ((s / s.shift(5) - 1) / (dvol * np.sqrt(5))).to_numpy()


def opex_week(d: date) -> bool:
    first = date(d.year, d.month, 1)
    fri3 = first.toordinal() + (4 - first.weekday()) % 7 + 14
    return fri3 - 4 <= d.toordinal() <= fri3


@dataclass
class Tr:
    i: int
    j: int
    vd: bool
    stress: bool
    deep: bool


def simulate(S: np.ndarray, stress: np.ndarray, mode: str, entry_ref: callable | None = None,
             vix: np.ndarray | None = None) -> list[Tr]:
    """Tek pozisyon C3b. mode: 'up' (taban), 'x1' (VD → up, diğer → ertesi gün), 'be' (yükseliş ∧ S ≥ giriş, ≤ 5 gün).
    Çıkış günü yeni sinyal varsa aynı gün yeniden girilir (canlı kod). entry_ref(i) → giriş fiyatı (be için; yoksa S[i]).
    'vx' = 'up' + VIX koruması: vix[i] (i gününden önceki VIX kapanışı) ≥ VIX_EXIT × vix[giriş] → çık (TUR 2 V1)."""
    r, z = rsi2(S), z5_of(S)
    out: list[Tr] = []
    pos = None
    for i in range(len(S)):
        if pos is not None:
            k, vd, ref = pos["k"], pos["vd"], pos["ref"]
            up = S[i] > S[i - 1]
            held = i - k
            if mode == "up" or (mode == "x1" and vd):
                ex = up or held >= MAX_HOLD
            elif mode == "vx":
                ex = up or held >= MAX_HOLD or (np.isfinite(vix[i]) and np.isfinite(vix[k]) and vix[i] >= VIX_EXIT * vix[k])
            elif mode == "x1":
                ex = held >= 1
            else:  # be
                ex = (up and S[i] >= ref) or held >= MAX_HOLD
            if ex:
                out.append(Tr(k, i, vd, pos["st"], pos["dp"]))
                pos = None
        if pos is None and np.isfinite(r[i]) and r[i] < RSI_TH:
            dp = bool(np.isfinite(z[i]) and z[i] <= Z5_TH)
            st = bool(stress[i])
            pos = {"k": i, "vd": st and dp, "st": st, "dp": dp, "ref": entry_ref(i) if entry_ref else S[i]}
    return out


def weight(t: Tr, cand: str) -> float:
    if cand in ("D1", "K1"):
        return 1.0 if t.vd else 1 / 3
    if cand in ("D2", "K2", "V1K2"):
        return 0.25 + 0.375 * t.stress + 0.375 * t.deep
    if cand == "D3":
        return 1.0 if t.vd else 0.0
    return 1.0


def mode_of(cand: str) -> str:
    return {"X1": "x1", "X2": "be", "V1": "vx", "V1K2": "vx"}.get(cand, "up")


def entry16(cand: str) -> bool:
    return cand in ("K1", "K2", "E16", "V1K2", "Y3")


def exit_kind(cand: str) -> str:
    """'1530' (canlı), '1600' (Y1), 'next0930' (Y2/Y3; çıkış günü yeniden giriş varsa 15:30'da kalır)."""
    return {"Y1": "1600", "Y2": "next0930", "Y3": "next0930"}.get(cand, "1530")


def reentry_flags(tr: list) -> list[bool]:
    """İşlemin çıkış günü aynı anda yeni işlem açılıyor mu (o zaman çıkış 15:30'da kalır)."""
    starts = {t.i for t in tr}
    return [t.j in starts for t in tr]


# ───────── ölçüler (gün serisi, ölçekten bağımsız) ─────────
def stats(s: pd.Series) -> dict:
    s = s.sort_index()
    eq = s.cumsum()
    dd = eq - eq.cummax()
    mo = s.groupby(pd.to_datetime(pd.Index(s.index)).to_period("M")).sum()
    if len(mo):
        mo = mo.reindex(pd.period_range(mo.index.min(), mo.index.max(), freq="M"), fill_value=0.0)
    tot, mdd = float(s.sum()), float(dd.min()) if len(dd) else 0.0
    srt = np.sort(s.values)
    return {"toplam": tot, "maks_dusus": mdd, "calmar": tot / abs(mdd) if mdd < 0 else np.nan,
            "sharpe": float(mo.mean() / mo.std() * math.sqrt(12)) if len(mo) > 2 and mo.std() > 0 else np.nan,
            "en_kotu_gun": float(srt[0]) if len(srt) else np.nan, "en_kotu_10": float(srt[:10].sum())}


def monthly(s: pd.Series, months: pd.PeriodIndex) -> np.ndarray:
    mo = s.groupby(pd.to_datetime(pd.Index(s.index)).to_period("M")).sum()
    return mo.reindex(months, fill_value=0.0).to_numpy()


def boot_sr(a: np.ndarray, b: np.ndarray, n: int = 4000, seed: int = 5) -> float:
    """Aylık eşli bootstrap P(SR_a > SR_b)."""
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(a), (n, len(a)))
    A, B = a[ix], b[ix]
    return float((A.mean(1) / (A.std(1) + 1e-12) > B.mean(1) / (B.std(1) + 1e-12)).mean())


def sr(v: np.ndarray) -> float:
    sd = v.std(ddof=1)
    return float(v.mean() / sd * math.sqrt(12)) if sd > 0 else np.nan
