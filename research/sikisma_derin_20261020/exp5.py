"""Sıkışma — beşinci tur: H1'in doğrudan sınaması P(Δ<0) + risk-sabit lot ağırlıklandırma + yön → results/rapor5.md

Ön-kayıt eki (exp4 sonrası):
- H1 (PROTOCOL.md) "sıkışık girişler daha kötü" doğrudan Δ = ortR(sıkışık) − ortR(diğer) < 0 ile sınanır:
  gün-blok bootstrap P(Δ<0) ve saat-eşli plasebo (aynı saatten aynı sayıda rastgele "sıkışık" etiketi).
- Yeni kullanım (algoritma): ortalama riski sabit tutan ağırlık w = 1 − α (sıkışık) / 1 + α·k (diğer), k = n_sıkışık /
  n_diğer (beklenen toplam lot aynı). α ∈ {0,5}. Kazanç = Σ w·R − Σ R. Ayrıca "yalnız küçült" (sıkışıkta ×0,5).
- Kümeler: dış birleşik (türetme penceresi hariç), GERİ, İLERİ; yön SELL/BUY ayrı (keşif notu: BUY'da sıkışık küme
  pozitif, engellemek zarar).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C
import exp4 as X4

OUT = C.HERE / "results"
ALPHA = 0.5


def stats(d: pd.DataFrame, lab: str, th: float = 1.0) -> dict:
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()].sort_values("t").reset_index(drop=True)
    R = d.R.to_numpy(float)
    sq = (d.atr_14_100 < th).to_numpy()
    days = C.day_ids(d.t)
    hours = pd.to_datetime(d.t, utc=True).dt.hour.to_numpy()
    k = sq.sum() / max(1, (~sq).sum())
    w = np.where(sq, 1 - ALPHA, 1 + ALPHA * k)
    gain = float((w * R).sum() - R.sum())
    ud, inv = np.unique(days, return_inverse=True)
    picks = C.RNG.integers(0, ud.size, (C.N_BOOT, ud.size))
    dl, gn = [], []
    for p in picks:
        idx = np.concatenate([np.flatnonzero(inv == j) for j in p])
        r, s = R[idx], sq[idx]
        if s.sum() >= 3 and (~s).sum() >= 3:
            dl.append(r[s].mean() - r[~s].mean())
            kk = s.sum() / (~s).sum()
            gn.append(((np.where(s, 1 - ALPHA, 1 + ALPHA * kk)) * r).sum() - r.sum())
    real = R[sq].mean() - R[~sq].mean()
    sims = []
    for _ in range(C.N_PLAC):
        lab_ = np.zeros_like(sq)
        for h in np.unique(hours[sq]):
            pool = np.flatnonzero(hours == h)
            lab_[C.RNG.choice(pool, int((sq & (hours == h)).sum()), replace=False)] = True
        sims.append(R[lab_].mean() - R[~lab_].mean())
    return {"küme": lab, "n": len(d), "sıkışık": int(sq.sum()), "ortR sıkışık": R[sq].mean(), "ortR diğer": R[~sq].mean(),
            "Δ": real, "P(Δ<0)": float(np.mean(np.array(dl) < 0)), "saat_plasebo(Δ)": float(np.mean(np.array(sims) > real)),
            "ağırlık kazancı R": gain, "P(kazanç>0)": float(np.mean(np.array(gn) > 0)),
            "yalnız küçült R": float(-0.5 * R[sq].sum())}


def main() -> None:
    b = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    nd = b[(b.sym == "NDX.INDX") & (~b.fam.isin(["DECIDER", "MANUEL"]))]
    der = (nd.t >= X4.DER_LO) & (nd.t < X4.DER_HI)
    oos, back, fwd = nd[~der], nd[nd.t < X4.DER_LO], nd[nd.t >= X4.DER_HI]
    rows = []
    for lab, d in (("dış birleşik", oos), ("GERİ", back), ("İLERİ", fwd), ("türetme penceresi", nd[der]),
                   ("dış · SELL", oos[oos.s < 0]), ("İLERİ · SELL", fwd[fwd.s < 0]),
                   ("dış · BUY", oos[oos.s > 0]), ("İLERİ · BUY", fwd[fwd.s > 0])):
        rows.append(stats(d, lab))
    rows.append(stats(fwd, "İLERİ (eşik 0,9)", 0.9))
    rows.append(stats(oos, "dış birleşik (eşik 0,9)", 0.9))
    for s, tag in (("GDAXI.INDX", "DAX"), ("USOIL.FOREX", "USOIL")):
        rows.append(stats(b[(b.sym == s) & ~b.fam.isin(["DECIDER", "MANUEL"])], f"bot {tag} (aktarım)"))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "h1_agirlik.csv", index=False)
    L = ["# Sıkışma — beşinci tur: H1 doğrudan + risk-sabit lot ağırlığı (exp5.py)",
         "\nΔ < 0 = sıkışık işlemler daha kötü (H1). `saat_plasebo(Δ)` = aynı saatlerden rastgele etiketin Δ'sinin gerçekten "
         "büyük olma oranı (≥%90 → saat etkisinden fazla). Ağırlık: sıkışıkta ×0,5, diğerlerinde ortalama riski koruyacak "
         "kadar büyük."]
    L.append(C.md(t))
    txt = "\n".join(L)
    (OUT / "rapor5.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
