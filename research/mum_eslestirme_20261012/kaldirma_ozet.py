"""kaldirma_testi.py çıktısının özeti: kaldırmadan önce/sonra yön, büyüklük, hedef isabeti + anlamlılık + çoklu-TF uyumu.

Tanımlar (hepsi sorgu başına, ATR birimi):
  yön     : komşu oyu P = pay(r_H > 0). Çağrı = P > 0,5 yukarı / < 0,5 aşağı / = 0,5 çağrı yok.
            Taban = kütüphanenin koşulsuz yukarı oranı p0 → hep çoğunluk yönünü söyleyen tahmin (aynı sorgularda).
            Brier "takvim" skoru: komşu yoksa P := p0 (çekimser sorgu tabana düşer, ChatGPT P6).
  büyüklük: tahmin = komşuların medyan |r_H|; taban = aynı UTC saatinin medyan |r_H|; hata = |tahmin − gerçek|.
  hedef   : ±1 ATR yarışı; komşulardaki "önce +1" payı vs taban payı, yalnız sonucu belli sorgularda.
  plasebo : aynı havuzdan aynı sayıda rastgele komşu (20 tekrar ortalaması).
Anlamlılık: hücre (sembol × TF × ufuk × temsil × varyant) başına model−taban farkının gün-blok bootstrap'ı (blok ≥ ufuk),
B = 1000; "daha iyi" P(fark > 0) ≥ 0,975, "daha kötü" ≤ 0,025. Null altında her yönde ~%2,5 hücre beklenir.
Çalıştır: python3 research/mum_eslestirme_20261012/kaldirma_ozet.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from _common import HERE

RES = HERE / "results"
TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
TF_ORDER = ["5m", "15m", "30m", "1h", "4h", "1d"]
B = 1000
rng = np.random.default_rng(2026)


def load() -> pd.DataFrame:
    d = pd.concat([pd.read_parquet(p) for p in sorted((RES / "kaldirma").glob("*.parquet"))], ignore_index=True)
    d = d[np.isfinite(d.y) & (d.y != 0)].copy()
    yb = (d.y > 0).astype(float)
    has = d.n > 0
    d["call"] = np.where(has, np.sign(d.pu - 0.5), 0.0)
    d["corr"] = np.where(d.call != 0, ((d.call > 0) == (d.y > 0)).astype(float), np.nan)
    d["bcall"] = np.sign(d.p0 - 0.5)
    d["bcorr"] = np.where(d.call != 0, ((d.bcall > 0) == (d.y > 0)).astype(float), np.nan)
    d["hcorr"] = np.where(d.call != 0, ((np.sign(d.p0h - 0.5) > 0) == (d.y > 0)).astype(float), np.nan)
    P = np.where(has, d.pu, d.p0)
    d["br"] = (P - yb) ** 2; d["br0"] = (d.p0 - yb) ** 2; d["br0h"] = (d.p0h - yb) ** 2
    d["br_plc"] = np.where(has, d.plc_br, d.br0)
    pred = np.where(has, d.med, d.bmed_h)
    d["ae"] = np.abs(pred - d.absr); d["ae0"] = np.abs(d.bmed_h - d.absr)
    d["ae_plc"] = np.where(has, d.plc_ae, d.ae0)
    dec = d.race.isin([1, -1]) & np.isfinite(d.prace) & np.isfinite(d.prace0)
    rb = (d.race == 1).astype(float)
    d["rcorr"] = np.where(dec & (d.prace != 0.5), ((d.prace > 0.5) == (d.race == 1)).astype(float), np.nan)
    d["rbcorr"] = np.where(np.isfinite(d.rcorr), ((d.prace0 > 0.5) == (d.race == 1)).astype(float), np.nan)
    d["rbr"] = np.where(dec, (d.prace - rb) ** 2, np.nan); d["rbr0"] = np.where(dec, (d.prace0 - rb) ** 2, np.nan)
    d["day"] = (d.te // 86_400_000_000_000).astype(np.int64)
    return d


def summarize(g: pd.DataFrame) -> pd.Series:
    called = g.call != 0
    out = {
        "sorgu": len(g), "tespit": int((g.n > 0).sum()), "kapsama_%": 100 * (g.n > 0).mean(),
        "ort_komşu": g.n[g.n > 0].mean() if (g.n > 0).any() else 0.0,
        "yön_isabet_%": 100 * g["corr"][called].mean(), "taban_isabet_%": 100 * g.bcorr[called].mean(),
        "saat_taban_%": 100 * g.hcorr[called].mean(),
        "plasebo_isabet_%": 100 * g.plc_acc[called].mean(),
        "Brier_beceri_%": 100 * (1 - g.br.sum() / g.br0.sum()),
        "Brier_vs_plasebo_%": 100 * (1 - g.br.sum() / g.br_plc.sum()),
        "büyüklük_beceri_%": 100 * (1 - g.ae.sum() / g.ae0.sum()),
        "büyüklük_vs_plasebo_%": 100 * (1 - g.ae.sum() / g.ae_plc.sum()),
        "hedef_isabet_%": 100 * g.rcorr.mean(), "hedef_taban_%": 100 * g.rbcorr.mean(),
        "hedef_Brier_beceri_%": 100 * (1 - np.nansum(g.rbr) / np.nansum(g.rbr0)),
    }
    m = (g.n > 0) & np.isfinite(g.med)
    out["büyüklük_rho"] = spearmanr(g.med[m], g.absr[m]).correlation if m.sum() > 10 else np.nan
    out["saat_taban_rho"] = spearmanr(g.bmed_h[m], g.absr[m]).correlation if m.sum() > 10 else np.nan
    out["yön_fark_puan"] = out["yön_isabet_%"] - out["taban_isabet_%"]
    return pd.Series(out)


def block_boot(diff: np.ndarray, block: np.ndarray) -> tuple[float, float, float]:
    """Gün-blok bootstrap: ortalama fark, P(fark > 0), %95 aralık genişliği yarısı."""
    ok = np.isfinite(diff)
    diff, block = diff[ok], block[ok]
    if len(diff) < 30:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(block, return_inverse=True)
    S = np.bincount(inv, diff); N = np.bincount(inv)
    idx = rng.integers(0, len(u), size=(B, len(u)))
    bm = S[idx].sum(1) / N[idx].sum(1)
    return float(diff.mean()), float((bm > 0).mean()), float((np.quantile(bm, 0.975) - np.quantile(bm, 0.025)) / 2)


def cell_tests(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sym, tf, H, rep, var), g in d.groupby(["sym", "tf", "H", "rep", "var"], sort=False):
        bdays = max(1, int(np.ceil(H * TF_MIN[tf] / 1440)))
        blk = (g.day.to_numpy() // bdays)
        half = g.te.to_numpy() >= np.median(g.te.to_numpy())
        res = {"sym": sym, "tf": tf, "H": H, "rep": rep, "var": var, "sorgu": len(g), "tespit": int((g.n > 0).sum())}
        for name, diff in (("yön", (g["corr"] - g.bcorr).to_numpy()),
                           ("büyüklük", (g.ae0 - g.ae).to_numpy()),
                           ("hedef", (g.rcorr - g.rbcorr).to_numpy())):
            m, p, ci = block_boot(diff, blk)
            h1 = np.nanmean(diff[~half]) if np.isfinite(diff[~half]).any() else np.nan
            h2 = np.nanmean(diff[half]) if np.isfinite(diff[half]).any() else np.nan
            res.update({f"{name}_fark": m, f"{name}_P": p, f"{name}_ci": ci, f"{name}_y1": h1, f"{name}_y2": h2})
        rows.append(res)
    return pd.DataFrame(rows)


def agreement(d: pd.DataFrame) -> pd.DataFrame:
    """Aynı anda 5m/15m/30m/1h'in 4 saatlik ufuk tahminleri: kaç TF aynı yönü söylediğinde isabet ne?"""
    hmap = {("5m", 48), ("15m", 16), ("30m", 8), ("1h", 4)}
    x = d[[(tf, H) in hmap for tf, H in zip(d.tf, d.H)]]
    rows = []
    for (sym, rep, var), g in x.groupby(["sym", "rep", "var"]):
        pv = g.pivot_table(index="te", columns="tf", values="call", aggfunc="first")
        truth = g.groupby("te").y.first() > 0
        base = g[g.tf == "1h"].groupby("te").p0.first() > 0.5
        tfs = [t for t in ("5m", "15m", "30m", "1h") if t in pv.columns]
        pv = pv[tfs].dropna(how="any")
        if len(pv) < 50:
            continue
        up = (pv > 0).sum(1); dn = (pv < 0).sum(1); m = len(tfs)
        for k in range(m, 0, -1):
            sel = (up == k) | (dn == k)
            exact = sel & ~(((up == k) & (dn > 0)) | ((dn == k) & (up > 0)))
            if exact.sum() < 20:
                continue
            pred_up = (up == k)[exact]
            tr = truth.reindex(pred_up.index); bs = base.reindex(pred_up.index)
            ok = tr.notna() & bs.notna()
            rows.append({"sym": sym, "rep": rep, "var": var, "TF_sayısı": m, "aynı_yön_TF": k,
                         "an": int(ok.sum()), "isabet_%": 100 * (pred_up[ok] == tr[ok]).mean(),
                         "taban_isabet_%": 100 * (bs[ok] == tr[ok]).mean()})
    return pd.DataFrame(rows)


def main() -> None:
    d = load()
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    fmt = lambda t: t.round(2)  # noqa: E731
    v = d.groupby(["rep", "var"]).apply(summarize, include_groups=False).reset_index()
    v.to_csv(RES / "kaldirma_ozet_varyant.csv", index=False)
    print("=== TEMSİL × VARYANT (tüm sembol/TF/ufuk havuzu) ==="); print(fmt(v).to_string(index=False))
    t = d.groupby(["tf", "rep", "var"]).apply(summarize, include_groups=False).reset_index()
    t["_o"] = t.tf.map(TF_ORDER.index); t = t.sort_values(["_o", "rep", "var"]).drop(columns="_o")
    t.to_csv(RES / "kaldirma_ozet_tf.csv", index=False)
    print("\n=== TF × TEMSİL × VARYANT ==="); print(fmt(t[["tf", "rep", "var", "sorgu", "tespit", "kapsama_%", "yön_isabet_%", "taban_isabet_%",
                                                  "plasebo_isabet_%", "Brier_beceri_%", "büyüklük_beceri_%", "büyüklük_rho",
                                                  "saat_taban_rho", "hedef_isabet_%", "hedef_taban_%"]]).to_string(index=False))
    c = cell_tests(d); c.to_csv(RES / "kaldirma_hucre_testleri.csv", index=False)
    rows = []
    for (rep, var), g in c.groupby(["rep", "var"]):
        r = {"rep": rep, "var": var, "hücre": len(g)}
        for name in ("yön", "büyüklük", "hedef"):
            P = g[f"{name}_P"].dropna()
            both = g[(g[f"{name}_y1"] > 0) & (g[f"{name}_y2"] > 0)]
            r[f"{name}_test"] = len(P)
            r[f"{name}_iyi"] = int((P >= 0.975).sum()); r[f"{name}_kötü"] = int((P <= 0.025).sum())
            r[f"{name}_iyi_ve_iki_yarı+"] = int(((g[f"{name}_P"] >= 0.975) & (g[f"{name}_y1"] > 0) & (g[f"{name}_y2"] > 0)).sum())
            r[f"{name}_ort_fark"] = g[f"{name}_fark"].mean()
        rows.append(r)
    s = pd.DataFrame(rows); s.to_csv(RES / "kaldirma_anlamlilik.csv", index=False)
    print("\n=== ANLAMLILIK SAYIMI (null altında her yönde ~%2,5 hücre beklenir) ==="); print(fmt(s).to_string(index=False))
    a = agreement(d); a.to_csv(RES / "kaldirma_tf_uyumu.csv", index=False)
    if len(a):
        print("\n=== ÇOKLU-TF UYUMU (4 saatlik ufuk, 5m/15m/30m/1h aynı an) ===")
        print(fmt(a[a["var"].isin(["V0", "V2"])]).to_string(index=False))


if __name__ == "__main__":
    main()
