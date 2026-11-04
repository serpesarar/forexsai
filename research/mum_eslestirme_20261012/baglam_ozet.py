"""ME-03 özeti — PROTOCOL_BAGLAM.md'deki kıyaslar.

B1: şekil + bağlam  ↔  yalnız bağlam (aynı bağlamın koşullu tabanı)       — "bağlama şekil ekleyince kazanç var mı?"
B2: yalnız bağlam   ↔  koşulsuz taban                                       — "bağlamın kendisi bilgi taşıyor mu?"
B3: iki sembolün ortak şekli ↔ hedefin kendi şekli / ortağın şekli / taban
Başarı: hücre (sembol × TF × ufuk × temsil × bağlam/çift) başına eşli fark, gün-blok bootstrap (blok ≥ ufuk, B=1000)
P ≥ 0,975 ve iki kronolojik yarı > 0. Genel karar: başarılı hücre sayısı %2,5 tesadüf beklentisini binom p < 0,01 ile
aşmalı ve ≥ 2 sembolde görülmeli.
Çalıştır: python3 research/mum_eslestirme_20261012/baglam_ozet.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from _common import HERE

RES = HERE / "results"
TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
TF_ORDER = ["5m", "15m", "30m", "1h", "4h", "1d"]
B = 1000
rng = np.random.default_rng(7)


def boot(diff: np.ndarray, blk: np.ndarray, t: np.ndarray):
    ok = np.isfinite(diff); diff, blk, t = diff[ok], blk[ok], t[ok]
    if len(diff) < 30:
        return np.nan, np.nan, np.nan, np.nan
    u, inv = np.unique(blk, return_inverse=True)
    S = np.bincount(inv, diff); N = np.bincount(inv)
    idx = rng.integers(0, len(u), size=(B, len(u)))
    bm = S[idx].sum(1) / N[idx].sum(1)
    half = t >= np.median(t)
    return float(diff.mean()), float((bm > 0).mean()), float(diff[~half].mean()), float(diff[half].mean())


def basics(d: pd.DataFrame) -> pd.DataFrame:
    d = d[np.isfinite(d.y) & (d.y != 0)].copy()
    up = d.y > 0
    has = d.n > 0
    d["call"] = np.where(has, np.sign(d.pu - 0.5), 0.0)
    d["corr"] = np.where(d.call != 0, ((d.call > 0) == up).astype(float), np.nan)
    d["bcorr"] = np.where(np.isfinite(d.p0) & (d.p0 != 0.5), ((d.p0 > 0.5) == up).astype(float), np.nan)
    d["ae"] = np.where(has, np.abs(d.med - d.absr), np.nan)
    d["ae_h"] = np.abs(d.bmed_h - d.absr)
    dec = d.race.isin([1, -1])
    d["rcorr"] = np.where(dec & np.isfinite(d.prace) & (d.prace != 0.5) & has, ((d.prace > 0.5) == (d.race == 1)).astype(float), np.nan)
    d["day"] = (d.ts // 86_400_000_000_000).astype(np.int64)
    d["blk"] = d.day // np.maximum(1, np.ceil(d.H * d.tf.map(TF_MIN) / 1440)).astype(np.int64)
    return d


def verdict(cells: pd.DataFrame, col_p: str, col_y1: str, col_y2: str, group: list) -> pd.DataFrame:
    rows = []
    for key, g in cells.groupby(group):
        g = g[np.isfinite(g[col_p])]
        if g.empty:
            continue
        succ = (g[col_p] >= 0.975) & (g[col_y1] > 0) & (g[col_y2] > 0)
        worse = (g[col_p] <= 0.025) & (g[col_y1] < 0) & (g[col_y2] < 0)
        k, n = int(succ.sum()), len(g)
        p = binomtest(k, n, 0.025, alternative="greater").pvalue if n else np.nan
        syms = sorted(set(g.loc[succ, "sym"])) if k else []
        rows.append(dict(zip(group, key if isinstance(key, tuple) else (key,))) |
                     {"hücre": n, "başarılı": k, "tutarlı_kötü": int(worse.sum()), "binom_p": p,
                      "başarılı_semboller": ",".join(syms), "KARAR": "KATKI VAR" if (p < 0.01 and len(syms) >= 2) else "yok"})
    return pd.DataFrame(rows)


# ─────────────────────────── bağlam ───────────────────────────
def ctx_analysis() -> None:
    d = basics(pd.concat([pd.read_parquet(p) for p in sorted((RES / "baglam").glob("*.parquet"))], ignore_index=True))
    up = d.y > 0
    d["ccorr"] = np.where(np.isfinite(d.p0c) & (d.p0c != 0.5), ((d.p0c > 0.5) == up).astype(float), np.nan)
    d["ae_c"] = np.abs(d.bmedc - d.absr)
    d["rccorr"] = np.where(np.isfinite(d.rcorr) & np.isfinite(d.prace0c), ((d.prace0c > 0.5) == (d.race == 1)).astype(float), np.nan)
    yb = up.astype(float)
    d["br0"] = (d.p0 - yb) ** 2; d["br_c"] = (d.p0c.fillna(d.p0) - yb) ** 2
    d["br_m"] = (np.where(d.n > 0, d.pu, d.p0c.fillna(d.p0)) - yb) ** 2
    called = d.call != 0
    # havuz özeti
    s = d.groupby(["rep", "ctx"]).apply(lambda g: pd.Series({
        "sorgu": len(g), "tahmin_%": 100 * (g.n > 0).mean(),
        "model_yön_%": 100 * g["corr"][g.call != 0].mean(),
        "bağlam_taban_%": 100 * g.ccorr[g.call != 0].mean(),
        "koşulsuz_taban_%": 100 * g.bcorr[g.call != 0].mean(),
        "plasebo_%": 100 * g.plc_acc[g.call != 0].mean(),
        "B1_yön_fark_puan": 100 * (g["corr"] - g.ccorr)[g.call != 0].mean(),
        "B2_bağlam_bilgisi_puan": 100 * (g.ccorr - g.bcorr).mean(),
        "büyüklük_vs_bağlam_%": 100 * (1 - g.ae.sum() / g.ae_c[g.n > 0].sum()),
        "büyüklük_vs_saat_%": 100 * (1 - g.ae.sum() / g.ae_h[g.n > 0].sum()),
        "hedef_model_%": 100 * g.rcorr.mean(), "hedef_bağlam_%": 100 * g.rccorr.mean(),
        # ön-kayıt DIŞI, bilgi amaçlı: olasılık kalibrasyonu (Brier). Çoğunluk yönünü değiştirmeyen bağlam bilgisini görür.
        "Brier_B2_bağlam_vs_koşulsuz_%": 100 * (1 - g.br_c.sum() / g.br0.sum()),
        "Brier_B1_model_vs_bağlam_%": 100 * (1 - g.br_m.sum() / g.br_c.sum())}), include_groups=False).reset_index()
    s.to_csv(RES / "baglam_ozet_havuz.csv", index=False)
    print("=== BAĞLAM — tüm havuz ===")
    print(s.round(2).to_string(index=False))
    # sembol × bağlam (P33)
    t = d[d.rep == "P33"].groupby(["sym", "ctx"]).apply(lambda g: pd.Series({
        "model_%": 100 * g["corr"][g.call != 0].mean(), "bağlam_taban_%": 100 * g.ccorr[g.call != 0].mean(),
        "koşulsuz_%": 100 * g.bcorr[g.call != 0].mean(), "B1_puan": 100 * (g["corr"] - g.ccorr)[g.call != 0].mean(),
        "B2_puan": 100 * (g.ccorr - g.bcorr).mean(),
        "Brier_B2_%": 100 * (1 - g.br_c.sum() / g.br0.sum()), "Brier_B1_%": 100 * (1 - g.br_m.sum() / g.br_c.sum())}),
        include_groups=False).reset_index()
    print("\n=== SEMBOL × BAĞLAM (P33) ==="); print(t.round(2).to_string(index=False))
    # VIX / CAPREV hücreleri ayrıntı
    x = d[(d.rep == "P33") & d.ctx.isin(["vix", "vix_stres"]) & d.sym.isin(["NDX", "DAX"])]
    lab = {("vix", 0): "VIX<18,4", ("vix", 1): "VIX≥18,4", ("vix_stres", 0): "sakin", ("vix_stres", 1): "stres∧VIX düşük",
           ("vix_stres", 2): "VIX yüksek, stres yok", ("vix_stres", 3): "stres∧VIX yüksek (CAPREV)"}
    rows = []
    for (sym, tf, ctx, cv), g in x.groupby(["sym", "tf", "ctx", "cval"]):
        if tf not in ("1h", "4h", "1d"):
            continue
        rows.append({"sym": sym, "tf": tf, "hücre": lab.get((ctx, cv), cv), "sorgu": len(g), "gerçek_yukarı_%": 100 * (g.y > 0).mean(),
                     "bağlam_taban_%": 100 * g.ccorr.mean(), "model_%": 100 * g["corr"][g.call != 0].mean(),
                     "koşulsuz_%": 100 * g.bcorr.mean()})
    print("\n=== NDX/DAX VIX ve STRES HÜCRELERİ (P33, 1h/4h/1d, tüm ufuklar) ===")
    print(pd.DataFrame(rows).round(1).to_string(index=False))
    # hücre testleri
    cells = []
    for (sym, tf, H, rep, ctx), g in d.groupby(["sym", "tf", "H", "rep", "ctx"], sort=False):
        c = g[g.call != 0]
        b1 = boot((c["corr"] - c.ccorr).to_numpy(), c.blk.to_numpy(), c.ts.to_numpy())
        m = g[g.n > 0]
        b1m = boot((m.ae_c - m.ae).to_numpy(), m.blk.to_numpy(), m.ts.to_numpy())
        b2 = boot((g.ccorr - g.bcorr).to_numpy(), g.blk.to_numpy(), g.ts.to_numpy())
        cells.append({"sym": sym, "tf": tf, "H": H, "rep": rep, "ctx": ctx,
                      "B1_fark": b1[0], "B1_P": b1[1], "B1_y1": b1[2], "B1_y2": b1[3],
                      "B1m_fark": b1m[0], "B1m_P": b1m[1], "B1m_y1": b1m[2], "B1m_y2": b1m[3],
                      "B2_fark": b2[0], "B2_P": b2[1], "B2_y1": b2[2], "B2_y2": b2[3]})
    cells = pd.DataFrame(cells); cells.to_csv(RES / "baglam_hucre_testleri.csv", index=False)
    print("\n=== B1 YÖN: şekil+bağlam > yalnız bağlam ===")
    v1 = verdict(cells, "B1_P", "B1_y1", "B1_y2", ["ctx", "rep"]); print(v1.to_string(index=False))
    print("\n=== B1 BÜYÜKLÜK: şekil+bağlam > bağlamın medyan hareketi ===")
    v1m = verdict(cells, "B1m_P", "B1m_y1", "B1m_y2", ["ctx", "rep"]); print(v1m.to_string(index=False))
    print("\n=== B2: yalnız bağlam > koşulsuz taban (bağlamın kendi bilgisi) ===")
    v2 = verdict(cells[cells.rep == "P33"], "B2_P", "B2_y1", "B2_y2", ["ctx"]); print(v2.to_string(index=False))
    pd.concat([v1.assign(test="B1_yön"), v1m.assign(test="B1_büyüklük"), v2.assign(test="B2")]).to_csv(RES / "baglam_karar.csv", index=False)
    b2s = cells[(cells.rep == "P33") & (cells.B2_P >= 0.975) & (cells.B2_y1 > 0) & (cells.B2_y2 > 0)]
    if len(b2s):
        print("\nB2'de başarılı hücreler:"); print(b2s[["sym", "tf", "H", "ctx", "B2_fark", "B2_P", "B2_y1", "B2_y2"]].round(3).to_string(index=False))


# ─────────────────────────── çapraz ───────────────────────────
def pair_analysis() -> None:
    files = sorted((RES / "capraz").glob("*.parquet"))
    if not files:
        return
    d = basics(pd.concat([pd.read_parquet(p) for p in files], ignore_index=True))
    s = d.groupby(["rep", "var"]).apply(lambda g: pd.Series({
        "sorgu": len(g), "yön_%": 100 * g["corr"][g.call != 0].mean(), "taban_%": 100 * g.bcorr[g.call != 0].mean(),
        "plasebo_%": 100 * g.plc_acc[g.call != 0].mean(),
        "büyüklük_vs_saat_%": 100 * (1 - g.ae.sum() / g.ae_h[g.n > 0].sum()),
        "hedef_%": 100 * g.rcorr.mean()}), include_groups=False).reset_index()
    print("\n\n=== ÇAPRAZ-SEMBOL — tüm havuz ==="); print(s.round(2).to_string(index=False))
    s.to_csv(RES / "capraz_ozet_havuz.csv", index=False)
    key = ["sym", "ortak", "tf", "H", "rep", "q"]
    w = d.pivot_table(index=key, columns="var", values=["corr", "ae"], aggfunc="first")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    meta = d[d["var"] == "ikisi"].set_index(key)[["blk", "ts", "bcorr", "plc_acc"]]
    w = w.join(meta, how="inner").reset_index()
    pr = w.groupby(["sym", "ortak"]).apply(lambda g: pd.Series({
        "kendi_%": 100 * g.corr_kendi.mean(), "ortak_%": 100 * g.corr_ortak.mean(), "ikisi_%": 100 * g.corr_ikisi.mean(),
        "taban_%": 100 * g.bcorr.mean(), "ikisi−kendi_puan": 100 * (g.corr_ikisi - g.corr_kendi).mean(),
        "büyüklük_ikisi_vs_kendi_%": 100 * (1 - g.ae_ikisi.sum() / g.ae_kendi.sum())}), include_groups=False).reset_index()
    print("\n=== ÇİFT BAZINDA (tüm TF/ufuk/temsil) ==="); print(pr.round(2).to_string(index=False))
    cells = []
    for (sym, ortak, tf, H, rep), g in w.groupby(["sym", "ortak", "tf", "H", "rep"]):
        r = {"sym": sym, "ortak": ortak, "tf": tf, "H": H, "rep": rep}
        for nm, diff in (("ik_kendi", g.corr_ikisi - g.corr_kendi), ("ik_ortak", g.corr_ikisi - g.corr_ortak),
                         ("ik_taban", g.corr_ikisi - g.bcorr), ("ikm_kendi", g.ae_kendi - g.ae_ikisi)):
            m, p, y1, y2 = boot(diff.to_numpy(), g.blk.to_numpy(), g.ts.to_numpy())
            r |= {f"{nm}_fark": m, f"{nm}_P": p, f"{nm}_y1": y1, f"{nm}_y2": y2}
        cells.append(r)
    cells = pd.DataFrame(cells); cells.to_csv(RES / "capraz_hucre_testleri.csv", index=False)
    for nm, lab in (("ik_kendi", "ortak şekil > kendi şekli (yön)"), ("ik_ortak", "ortak şekil > ortağın şekli (yön)"),
                    ("ik_taban", "ortak şekil > hep-çoğunluk tabanı (yön)"), ("ikm_kendi", "ortak şekil > kendi şekli (büyüklük)")):
        print(f"\n=== B3: {lab} ===")
        print(verdict(cells, f"{nm}_P", f"{nm}_y1", f"{nm}_y2", ["rep"]).to_string(index=False))


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)
    ctx_analysis()
    pair_analysis()
