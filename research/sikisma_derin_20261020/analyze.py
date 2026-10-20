"""Sıkışma araştırması — tüm kaynak × algoritma × eşik değerlendirmesi + max-istatistik → results/rapor.md.

python3 research/sikisma_derin_20261020/analyze.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import core as C

OUT = C.HERE / "results"
FWD = pd.Timestamp("2026-08-28", tz="UTC")
MOMENTUM_FAMS = ("MOMSR", "DAYCOMBO", "REENTRY", "USOIL_BRK")


def qref_for(tag: str) -> dict:
    pl = pd.read_parquet(OUT / ("ev_S8_placebo.parquet" if tag == "NDX" else f"ev_S8_placebo_{tag}.parquet"))
    return {f: {q: float(pl[f].quantile(q)) for q in C.QUANT_TH} for f in C.QUANT_FEATS}


def sources() -> list[tuple[str, pd.DataFrame, str]]:
    b = pd.read_parquet(OUT / "ev_S1_bot.parquet")
    nd = b[(b.sym == "NDX.INDX") & (~b.fam.isin(["DECIDER", "MANUEL"]))]
    out = [("S1 bot NDX tümü", nd, "NDX"),
           ("S1-F bot NDX İLERİ (08-28→)", nd[nd.t >= FWD], "NDX"),
           ("S1-P bot NDX 08-28 öncesi", nd[nd.t < FWD], "NDX"),
           ("S1 bot NDX momentum aileleri", nd[nd.fam.isin(MOMENTUM_FAMS)], "NDX"),
           ("S1 bot NDX VIXREG", nd[nd.fam == "VIXREG"], "NDX"),
           ("S1 bot NDX CHREV", nd[nd.fam == "CHREV"], "NDX")]
    for s, tag in (("GDAXI.INDX", "GDAXI"), ("USOIL.FOREX", "USOIL")):
        out.append((f"S1 bot {tag}", b[(b.sym == s) & (~b.fam.isin(["DECIDER", "MANUEL"]))], tag))
    for f, lab, tag in (("ev_S2_skipped", "S2 engellenen NDX SELL", "NDX"), ("ev_S3_panel", "S3 panel NDX", "NDX"),
                        ("ev_S4_decider", "S4 decider NDX", "NDX"), ("ev_S5_daycombo", "S5 DAYCOMBO 2025-26", "NDX"),
                        ("ev_S6M_ndx", "S6M NDX kırılım-devam", "NDX"), ("ev_S6R_ndx", "S6R NDX kırılım-dönüş", "NDX"),
                        ("ev_S8_placebo", "S8 NDX plasebo (rastgele yön)", "NDX")):
        out.append((lab, pd.read_parquet(OUT / f"{f}.parquet"), tag))
    for tag in ("GDAXI", "USOIL", "XAUUSD"):
        for k, lab in (("M", "kırılım-devam"), ("R", "kırılım-dönüş")):
            out.append((f"S7{k} {tag} {lab}", pd.read_parquet(OUT / f"ev_S7{k}_{tag}.parquet"), tag))
        out.append((f"S8 {tag} plasebo", pd.read_parquet(OUT / f"ev_S8_placebo_{tag}.parquet"), tag))
    return out


def headline(tab: pd.DataFrame, rule: str) -> pd.DataFrame:
    t = tab[tab.kural == rule].copy()
    return t[["kaynak", "n", "engel", "ortR_engel", "ortR_kalan", "kurt_R", "P(kurt>0)", "saat_plasebo", "Ç+", "çeyrekler"]]


def main() -> None:
    allt = []
    ms = {}
    for lab, d, tag in sources():
        q = qref_for(tag)
        big = len(d) > 3000
        t = C.evaluate(d, q, lab, full=True) if not big else C.evaluate(d, q, lab, full=True)
        allt.append(t)
        if lab.startswith(("S1 bot NDX tümü", "S1-F")):
            ms[lab] = C.max_stat(d, q)
        print(f"{lab}: {len(d)} olay, {len(t)} kural", flush=True)
    tab = pd.concat(allt, ignore_index=True)
    tab.to_csv(OUT / "tum_kurallar.csv", index=False)

    L = ["# Sıkışma (SQZ) derin sınama — sonuçlar (ön-kayıt PROTOCOL.md)",
         "\n`kurt_R` = engellenen olayların −ΣR (pozitif = engel kazandırırdı). `P(kurt>0)` gün-blok bootstrap. "
         "`saat_plasebo` = aynı UTC saatinden aynı sayıda rastgele engelden daha iyi olma oranı. `Ç+` = 4 kronolojik "
         "çeyrekten kaçında kurt_R ≥ 0."]
    L.append("\n## 1. Botun kendi kuralı (atr_14_100 < 1,00) — tüm kaynaklarda")
    L.append(C.md(headline(tab, "atr_14_100<1")))
    L.append("\n## 2. Gün-içi mevsimsellikten arındırılmış sürüm (atr14_seas < 1,00)")
    L.append(C.md(headline(tab, "atr14_seas<1")))
    L.append("\n## 3. Seçim düzeltmesi (S1, 31 kural içinde en iyisi; dairesel kaydırma ×1000)")
    for lab, (obs, null) in ms.items():
        L.append(f"- {lab}: en iyi kural kurt_R {obs:+.2f} · boş medyan {np.median(null):+.2f}, %90 {np.quantile(null, .9):+.2f} "
                 f"→ p(seçim) = {(null >= obs).mean():.3f}")
    L.append("\n## 4. S1-F İLERİ dönem — bütün kurallar (kurt_R'ye göre)")
    f = tab[tab.kaynak.str.startswith("S1-F")].sort_values("kurt_R", ascending=False)
    L.append(C.md(f[["kural", "engel", "ortR_engel", "ortR_kalan", "kurt_R", "P(kurt>0)", "saat_plasebo", "Ç+", "çeyrekler"]]))
    L.append("\n## 5. Kural başına kaynaklar arası tutarlılık (kurt_R işareti; + sayısı / kaynak sayısı)")
    piv = tab.pivot_table(index="kural", columns="kaynak", values="kurt_R")
    cons = pd.DataFrame({"kural": piv.index, "+kaynak": (piv > 0).sum(axis=1).to_numpy(),
                         "kaynak": piv.notna().sum(axis=1).to_numpy(),
                         "P≥%95 ve +": [int(((tab.kural == k) & (tab.kurt_R > 0) & (tab["P(kurt>0)"] >= 0.95)).sum())
                                        for k in piv.index]})
    L.append(C.md(cons.sort_values("+kaynak", ascending=False), "{:.0f}"))
    txt = "\n".join(L)
    (OUT / "rapor.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
