"""Sıkışma — dördüncü tur: bot üzerinde EN ADİL test + pratik varyantlar → results/rapor4.md

Ön-kayıt eki (exp3 sonrası; sonuçlara bakmadan):
- Kural dış AI raporunda 2026-08-13 → 08-27 penceresinden (28 işlem) türetildi, eşik 1,00 orada seçildi.
  O pencere DIŞARIDA bırakılınca kalan iki dönem gerçek dış örneklemdir: GERİ (06-29 → 08-12; 08-28 denetimi bunu
  zaten görmüştü) ve İLERİ (08-28 → bugün; hiç görülmedi). Birincil = GERİ+İLERİ birleşik, eşik 1,00, aile kısıtı yok.
- Geçme (B14'ü canlı kart adayına yükseltmek için): birleşik dış örneklemde gün-blok P(kurt>0) ≥ %90, saat-eşli
  plasebo ≥ %90, aylar ≥ 3/4 Δ<0, İLERİ'de Δ<0. Ayrıca güç hesabı: İLERİ etkisiyle P≥%90 için gereken n.
- Pratik varyantlar (rapor amaçlı, seçim değil): eşik 0,9; yalnız VIXREG; engel yerine lot ×0,5; R ve gerçek $.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C

OUT = C.HERE / "results"
DER_LO, DER_HI = pd.Timestamp("2026-08-13", tz="UTC"), pd.Timestamp("2026-08-28", tz="UTC")
POWER_TARGET = 0.90


def evalb(d: pd.DataFrame, th: float, lab: str) -> dict:
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()].sort_values("t").reset_index(drop=True)
    R = d.R.to_numpy(float)
    blk = (d.atr_14_100 < th).to_numpy()
    mon = pd.to_datetime(d.t, utc=True).dt.strftime("%m").to_numpy()
    mneg = sum(1 for m in np.unique(mon) if (blk & (mon == m)).sum() >= 3 and (~blk & (mon == m)).sum() >= 3
               and R[blk & (mon == m)].mean() < R[~blk & (mon == m)].mean())
    mtot = sum(1 for m in np.unique(mon) if (blk & (mon == m)).sum() >= 3 and (~blk & (mon == m)).sum() >= 3)
    net = d.net.to_numpy(float)
    return {"küme": lab, "eşik": th, "n": len(d), "engel": int(blk.sum()), "ortR_engel": R[blk].mean(),
            "ortR_kalan": R[~blk].mean(), "Δ": R[blk].mean() - R[~blk].mean(), "kurt_R": -R[blk].sum(),
            "kurt_$": -net[blk].sum(), "yarım lot kurt_R": -0.5 * R[blk].sum(),
            "P(kurt>0)": C.boot_saved(R, blk, C.day_ids(d.t)),
            "saat_plasebo": C.hour_placebo(R, blk, pd.to_datetime(d.t, utc=True).dt.hour.to_numpy()),
            "ay Δ<0": f"{mneg}/{mtot}"}


def power(d: pd.DataFrame, th: float, n_target: tuple = (100, 150, 200, 300, 400)) -> list[str]:
    """İLERİ dönemin etkisi gerçekse, aynı dağılımdan n işlemle P(kurt>0) ≥ %90 olasılığı (yeniden örnekleme)."""
    d = d[np.isfinite(d.R) & d.atr_14_100.notna()]
    R, blk = d.R.to_numpy(float), (d.atr_14_100 < th).to_numpy()
    out = []
    for n in n_target:
        hits = 0
        for _ in range(400):
            i = C.RNG.integers(0, R.size, n)
            r, b = R[i], blk[i]
            s = np.array([-r[j][b[j]].sum() for j in C.RNG.integers(0, n, (300, n))])
            hits += (s > 0).mean() >= POWER_TARGET
        out.append(f"n={n}: %{100 * hits / 400:.0f}")
    return out


def main() -> None:
    b = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    nd = b[(b.sym == "NDX.INDX") & (~b.fam.isin(["DECIDER", "MANUEL"]))].copy()
    der = (nd.t >= DER_LO) & (nd.t < DER_HI)
    back, fwd = nd[nd.t < DER_LO], nd[nd.t >= DER_HI]
    oos = nd[~der]
    L = ["# Sıkışma — dördüncü tur: bot dış-örneklem testi (exp4.py; ön-kayıt eki dosya başında)",
         f"\nTüretme penceresi 08-13 → 08-27 dışarıda: {int(der.sum())} işlem. GERİ {len(back)}, İLERİ {len(fwd)}."]
    rows = []
    for lab, d in (("BİRLEŞİK dış (GERİ+İLERİ)", oos), ("GERİ 06-29→08-12", back), ("İLERİ 08-28→", fwd),
                   ("tüketim penceresi 08-13→08-27", nd[der])):
        for th in (1.0, 0.9):
            rows.append(evalb(d, th, lab))
    for lab, d in (("BİRLEŞİK dış · VIXREG", oos[oos.fam == "VIXREG"]), ("İLERİ · VIXREG", fwd[fwd.fam == "VIXREG"]),
                   ("BİRLEŞİK dış · VIXREG dışı", oos[oos.fam != "VIXREG"]), ("İLERİ · VIXREG dışı", fwd[fwd.fam != "VIXREG"]),
                   ("BİRLEŞİK dış · SELL", oos[oos.s < 0]), ("BİRLEŞİK dış · BUY", oos[oos.s > 0])):
        rows.append(evalb(d, 1.0, lab))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "bot_dis_orneklem.csv", index=False)
    L.append(C.md(t))
    L.append("\n## Güç: İLERİ dönemin etkisi (eşik 1,00) gerçekse kaç işlemle P(kurt>0) ≥ %90 yakalanır?")
    L.append("- " + " · ".join(power(fwd, 1.0)))
    L.append("- eşik 0,9: " + " · ".join(power(fwd, 0.9)))
    rate = len(fwd) / max(1, (fwd.t.max() - fwd.t.min()).days) * 7
    L.append(f"- İLERİ dönemde haftada ≈{rate:.1f} NDX bot işlemi")
    txt = "\n".join(L)
    (OUT / "rapor4.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
