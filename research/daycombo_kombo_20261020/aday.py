"""Aday 'SQZ<1 ∧ pre_dist_ema50_1h alt tertil' (dunku_isaret.py'de sonuçtan ÖNCE tanımlandı; 6 testten biri).
Yıl başına: gün-blok P(kurt>0), aynı yılda aynı sayıda rastgele DAYCOMBO engellemenin yüzdeliği (plasebo), saat-eşli
plasebo, çeyrekler; canlı DAYCOMBO ve REENTRY'de aynı kural (tertil eşiği 356 işlemden, sabit).
python3 research/daycombo_kombo_20261020/aday.py"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dk_run3", H / "run.py")
K = importlib.util.module_from_spec(spec); sys.modules["dk_run3"] = K; spec.loader.exec_module(K)
C = K.C
N = 4000


def card(d: pd.DataFrame, m: np.ndarray, lab: str) -> dict:
    d = d.reset_index(drop=True)
    R = d.R.to_numpy(float)
    rnd = np.array([-R[K.RNG.choice(R.size, m.sum(), replace=False)].sum() for _ in range(N)])
    real = -R[m].sum()
    qs = C.quarters(R, m)
    return {"küme": lab, "n": len(d), "engel": int(m.sum()), "ortR engel": R[m].mean() if m.any() else np.nan,
            "ortR kalan": R[~m].mean(), "kurt_R": real, "P(kurt>0)": C.boot_saved(R, m, C.day_ids(d.t)),
            "rastgele engel yüzdeliği": float((rnd < real).mean()),
            "saat_plasebo": C.hour_placebo(R, m, pd.to_datetime(d.t, utc=True).dt.hour.to_numpy()) if m.sum() >= 3 else np.nan,
            "çeyrekler": "/".join(f"{x:+.1f}" for x in qs)}


def main() -> None:
    d = pd.read_parquet(K.OUT / "daycombo_feats.parquet").sort_values("t").reset_index(drop=True)
    q = float(np.nanquantile(d.pre_dist_ema50_1h, 1 / 3))
    rule = lambda x: (x.atr_14_100 < 1).to_numpy() & (x.pre_dist_ema50_1h <= q).to_numpy()  # noqa: E731
    rows = [card(d[d.split == "keşif"], rule(d[d.split == "keşif"]), "DAYCOMBO 2025 (yeniden üretim)"),
            card(d[d.split == "sınama"], rule(d[d.split == "sınama"]), "DAYCOMBO 2026 (yeniden üretim)"),
            card(d, rule(d), "DAYCOMBO 2025+2026")]
    b = pd.read_parquet(C.ROOT / "research" / "sikisma_derin_20261020" / "results" / "ev_S1_bot.parquet")
    tr = pd.read_csv(C.ROOT / "output" / "islem_otopsi" / "2026-10-20_1429_all" / "islemler.csv")
    tr["t"] = pd.to_datetime(tr.entry_utc, utc=True)
    for fam in ("DAYCOMBO", "REENTRY"):
        x = tr[(tr.family == fam) & tr.outcome.isin(["TP", "SL", "BE"])][["t", "r_exit", "pre_dist_ema50_1h"]].rename(columns={"r_exit": "R"})
        x = pd.merge_asof(x.sort_values("t"), b[["t", "atr_14_100"]].sort_values("t"), on="t", direction="nearest",
                          tolerance=pd.Timedelta(seconds=5))
        x = x[np.isfinite(x.R) & x.atr_14_100.notna() & ((x.t < "2026-10-19") | (x.t >= "2026-10-20"))]  # 10-19 = hipotezin kaynağı, hariç
        rows.append(card(x, rule(x), f"canlı {fam} (07-30→10-20, 10-19 hariç)"))
    t = pd.DataFrame(rows)
    L = [f"# Aday SQZ<1 ∧ 1h EMA50 uzaklığı ≤ {q:.2f} ATR (alt tertil) — sınama", C.md(t)]
    txt = "\n".join(L)
    (K.OUT / "aday.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
