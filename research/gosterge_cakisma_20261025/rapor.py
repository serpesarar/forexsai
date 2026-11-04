"""summarize.py çıktılarından SONUCLAR.md tablolarını üret (anlatı RAPOR.md'de elle yazılır)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import config as C

TF_ORDER = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]


def _heat(g: pd.DataFrame, sym: str) -> list[str]:
    s = g[g.sym == sym]
    tfs = [t for t in TF_ORDER if t in set(s.tf)]
    L = [f"| TF \\ h | " + " | ".join(str(h) for h in C.HORIZONS) + " |", "|---|" + "---|" * len(C.HORIZONS)]
    for tf in tfs:
        cells = []
        for h in C.HORIZONS:
            r = s[(s.tf == tf) & (s.h == h)]
            if r.empty:
                cells.append("–")
                continue
            r = r.iloc[0]
            cells.append(f"**{int(r.kanitli)}** · D {int(r.dogr)}/{int(r.dogr_ters)} · K {int(r.kasa)}/{int(r.kasa_ters)} · ε {r.esik}")
        L.append(f"| {tf} | " + " | ".join(cells) + " |")
    return L


def _model(m: pd.DataFrame, sym: str) -> list[str]:
    s = m[(m.sym == sym)]
    if "olculemez" in s:
        s = s[s.olculemez != True]  # noqa: E712
    L = ["| TF | h | AUC kasa | AUC taban | fark | en emin %10 isabet | taban | fark | bağımsız n | z |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tf in [t for t in TF_ORDER if t in set(s.tf)]:
        for _, r in s[s.tf == tf].sort_values("h").iterrows():
            n = max(r.top10_n_indep, 1)
            z = (r.top10_hit - r.top10_base) / np.sqrt(max(r.top10_base * (1 - r.top10_base), 1e-9) / n)
            L.append(f"| {tf} | {int(r.h)} | {r.auc_test:.3f} | {r.auc_test_base:.3f} | {r.auc_lift:+.3f} | "
                     f"{r.top10_hit:.3f} | {r.top10_base:.3f} | {r.top10_lift:+.3f} | {int(r.top10_n_indep)} | {z:+.2f} |")
    return L


def _replication(rep: pd.DataFrame, cells: pd.DataFrame) -> list[str]:
    if rep.empty:
        return ["Doğrulamayı geçen kombinasyon yok."]
    key = ["src_sym", "src_tf", "src_h", "combo", "dir"]
    nmin = rep.tf.map(C.N_MIN) / 4                       # EK-4: ön kayıttaki asgari n
    other = rep[~rep.same_cell & (rep.DOGRULAMA_n >= nmin) & (rep.KASA_n >= nmin) & (rep.KESIF_n >= nmin)]
    agg = other.groupby(key).agg(hucre=("tf", "size"),
                                 kasa_ayni_yon=("KASA_z", lambda z: int((z >= C.Z_PASS).sum())),
                                 kasa_ters=("KASA_z", lambda z: int((z <= -C.Z_PASS).sum())),
                                 tum_ayni=("KESIF_z", "size")).reset_index()
    full = other.assign(tum_z=(other.KESIF_z + other.DOGRULAMA_z + other.KASA_z) / np.sqrt(3))
    agg["tum_donem_ayni_yon"] = full.groupby(key).tum_z.apply(lambda z: int((z >= C.Z_PASS).sum())).values
    agg["tum_donem_ters"] = full.groupby(key).tum_z.apply(lambda z: int((z <= -C.Z_PASS).sum())).values
    kan = cells[cells.kanitli][["sym", "tf", "h", "combo"]].rename(columns={"sym": "src_sym", "tf": "src_tf", "h": "src_h"})
    kan["kanitli"] = True
    agg = agg.merge(kan, on=["src_sym", "src_tf", "src_h", "combo"], how="left").fillna({"kanitli": False})
    tot = dict(aday=len(agg), hucre=int(agg.hucre.sum()), kasa_ayni=int(agg.kasa_ayni_yon.sum()), kasa_ters=int(agg.kasa_ters.sum()),
               tum_ayni=int(agg.tum_donem_ayni_yon.sum()), tum_ters=int(agg.tum_donem_ters.sum()))
    L = [f"Doğrulamayı geçen **{tot['aday']}** kombinasyon, kaynak hücreleri dışındaki **{tot['hucre']}** (sembol, TF, h) "
         f"hücresinde aynı tanım ve aynı yönle yeniden ölçüldü (her bölmede n ≥ n_min/4 olan hücreler).",
         f"- KASA bölmesinde aynı yönde anlamlı (z ≥ 1,645): **{tot['kasa_ayni']}**, ters yönde anlamlı: **{tot['kasa_ters']}** "
         f"(boş beklenti her biri ≈ %5 → ≈ {tot['hucre'] * 0.05:.0f}).",
         f"- Tüm dönem (üç bölme birleşik z) aynı yönde anlamlı: **{tot['tum_ayni']}**, ters: **{tot['tum_ters']}**.", "",
         "En çok tekrarlayan 15 aday (KASA'da aynı yön anlamlı hücre sayısına göre):", "",
         "| Kaynak | Kombinasyon | Yön | Kanıtlı | Hücre | KASA aynı / ters | Tüm dönem aynı / ters |", "|---|---|---|---|---:|---:|---:|"]
    for _, r in agg.sort_values(["kasa_ayni_yon", "tum_donem_ayni_yon"], ascending=False).head(15).iterrows():
        L.append(f"| {r.src_sym} {r.src_tf} h={r.src_h} | `{r.combo}` | {r.dir} | {'evet' if r.kanitli else ''} | {r.hucre} | "
                 f"{r.kasa_ayni_yon} / {r.kasa_ters} | {r.tum_donem_ayni_yon} / {r.tum_donem_ters} |")
    return L, tot


def main() -> None:
    g = pd.read_csv(C.RES / "hucre_tablosu.csv")
    cells = []
    for sym in C.SOURCES:
        for tf in C.SOURCES[sym]:
            p = C.RES / sym / tf / "cells.csv"
            if p.exists():
                cells.append(pd.read_csv(p).assign(sym=sym, tf=tf))
    cells = pd.concat(cells, ignore_index=True)
    m = pd.read_csv(C.RES / "model_tablosu.csv")
    hk = json.load(open(C.RES / "hukum.json"))
    cov = json.load(open(C.RES / "coverage.json"))
    rep_p = C.RES / "tekrarlanma.csv.gz"
    rep = pd.read_csv(rep_p) if rep_p.exists() else pd.DataFrame()
    title = "ana kütüphane" if C.LIB == "main" else "parametre varyantı kütüphanesi (EK-6)"
    L = [f"# GÇM — sonuç tabloları (otomatik, {title})", "",
         f"Kapsama: {cov['indicators']} gösterge, {cov['states']} durum, {cov['n_families']} aile → "
         f"topluluk scriptlerinin %{cov['share_scripts'] * 100:.1f}'i (boost ağırlıklı %{cov['share_boost'] * 100:.1f}).", "",
         "## Sistem düzeyi hüküm", "", "| Sembol | Seçilen | Kanıtlı | Boş beklenti (q99) | Doğr. geçen / ters | Kasa geçen / ters | Keşifte seçimden sağ |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for k, v in hk.items():
        L.append(f"| {k} | {v['secilen']} | **{v['kanitli']}** | {v['bos_beklenti']} ({v['bos_q99']}) | {v['dogr_gecen']} / {v['dogr_ters']} | "
                 f"{v['kasa_gecen']} / {v['kasa_ters']} | {v['kesif_secimden_sag']} |")
    L += ["", "Hücre biçimi: **kanıtlı** · D doğrulama geçen/ters-anlamlı · K kasa geçen/ters-anlamlı · ε seçim eşiği (plasebo max|z| %95). "
          "Her hücrede 30 kombinasyon seçildi; tesadüfen her birinin geçmesi ≈ %5.", ""]
    for sym in [s for s in C.SOURCES if s in set(g.sym)]:
        L += [f"## {sym}", "", "### Kombinasyon madenciliği", ""] + _heat(g, sym) + ["", "### Tüm-gösterge modeli (KASA)", ""] + _model(m, sym) + [""]
    L += ["## Tekrarlanma (tüm TF × sembol)", ""]
    if not rep.empty:
        cov_cells = rep.groupby(["sym", "tf"]).h.nunique()
        L += ["Tekrarlanma ölçümünün kapsadığı (sembol, TF) hücreleri (ufuk sayısı): " +
              ", ".join(f"{s} {t} ({n})" for (s, t), n in cov_cells.items()), ""]
    out = _replication(rep, cells)
    L += out[0] if isinstance(out, tuple) else out
    if isinstance(out, tuple):
        json.dump(out[1], open(C.RES / "tekrarlanma_ozet.json", "w"), indent=1)
    kan = cells[cells.kanitli]
    L += ["", f"## Kanıtlı adaylar ({len(kan)})", ""]
    if len(kan):
        L += ["| Sembol | TF | h | Kombinasyon | Yön | Keşif z | Doğr. z | Kasa z | Kasa isabet / taban | Kasa getiri bp / maliyet |",
              "|---|---|---:|---|---|---:|---:|---:|---|---|"]
        for _, r in kan.iterrows():
            L.append(f"| {r.sym} | {r.tf} | {r.h} | `{r.combo}` | {r.dir} | {r.KESIF_z:.2f} | {r.DOGRULAMA_z:.2f} | {r.KASA_z:.2f} | "
                     f"{r.KASA_hit:.3f} / {r.KASA_base:.3f} (n {int(r.KASA_n)}) | {r.KASA_ret_bp:.1f} / {r.KASA_cost_bp:.1f} |")
    (C.HERE / ("SONUCLAR.md" if C.LIB == "main" else "SONUCLAR_V.md")).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("SONUCLAR.md yazıldı")


if __name__ == "__main__":
    main()
