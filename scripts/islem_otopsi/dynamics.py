"""Zaman dinamiği: giriş-hizalı R yolu (ayrışma dakikası), çıkış-hizalı hacim profili,
erken-çıkış bedeli ve kalibre edilmiş geometri karşı-olgusu (1m yeniden oynatma).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import settings as S
from .compare import LOSS, WIN, first_legs
from .features import _nanmean, make_ctx
from .indicators import SymbolBars
from .stats import auc

EARLY_K = (5, 10, 15, 30, 60)
EXIT_RULE_LEVELS = (0.3, 0.5)
EXIT_WINDOWS = ((-30, -21), (-20, -11), (-10, -1), (0, 0))


def _ctxs(t: pd.DataFrame, sbs: dict[str, SymbolBars]) -> list:
    out = []
    for _, r in first_legs(t).iterrows():
        if r["outcome"] not in (LOSS, WIN) or not np.isfinite(r["r_exit"]):
            continue
        c = make_ctx(r, sbs[r["symbol"]])
        if c is not None and np.isfinite(c.risk) and c.i_exit >= c.i_in0:
            out.append((r, c))
    return out


def entry_paths(t: pd.DataFrame, sbs: dict[str, SymbolBars], k_max: int = S.EVENT_ENTRY_MAX_MIN) -> dict:
    """R(k) matrisi: k dk sonra kapanış-R; çıkıştan sonra gerçekleşen R'de dondurulur."""
    items = _ctxs(t, sbs)
    n = len(items)
    R = np.full((n, k_max), np.nan)
    OPEN = np.zeros((n, k_max), dtype=bool)
    lab, rr = [], []
    for i, (r, c) in enumerate(items):
        js = c.i_in0 + np.arange(k_max)
        is_open = js < c.i_exit
        valid = js < c.sb.a["close"].size
        vals = np.where(is_open & valid, c.r(c.sb.a["close"][np.minimum(js, c.sb.a["close"].size - 1)]), r["r_exit"])
        R[i], OPEN[i] = vals, is_open
        lab.append(r["outcome"])
        rr.append(c.reward / c.risk if np.isfinite(c.reward) else np.nan)
    return {"R": R, "OPEN": OPEN, "lab": np.array(lab), "rr": np.array(rr),
            "r_exit": np.array([r["r_exit"] for r, _ in items])}


def divergence_minute(ep: dict) -> dict:
    """SL ve TP'nin AÇIK işlemler arasında belirgin ayrıştığı ilk dakika."""
    R, OPEN, lab = ep["R"], ep["OPEN"], ep["lab"]
    for k in range(R.shape[1]):
        a = R[(lab == WIN) & OPEN[:, k], k]
        b = R[(lab == LOSS) & OPEN[:, k], k]
        if a.size < S.MIN_GROUP_N or b.size < S.MIN_GROUP_N:
            continue
        gap = a.mean() - b.mean()
        se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size)
        if gap >= S.DIVERGENCE_GAP_R and se > 0 and gap / se >= S.DIVERGENCE_T:
            return {"dakika": k + 1, "fark_r": float(gap), "t": float(gap / se), "n_tp": a.size, "n_sl": b.size}
    return {}


def early_warning(ep: dict) -> pd.DataFrame:
    """k. dakikada açık işlemler: R_k SL'yi ne kadar ayırıyor + 'R_k ≤ −x ise çık' bedeli.

    Çıkış k. bar KAPANIŞINDAN varsayıldı (bir sonraki açılış daha dürüst ve biraz daha
    kötüdür) → kurtarılan R hafif İYİMSERDİR. Defter M9: bu tür kurallar 487 işlemde elendi.
    """
    R, OPEN, lab, rx = ep["R"], ep["OPEN"], ep["lab"], ep["r_exit"]
    rows = []
    for k in EARLY_K:
        if k > R.shape[1]:
            continue
        m = OPEN[:, k - 1]
        rk = R[m, k - 1]
        row = {"dakika": k, "acik_tp": int((lab[m] == WIN).sum()), "acik_sl": int((lab[m] == LOSS).sum()),
               "auc_tp_yuksek": auc(rk[lab[m] == WIN], rk[lab[m] == LOSS])}
        for x in EXIT_RULE_LEVELS:
            hit = rk <= -x
            delta = rk[hit] - rx[m][hit]
            lab_x = str(x).replace(".", ",")
            row[f"R≤−{lab_x}: yakalanan SL"] = int((lab[m][hit] == LOSS).sum())
            row[f"R≤−{lab_x}: öldürülen TP"] = int((lab[m][hit] == WIN).sum())
            row[f"R≤−{lab_x}: net R"] = float(delta.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def exit_volume_profile(t: pd.DataFrame, sbs: dict[str, SymbolBars]) -> pd.DataFrame:
    """Çıkıştan önceki pencerelerde mevsimsel hacim ve |hareket|/ATR — SL vs TP (yalnız işlem içi barlar)."""
    rows = []
    for r, c in _ctxs(t, sbs):
        a = c.sb.a
        rec = {"outcome": r["outcome"], "giris_oncesi": r.get("pre_vol_seas_15", np.nan)}
        for lo, hi in EXIT_WINDOWS:
            js = np.arange(c.i_exit + lo, c.i_exit + hi + 1)
            js = js[(js >= c.i_in0) & (js < a["close"].size)]
            key = f"{lo}..{hi}" if hi < 0 else "cikis_bari"
            rec[f"hacim {key}"] = _nanmean(a["vol_seas"][js]) if js.size else np.nan
            rec[f"hareket {key}"] = (float(np.nanmean(np.abs(a["close"][js] - a["open"][js]) / a["atr"][js]))
                                     if js.size else np.nan)
        rows.append(rec)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    out = []
    for col in [c for c in df.columns if c != "outcome"]:
        rec = {"ölçü": col}
        for name in (LOSS, WIN):
            x = df.loc[df["outcome"] == name, col].dropna()
            rec[f"{name} medyan"] = float(x.median()) if len(x) else np.nan
            rec[f"{name} n"] = int(len(x))
        out.append(rec)
    return pd.DataFrame(out)


def _replay_one(c, sl_mult: float, tp_mult: float) -> tuple[float, bool]:
    a, s = c.sb.a, c.s
    j1 = min(c.i_in0 + S.REPLAY_MAX_HOLD_MIN, a["close"].size)
    hi, lo = a["high"][c.i_in0:j1], a["low"][c.i_in0:j1]
    if not hi.size:
        return np.nan, False
    sl = c.entry - s * c.risk * sl_mult
    tp = c.entry + s * c.reward * tp_mult
    adj = 0.0 if s > 0 else c.spread
    hit_sl = (lo + adj <= sl) if s > 0 else (hi + adj >= sl)
    hit_tp = (hi + adj >= tp) if s > 0 else (lo + adj <= tp)
    ks, kt = np.flatnonzero(hit_sl), np.flatnonzero(hit_tp)
    k_sl = ks[0] if ks.size else np.inf
    k_tp = kt[0] if kt.size else np.inf
    if np.isinf(k_sl) and np.isinf(k_tp):
        return float(c.r(a["close"][j1 - 1])), False
    if k_sl <= k_tp:
        return -sl_mult, True
    return c.reward * tp_mult / c.risk, True


def geometry_whatif(t: pd.DataFrame, sbs: dict[str, SymbolBars]) -> dict:
    """Yönetimsiz saf geometri; önce (1,1) gerçek sonuçla kalibre edilir."""
    items = [(r, c) for r, c in _ctxs(t, sbs) if np.isfinite(c.reward)]
    if len(items) < S.REPLAY_MIN_CALIB:
        return {"durum": f"yetersiz (n={len(items)} < {S.REPLAY_MIN_CALIB})"}
    base = [_replay_one(c, 1.0, 1.0)[0] for _, c in items]
    agree = np.mean([(b > 0) == (r["outcome"] == WIN) for (r, _), b in zip(items, base) if np.isfinite(b)])
    rows = []
    period = np.array([r["period"] for r, _ in items])
    for slm in S.GEOMETRY_SL_MULTS:
        for tpm in S.GEOMETRY_TP_MULTS:
            res = np.array([_replay_one(c, slm, tpm)[0] for _, c in items])
            ok = np.isfinite(res)
            rows.append({"sl_x": slm, "tp_x": tpm, "n": int(ok.sum()), "wr": float((res[ok] > 0).mean()),
                         "top_r_ayni_lot": float(res[ok].sum()), "ort_r_ayni_risk": float((res[ok] / slm).mean()),
                         "kesif_ort_r": float((res[ok & (period == "disc")] / slm).mean()) if (ok & (period == "disc")).any() else np.nan,
                         "odak_ort_r": float((res[ok & (period == "focus")] / slm).mean()) if (ok & (period == "focus")).any() else np.nan})
    status = "güvenilir" if agree >= S.REPLAY_MIN_AGREE else "GÜVENİLMEZ (kalibrasyon düşük)"
    return {"durum": status, "uyum": float(agree), "n": len(items), "tablo": pd.DataFrame(rows)}
