"""Adım 1 — kaynak envanteri ve saat ekseni denetimi.

Her dosya için: aralık, bar sayısı, ızgara dışı/duplike/OHLC ihlali; MT5 1m dosyaları
arasında ortak barlarda birebir eşitlik (saat çevrimi doğru mu); candle_cache ve Dukascopy
MT5 ile hangi gecikmede en iyi uyuşuyor.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import kaynak as K  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"


def basic(df: pd.DataFrame, tf_min: int) -> dict:
    t = df["t"].to_numpy()
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    return {
        "n": int(len(df)),
        "bas": str(pd.to_datetime(t.min(), unit="s")), "bit": str(pd.to_datetime(t.max(), unit="s")),
        "duplike": int(pd.Series(t).duplicated().sum()),
        "izgara_disi": int((t % (tf_min * 60) != 0).sum()),
        "ohlc_ihlal": int(((h < np.maximum(o, c)) | (l > np.minimum(o, c)) | (h < l)).sum()),
        "nan": int(df[["open", "high", "low", "close"]].isna().any(axis=1).sum()),
    }


def exact_overlap(a: pd.DataFrame, b: pd.DataFrame, tol: float = 1e-6) -> dict:
    m = a.merge(b, on="t", suffixes=("_a", "_b"))
    if m.empty:
        return {"ortak": 0}
    d = np.abs(m[[f"{k}_a" for k in "open high low close".split()]].to_numpy()
               - m[[f"{k}_b" for k in "open high low close".split()]].to_numpy())
    return {"ortak": int(len(m)), "birebir_%": round(100 * float((d.max(axis=1) <= tol).mean()), 3),
            "max_fark": round(float(d.max()), 3)}


def best_lag(a: pd.DataFrame, b: pd.DataFrame, lags=range(-180, 181, 30)) -> dict:
    """b'yi dakika kaydırarak a ile kapanış getirisi korelasyonu (saat ekseni denetimi)."""
    ra = a.set_index("t")["close"].pct_change()
    best = None
    for lag in lags:
        rb = b.assign(t=b["t"] + lag * 60).set_index("t")["close"].pct_change()
        j = pd.concat([ra, rb], axis=1, join="inner").dropna()
        if len(j) < 500:
            continue
        r = float(j.corr().iloc[0, 1])
        if best is None or r > best[1]:
            best = (lag, r, len(j))
    return {"en_iyi_gecikme_dk": best[0], "r": round(best[1], 4), "ortak": best[2]} if best else {}


def main() -> None:
    rep: dict = {"kaynaklar": {}, "mt5_1m_ciftleri": {}, "mt5_native_vs_1m": {}, "eksen": {}}
    duka = K.load_duka_1m()
    rep["kaynaklar"]["DUKA_1m"] = basic(duka, 1)

    m1 = {
        "c1_turev_M1": K.load_mt5_native("M1", K.MT5_DIR_A),
        "yon_lab_M1": K.load_mt5_native("M1", K.MT5_DIR_B),
        "tam_veri_1m_utc": K.load_mt5_utc_csv(K.MT5_UTC_CSV[0]),
        "islem_paketi_1m_utc": K.load_mt5_utc_csv(K.MT5_UTC_CSV[1]),
    }
    for k, v in m1.items():
        rep["kaynaklar"][k] = basic(v, 1)
    names = list(m1)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            rep["mt5_1m_ciftleri"][f"{names[i]}~{names[j]}"] = exact_overlap(m1[names[i]], m1[names[j]])

    for tf, mins in (("M5", 5), ("M15", 15), ("M30", 30), ("H1", 60)):
        rep["kaynaklar"][f"MT5_{tf}"] = basic(K.load_mt5_native(tf, K.MT5_DIR_A), mins)
    rep["kaynaklar"]["MT5_M5_yon_lab"] = basic(K.load_mt5_native("M5", K.MT5_DIR_B), 5)

    allm1 = pd.concat(m1.values()).drop_duplicates("t").sort_values("t")
    for i, p in enumerate(K.CANDLE_CACHE_1M):
        cc = K.load_candle_cache(p)
        rep["kaynaklar"][f"candle_cache_{i}"] = basic(cc, 1) | {"dosya": str(p.relative_to(K.ROOT))}
        rep["eksen"][f"candle_cache_{i}~MT5"] = best_lag(allm1, cc) | exact_overlap(allm1, cc, tol=0.051)
    rep["eksen"]["DUKA~MT5"] = best_lag(allm1, duka) | exact_overlap(allm1, duka, tol=3.0)

    OUT.mkdir(exist_ok=True)
    (OUT / "s01_envanter.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
