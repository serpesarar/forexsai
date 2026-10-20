"""Mum benzerlik motorunun geriye-dönük isabet karnesi → backend/data/candle_similarity_reliability.json.

Her sembol × TF × n (50, 100) için arşivin son %30'undan eşit aralıklı Q sorgu alınır. Her sorguda kütüphane
YALNIZ sorgu penceresinden önce ileri ufku bitmiş pencerelerdir (gelecek sızıntısı yok; servisle aynı match_core).
Ölçülen (orta ufuk H = HORIZONS[tf][1]):
  * yön isabeti: eşleşmelerin çoğunluk yönü (yukarı % ≠ 50) gerçekleşen H-bar getiri işaretini tuttu mu
  * tabanlar: yazı-tura %50; "hep kütüphane çoğunluğu" (sürüklenme); aynı sayıda RASTGELE komşunun çoğunluk yönü
  * güçlü uzlaşı alt kümesi (yukarı % ≥ 70 veya ≤ 30)
  * büyüklük: |medyan eşleşme getirisi| ve aynı-saat tipik hareketinin gerçekleşen |getiri| ile Spearman korelasyonu
Çalıştır (proje kökünden): python3 backend/scripts/candle_similarity_backtest.py
"""
from __future__ import annotations

import json
import zlib
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from services import candle_similarity_service as cs  # noqa: E402

N_LIST = (50, 100)
Q = 200
K = 20
TEST_FRAC = 0.30
STRONG = 70.0


def _spearman(a: np.ndarray, b: np.ndarray) -> float | None:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 20:
        return None
    return float(pd.Series(a[ok]).rank().corr(pd.Series(b[ok]).rank()))


def run_cell(arg: tuple[str, str, int]) -> tuple[str, dict]:
    sym, tf, n = arg
    s = cs.load_history(sym, tf)
    hs = cs.HORIZONS[tf]; H = hs[1]; hmax = max(hs)
    rng = np.random.default_rng(zlib.crc32(f"{sym}|{tf}|{n}".encode()))
    first = int(len(s.ts) * (1 - TEST_FRAC))
    ends = np.linspace(first, len(s.ts) - hmax - 1, Q).astype(int)
    rows = []
    for e in ends:
        q = cs._slice(s, e - n + 1, e + 1)
        if np.any(np.diff(q.ts) > cs.GAP_MAX_S):
            continue
        out = cs.match_core(s, q, tf, n, K, end_before_ts=int(q.ts[0]))
        if "error" in out:
            continue
        hz = out["horizons"][str(H)]
        real = s.c[e + H] / s.c[e] - 1
        ok = cs.valid_starts(s, n, hmax, int(q.ts[0]))
        cand = np.flatnonzero(ok)
        rnd = rng.choice(cand, size=min(K, len(cand)), replace=False) + n - 1
        rnd_up = 100 * float((s.c[rnd + H] / s.c[rnd] - 1 > 0).mean())
        rows.append({"up": hz["up_pct"], "base_up": hz["base_up_pct"], "med": hz["median_pct"],
                     "hour": hz.get("hour_median_abs_pct"), "rnd_up": rnd_up, "real": real, "top_sim_rms": float(out["dist"][0])})
    d = pd.DataFrame(rows)
    if d.empty:
        return f"{sym}|{tf}|{n}", {"n_queries": 0}
    dirn = np.sign(d.up.to_numpy() - 50); realdir = np.sign(d.real.to_numpy())
    strong = ((d.up >= STRONG) | (d.up <= 100 - STRONG)).to_numpy()

    def hit(pred: np.ndarray, mask: np.ndarray | None = None) -> float:
        m = (pred != 0) if mask is None else (pred != 0) & mask
        return float((pred[m] == realdir[m]).sum() / max(1, m.sum()))

    res = {"n_queries": int(len(d)), "horizon_bars": H, "test_from": cs._iso(int(s.ts[first])),
           "direction_hit_pct": 100 * hit(dirn),
           "random_neighbors_hit_pct": 100 * hit(np.sign(d.rnd_up.to_numpy() - 50)),
           "always_majority_hit_pct": 100 * hit(np.where(d.base_up.to_numpy() >= 50, 1.0, -1.0)),
           "strong_n": int(strong.sum()),
           "strong_hit_pct": 100 * hit(dirn, strong) if strong.sum() else None,
           "magnitude_corr_matches": _spearman(d.med.abs().to_numpy(), d.real.abs().to_numpy()),
           "magnitude_corr_hour_typical": _spearman(d.hour.to_numpy(float), d.real.abs().to_numpy()) if tf != "4h" else None}
    res["verdict"] = verdict(res)
    return f"{sym}|{tf}|{n}", res


def verdict(r: dict) -> str:
    """Kısa dürüst özet: eşleşme, rastgele komşu ve sürüklenme tabanını anlamlı aşıyor mu (binom, %95)."""
    n = r["n_queries"]
    edge = r["direction_hit_pct"] - max(r["random_neighbors_hit_pct"], r["always_majority_hit_pct"])
    se = 100 * 0.5 / np.sqrt(max(n, 1))
    if edge > 1.96 * se:
        return "tabanı aşıyor"
    if edge < -1.96 * se:
        return "tabanın altında"
    return "tabandan farksız"


def main() -> None:
    cells = [(sym, tf, n) for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX")
             for tf in cs.TIMEFRAMES for n in N_LIST
             if (cs.HISTORY_DIR / f"{sym.split('.')[0]}_{tf}.npz").exists()]
    with Pool(6) as p:
        out = dict(p.map(run_cell, cells))
    out["_meta"] = {"generated": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"), "queries_per_cell": Q,
                    "k": K, "test_frac": TEST_FRAC, "script": "backend/scripts/candle_similarity_backtest.py"}
    cs.RELIABILITY_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    df = pd.DataFrame({k: v for k, v in out.items() if not k.startswith("_")}).T
    pd.set_option("display.width", 250)
    print(df[["n_queries", "direction_hit_pct", "random_neighbors_hit_pct", "always_majority_hit_pct", "strong_n",
              "strong_hit_pct", "magnitude_corr_matches", "magnitude_corr_hour_typical", "verdict"]].to_string())


if __name__ == "__main__":
    main()
