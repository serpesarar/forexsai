"""ME-10 — "dalgalı tepe" yapısının kural tabanlı (yorumlanabilir özellik) tanımı: veri + özellik çekirdeği.

Bu modül SONUÇ (ileri getiri) hesaplamaz; yalnız sorgu anına kadar (≤ t) olan barlardan özellik üretir.
Kullanıcılar: 01_sablon_ozellikleri.py (şablon ölçümü), 02_kural_testi.py (ön-kayıtlı test).

Sorgu anı: NDX → her işlem günü 20:00 UTC'de başlayan 1h barın kapanışı (ME-08 ile aynı);
DAX → eksen-düzeltilmiş 1h dosyasında 19:00 UTC barı. Pencere = son W sorgu-günü: (Q[k−W], Q[k]] barları.
Tüm fiyatlar log; ölçek-bağımsızlık için mesafeler σ_ref (son 252 sorgu-günü, günlük getiri MAD-σ) biriminde.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/benzerlik_ornek_20261019"))
from merdiven_test import load as load_ndx_raw  # noqa: E402

DAX_FIXED = ROOT / "research/nasdaq_derin_20261013/caprev_dax_recheck/data_fixed/dax_1h.parquet"
REF_DAYS = 252        # σ_ref ve oynaklık oranı için geriye dönük sorgu-günü
REF_MIN = 126         # en az bu kadar geçmiş yoksa özellik NaN
ZZ = 1.0              # zigzag dönüş eşiği = ZZ × σ_ref (a priori, şablona bakılmadan)
HI_LONG, HI_SHORT = 60, 20


def load_ndx() -> pd.DataFrame:
    return load_ndx_raw()


def load_dax() -> pd.DataFrame:
    d = pd.read_parquet(DAX_FIXED)[["ts", "open", "high", "low", "close"]]
    return d[d.ts >= pd.Timestamp("2020-01-01", tz="UTC")].sort_values("ts").reset_index(drop=True)


def query_index(d: pd.DataFrame, hour: int) -> np.ndarray:
    """Her takvim gününde (UTC) verilen saatte başlayan bar; yoksa o gün sorgu yok."""
    return np.flatnonzero((d.ts.dt.hour == hour).to_numpy())


def zigzag_stats(p: np.ndarray, theta: float) -> tuple[int, int, float]:
    """Kapanış dizisi p (log) üzerinde θ dönüşlü zigzag.

    Dönüş: (≥θ salınım sayısı, alçalan-tepe sayısı, en derin geri çekilme / θ).
    Başlangıç noktası p[0] (pencerenin referans kapanışı). İlk pivot, ilk θ dönüşünden önceki uç değerdir.
    """
    if len(p) < 3 or not np.isfinite(theta) or theta <= 0:
        return 0, 0, np.nan
    piv: list[tuple[float, int]] = [(p[0], 0)]  # (fiyat, tip: 0 başlangıç, +1 tepe, −1 dip)
    trend = 0
    rmax = rmin = p[0]
    ext = p[0]
    for x in p[1:]:
        if trend == 0:
            rmax = max(rmax, x); rmin = min(rmin, x)
            if x <= rmax - theta:
                piv.append((rmax, +1)); trend = -1; ext = x
            elif x >= rmin + theta:
                piv.append((rmin, -1)); trend = +1; ext = x
        elif trend == +1:
            if x > ext:
                ext = x
            elif ext - x >= theta:
                piv.append((ext, +1)); trend = -1; ext = x
        else:
            if x < ext:
                ext = x
            elif x - ext >= theta:
                piv.append((ext, -1)); trend = +1; ext = x
    pts = [q for q, _ in piv] + ([ext] if trend != 0 else [])
    legs = np.abs(np.diff(pts))
    swings = int((legs >= theta - 1e-12).sum())
    peaks = [q for q, t in piv if t == +1]
    lh = int(sum(1 for a, b in zip(peaks[:-1], peaks[1:]) if b < a))
    # en derin geri çekilme: pencere içi zirveden sonraki en düşük kapanışa (tepe→dip) en büyük düşüş
    run_max = np.maximum.accumulate(p)
    dd = float((run_max - p).max())
    return swings, lh, dd / theta


def features(d: pd.DataFrame, Q: np.ndarray, W: int) -> pd.DataFrame:
    """Her sorgu k için (Q[k−W], Q[k]] penceresinin özellikleri. Yalnız ≤ Q[k] verisi kullanılır."""
    c = np.log(d.close.to_numpy()); hi = np.log(d.high.to_numpy()); lo = np.log(d.low.to_numpy())
    r1 = np.diff(c, prepend=np.nan)
    n = len(Q)
    dret = np.full(n, np.nan); dret[1:] = c[Q[1:]] - c[Q[:-1]]
    # σ_ref: son REF_DAYS günlük getirinin MAD-σ'sı (k dahil değil → katı geçmiş)
    s = pd.Series(np.abs(dret))
    sref = 1.4826 * s.shift(1).rolling(REF_DAYS, min_periods=REF_MIN).median().to_numpy()
    out = {k: np.full(n, np.nan) for k in (
        "net", "net_s", "eff", "rv", "pos", "rng_s", "dist60_s", "dist20_s", "dist60_pct", "dist20_pct",
        "dd60_s", "swings", "lh", "pull_s", "sref")}
    for k in range(max(W, HI_LONG), n):
        a, b = Q[k - W], Q[k]
        seg = slice(a + 1, b + 1)
        p = c[a:b + 1]
        rr = r1[seg]
        net = c[b] - c[a]
        path = np.nansum(np.abs(rr))
        H, L = hi[seg].max(), lo[seg].min()
        H60 = hi[Q[k - HI_LONG] + 1:b + 1].max(); H20 = hi[Q[k - HI_SHORT] + 1:b + 1].max()
        sr = sref[k]
        sw, lh, pull = zigzag_stats(p, ZZ * sr) if np.isfinite(sr) else (np.nan, np.nan, np.nan)
        out["net"][k] = net; out["net_s"][k] = net / sr
        out["eff"][k] = abs(net) / path if path > 0 else np.nan
        out["rv"][k] = np.nanstd(rr, ddof=1)
        out["pos"][k] = (c[b] - L) / (H - L) if H > L else np.nan
        out["rng_s"][k] = (H - L) / sr
        out["dist60_s"][k] = (H - H60) / sr; out["dist20_s"][k] = (H - H20) / sr
        out["dist60_pct"][k] = 100 * (np.exp(H - H60) - 1); out["dist20_pct"][k] = 100 * (np.exp(H - H20) - 1)
        out["dd60_s"][k] = (c[b] - H60) / sr
        out["swings"][k] = sw; out["lh"][k] = lh; out["pull_s"][k] = pull * ZZ if np.isfinite(pull) else np.nan
        out["sref"][k] = sr
    f = pd.DataFrame(out)
    rv = pd.Series(f.rv)
    f["rv_ratio"] = (rv / rv.shift(1).rolling(REF_DAYS, min_periods=REF_MIN).median()).to_numpy()
    f.insert(0, "qi", Q)
    f.insert(1, "ts", d.ts.iloc[Q].to_numpy())
    return f
