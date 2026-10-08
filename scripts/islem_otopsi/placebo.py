"""Plasebo tabanı (defter E13 / §0.5): aynı sembol, yön, UTC saati ve SL/TP FİYAT
mesafeleri — ama RASTGELE zaman. İki soruyu cevaplar:

  1. Botun giriş ANI rastgeleden iyi mi? (eşli fark: gerçek giriş − aynı geometride rastgele giriş)
  2. SL mekanizma payları (yön doğru/yanlış, hiç çalışmadı, neredeyse TP) rastgele yürüyüşün
     kendiliğinden ürettiği paylardan farklı mı? Farklı değilse "SL nedeni" anlatısı mekaniktir.

Her iki taraf da YÖNETİMSİZ yeniden oynatılır (BE/koştur yok) → elmayla elma.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S
from .compare import LOSS, WIN, first_legs
from .features import make_ctx
from .indicators import SymbolBars
from .stats import boot_mean_ci

PLACEBO_K = 5
PLACEBO_WINDOW_DAYS = 10
PLACEBO_EXCLUDE_MIN = 60


def simulate(sb: SymbolBars, s: int, entry: float, j0: int, risk: float, reward: float,
             spread: float) -> tuple[float, int, float]:
    """(R, çıkış bar konumu veya −1, çıkışa kadar MFE). Aynı barda iki bariyer → SL (muhafazakâr)."""
    a = sb.a
    j1 = min(j0 + S.REPLAY_MAX_HOLD_MIN, a["close"].size)
    hi, lo = a["high"][j0:j1], a["low"][j0:j1]
    if not hi.size:
        return np.nan, -1, np.nan
    adj = 0.0 if s > 0 else spread
    fav = s * ((hi if s > 0 else lo) + adj - entry) / risk
    adv = s * ((lo if s > 0 else hi) + adj - entry) / risk
    rr = reward / risk
    ks, kt = np.flatnonzero(adv <= -1.0), np.flatnonzero(fav >= rr)
    k_sl = ks[0] if ks.size else np.inf
    k_tp = kt[0] if kt.size else np.inf
    if np.isinf(k_sl) and np.isinf(k_tp):
        return float(s * (a["close"][j1 - 1] - entry) / risk), -1, float(fav.max())
    k = int(min(k_sl, k_tp))
    mfe = float(fav[:k].max()) if k > 0 else 0.0
    return (-1.0 if k_sl <= k_tp else rr), j0 + k, mfe


def verdict_after(sb: SymbolBars, s: int, entry: float, risk: float, reward: float, spread: float,
                  j_exit: int, horizon: int = S.POST_EXIT_MIN) -> str:
    """SL sonrası hüküm — path.sl_verdict ile aynı tanım (r_exit = −1)."""
    a = sb.a
    t_end = sb.m1.index[j_exit] + pd.Timedelta(minutes=horizon)
    j1 = sb.pos_at(t_end)
    if j1 <= j_exit + 1:
        return ""
    adj = 0.0 if s > 0 else spread
    hi, lo = a["high"][j_exit + 1:j1], a["low"][j_exit + 1:j1]
    fav = s * ((hi if s > 0 else lo) + adj - entry) / risk
    adv = s * ((lo if s > 0 else hi) + adj - entry) / risk
    if (fav >= reward / risk).any():
        return "YON_DOGRU"
    if adv.min() <= -1.0 - S.WRONG_DIR_EXTRA_R and not (fav >= 0).any():
        return "YON_YANLIS"
    return "KARARSIZ"


def _candidates(sb: SymbolBars, t0: pd.Timestamp) -> np.ndarray:
    idx = sb.m1.index
    lo = idx.searchsorted(t0 - pd.Timedelta(days=PLACEBO_WINDOW_DAYS))
    hi = idx.searchsorted(t0 + pd.Timedelta(days=PLACEBO_WINDOW_DAYS))
    pos = np.arange(lo, min(hi, idx.size - S.POST_EXIT_MIN))
    if not pos.size:
        return pos
    times = idx[pos]
    far = np.abs((times - t0).total_seconds()) > PLACEBO_EXCLUDE_MIN * 60
    return pos[(times.hour == t0.hour) & far]


def _one(sb: SymbolBars, c, j: int, s: int, kind: str, parent: pd.Series) -> dict:
    entry = c.entry if kind == "gerçek_giriş" else float(sb.a["open"][j]) + (c.spread if s > 0 else 0.0)
    R, j_exit, mfe = simulate(sb, s, entry, j, c.risk, c.reward, c.spread)
    out = "TP" if R > 0 and j_exit >= 0 else ("SL" if j_exit >= 0 else "ACIK")
    v = verdict_after(sb, s, entry, c.risk, c.reward, c.spread, j_exit) if out == "SL" else ""
    return {"pid": parent["pid"], "tur": kind, "side": parent["side"], "family": parent["family"],
            "R": R, "sonuc": out, "hukum": v, "mfe_r": mfe, "rr": c.reward / c.risk}


def run(t: pd.DataFrame, sbs: dict[str, SymbolBars], seed: int = S.RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _, r in first_legs(t).iterrows():
        if r["outcome"] not in (LOSS, WIN):
            continue
        sb = sbs[r["symbol"]]
        c = make_ctx(r, sb)
        if c is None or not (np.isfinite(c.risk) and np.isfinite(c.reward)) or c.i_exit < c.i_in0:
            continue
        cand = _candidates(sb, c.t0)
        if cand.size < PLACEBO_K:
            continue
        rows.append(_one(sb, c, c.i_in0, c.s, "gerçek_giriş", r))
        for j in rng.choice(cand, PLACEBO_K, replace=False):
            rows.append(_one(sb, c, int(j), c.s, "rastgele", r))
    return pd.DataFrame(rows)


def summarize(pl: pd.DataFrame) -> dict:
    """Gerçek giriş vs rastgele giriş: WR, ort R, eşli fark (bootstrap), SL mekanizma payları."""
    if pl.empty:
        return {}
    res = {"tablo": _rates(pl), "taraf": _rates(pl, "side")}
    real = pl[pl["tur"] == "gerçek_giriş"].set_index("pid")["R"]
    plac = pl[pl["tur"] == "rastgele"].groupby("pid")["R"].mean()
    diff = (real - plac.reindex(real.index)).dropna().to_numpy(float)
    lo, hi, p_pos = boot_mean_ci(diff)
    res["esli_fark"] = {"ort": float(diff.mean()) if diff.size else np.nan, "ci": (lo, hi), "p_pozitif": p_pos,
                        "n": int(diff.size)}
    return res


def _rates(pl: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    keys = ["tur"] + ([by] if by else [])
    rows = []
    for key, g in pl.groupby(keys):
        done = g[g["sonuc"] != "ACIK"]
        sl = done[done["sonuc"] == "SL"]
        rec = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
        rec.update({"n": len(done), "wr": (done["sonuc"] == "TP").mean() if len(done) else np.nan,
                    "ort_r": done["R"].mean(), "sl_yon_dogru": (sl["hukum"] == "YON_DOGRU").mean() if len(sl) else np.nan,
                    "sl_yon_yanlis": (sl["hukum"] == "YON_YANLIS").mean() if len(sl) else np.nan,
                    "sl_hic_calismadi": (sl["mfe_r"] < S.NEVER_WORKED_MFE_R).mean() if len(sl) else np.nan,
                    "sl_neredeyse_tp": (sl["mfe_r"] >= S.NEAR_TP_FRAC * sl["rr"]).mean() if len(sl) else np.nan})
        rows.append(rec)
    return pd.DataFrame(rows)
