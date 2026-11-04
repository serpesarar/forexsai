"""alg_tarama.py çıktılarının özeti: tüm yapılandırmalar CSV'si, aile/TF/ufuk tabloları, seçim düzeltmesi (maxT, tam hafta
kaydırma), Bonferroni, ADAY denetimi, iyi↔kötü simetrisi (E26) ve aileler arası uyum (keşif, ön-kayıt dışı).
Çalıştır: python3.13 research/mum_derin_tarama_20261013/algoritmalar/alg_ozet.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
MIN_N = 200
ORDER = [("1m", "15m"), ("1m", "1h"), ("1m", "1d"), ("5m", "15m"), ("5m", "1h"), ("5m", "1d"),
         ("15m", "15m"), ("15m", "1h"), ("15m", "1d"), ("1h", "1h"), ("1h", "1d")]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)


def load():
    cfgs, T, N, E = [], [], [], []
    for tf, hz in ORDER:
        p = RES / f"{tf}_{hz}_cfg.parquet"
        if not p.exists():
            print("EKSİK", tf, hz); continue
        c = pd.read_parquet(p); z = np.load(RES / f"{tf}_{hz}_null.npz")
        cfgs.append(c); T.append(z["t"]); N.append(z["n"]); E.append(z["e"])
    cfg = pd.concat(cfgs, ignore_index=True)
    return cfg, np.concatenate(T, 1), np.concatenate(N, 1), np.concatenate(E, 1)


def main() -> None:
    cfg, T, Nn, E = load()
    S = T.shape[0]
    elig_null = (Nn >= MIN_N) & np.isfinite(T)
    Tm = np.where(elig_null, T, -np.inf)
    maxT = Tm.max(1)
    Em = np.where(elig_null, E, -np.inf); maxE = Em.max(1)
    real_ok = (cfg.n >= MIN_N) & np.isfinite(cfg.t)
    n_elig = int(real_ok.sum())
    cfg["p_adj_maxT"] = [(1 + (maxT >= t).sum()) / (1 + S) if ok else np.nan for t, ok in zip(cfg.t, real_ok)]
    cfg["p_tek"] = 1 - norm.cdf(cfg.t)
    cfg["p_bonf"] = np.minimum(1, cfg.p_tek * n_elig)
    # aile içi maxT (yalnız o ailenin yapılandırmaları)
    cfg["p_adj_aile"] = np.nan
    for fam, g in cfg.groupby("fam"):
        cols = g.index.to_numpy()
        mf = Tm[:, cols].max(1)
        cfg.loc[cols, "p_adj_aile"] = [(1 + (mf >= t).sum()) / (1 + S) if ok else np.nan
                                       for t, ok in zip(g.t, real_ok[cols])]
    crit = pd.DataFrame({
        "n200": cfg.n >= MIN_N, "fark2": cfg.exc >= 0.02, "plasebo": cfg.plc_beat.fillna(False).astype(bool),
        "P975": cfg.P_boot >= 0.975, "iki_yari": (cfg.exc_y1 > 0) & (cfg.exc_y2 > 0), "hareket": cfg.mv_pts > 1.5,
        "secim": cfg.p_adj_maxT <= 0.05})
    cfg["gecen_olcut"] = crit.sum(1)
    cfg["aday"] = crit.all(1)
    cfg["aday_secim_haric"] = crit.drop(columns="secim").all(1)
    cfg.to_csv(RES / "tum_yapilandirmalar.csv", index=False)

    print(f"Yapılandırma: {len(cfg)} (n≥{MIN_N}: {n_elig}); kaydırma tekrarı {S}")
    print(f"Gerçek maxT = {cfg.t[real_ok].max():.3f}  boş maxT yüzdelikleri 50/90/95/99 = "
          f"{np.percentile(maxT, [50, 90, 95, 99]).round(3)}  → aile p = {(1 + (maxT >= cfg.t[real_ok].max()).sum()) / (1 + S):.3f}")
    print(f"Gerçek max fark = {100 * cfg.exc[real_ok].max():.2f} puan; boş max fark 50/95 = {np.percentile(100 * maxE, [50, 95]).round(2)}")
    print("\nÖlçüt geçme sayıları (n≥200 içinde):")
    print(crit[real_ok].sum().to_string())
    print(f"Seçim hariç tüm ölçütleri geçen: {int(cfg.aday_secim_haric.sum())}; ADAY: {int(cfg.aday.sum())}")
    top = cfg[real_ok].sort_values("t", ascending=False).head(15)
    print("\nEn yüksek t (n≥200):")
    print(top[["tf", "hz", "fam", "W", "par", "K", "rule", "n", "acc", "acc_maj", "acc_hour", "exc", "t", "P_boot",
               "exc_y1", "exc_y2", "plc_max", "mv_pts", "p_adj_maxT", "p_adj_aile", "p_bonf", "gecen_olcut"]].round(4).to_string())
    near = cfg[cfg.gecen_olcut >= 5].sort_values("t", ascending=False)
    print(f"\n≥5 ölçüt geçen {len(near)} yapılandırma:")
    print(near[["tf", "hz", "fam", "W", "par", "K", "rule", "n", "exc", "t", "P_boot", "exc_y1", "exc_y2", "plc_beat",
                "mv_pts", "p_adj_maxT"]].round(4).head(25).to_string())

    # iyi ↔ kötü simetrisi (E26)
    ok = cfg[real_ok]
    good = ((ok.P_boot >= 0.975) & (ok.exc_y1 > 0) & (ok.exc_y2 > 0)).sum(); bad = (ok.P_boot <= 0.025).sum()
    bt = binomtest(int(good), int(good + bad), 0.5).pvalue if good + bad else np.nan
    print(f"\nAnlamlı İYİ (P≥0,975 & iki yarı +): {good}  ·  anlamlı KÖTÜ (P≤0,025): {bad}  · işaret testi p={bt:.3g}"
          f"  · tesadüf beklentisi her yönde ≈{0.025 * n_elig:.0f}")
    ag = ok.groupby("fam").agg(yap=("t", "size"), n_ort=("n", "mean"), isabet=("acc", "mean"), cogunluk=("acc_maj", "mean"),
                               saat=("acc_hour", "mean"), plasebo=("plc_mean", "mean"), fark_ort=("exc", "mean"),
                               fark_maks=("exc", "max"), t_maks=("t", "max"),
                               iyi=("P_boot", lambda x: int((x >= 0.975).sum())), kotu=("P_boot", lambda x: int((x <= 0.025).sum())),
                               p_aile_min=("p_adj_aile", "min"))
    ag["model_eksi_plasebo"] = ag.isabet - ag.plasebo
    print("\nAile özeti (n≥200 yapılandırmalar, ortalama):"); print(ag.round(4).to_string())
    ag.to_csv(RES / "ozet_aile.csv")
    th = ok.groupby(["tf", "hz"]).agg(yap=("t", "size"), isabet=("acc", "mean"), cogunluk=("acc_maj", "mean"),
                                      saat=("acc_hour", "mean"), plasebo=("plc_mean", "mean"), fark_ort=("exc", "mean"),
                                      fark_maks=("exc", "max"), t_maks=("t", "max"),
                                      iyi=("P_boot", lambda x: int((x >= 0.975).sum())), kotu=("P_boot", lambda x: int((x <= 0.025).sum())))
    print("\nTF × ufuk özeti:"); print(th.round(4).to_string()); th.to_csv(RES / "ozet_tf_ufuk.csv")
    rk = ok.groupby(["rule"]).agg(yap=("t", "size"), n_ort=("n", "mean"), isabet=("acc", "mean"), fark_ort=("exc", "mean"),
                                  iyi=("P_boot", lambda x: int((x >= 0.975).sum())), kotu=("P_boot", lambda x: int((x <= 0.025).sum())))
    print("\nKural özeti:"); print(rk.round(4).to_string())
    kw = ok[ok.K > 0].groupby(["K"]).agg(yap=("t", "size"), isabet=("acc", "mean"), fark_ort=("exc", "mean"))
    ww = ok[~ok.fam.isin(["cokolcek", "refR7", "ngram"])].groupby("W").agg(yap=("t", "size"), isabet=("acc", "mean"), fark_ort=("exc", "mean"))
    print("\nK:"); print(kw.round(4).to_string()); print("\nW:"); print(ww.round(4).to_string())
    # kanonik yapılandırma: K=50, tüm, W=20 (W'li aileler), SAX a3w4, ngram a3w6
    can = cfg[(cfg.rule == "tum") & (((cfg.K == 50) & cfg.W.isin([20, 32, 7])) | ((cfg.fam == "SAXyol") & (cfg.W == 20) & (cfg.par == "a3w4"))
                                     | ((cfg.fam == "ngram") & (cfg.par == "a3w6")))]
    can = can[~((can.fam == "ngram") & (can.K > 0))]
    pv = can.pivot_table(index=["tf", "hz"], columns="fam", values="exc", aggfunc="first")
    print("\nKanonik yapılandırma farkı (isabet − maks taban, puan):"); print((100 * pv).round(2).to_string())
    pv2 = can.pivot_table(index=["tf", "hz"], columns="fam", values="acc", aggfunc="first")
    pv3 = can.pivot_table(index=["tf", "hz"], columns="fam", values="plc_mean", aggfunc="first")
    print("\nKanonik isabet − plasebo (puan):"); print((100 * (pv2 - pv3)).round(2).to_string())
    pd.concat({"fark": pv, "isabet": pv2, "plasebo": pv3}, axis=1).to_csv(RES / "ozet_kanonik.csv")
    dtw = cfg[cfg.fam == "DTW"]
    print("\nDTW kesinlik oranı (seçim tam LB_Keogh sertifikalı):", dtw.groupby(["tf", "hz"]).dtw_exact.mean().round(3).to_dict())
    np.savez_compressed(RES / "secim_duzeltmesi_null.npz", maxT=maxT, maxE=maxE)
    consensus()


def consensus() -> None:
    """Keşif (ön-kayıt dışı): kanonik yapılandırmalarda kaç aile aynı yönü söylüyor → isabet vs taban."""
    rows = []
    for tf, hz in ORDER:
        p = RES / f"{tf}_{hz}_q.npz"
        if not p.exists():
            continue
        z = np.load(p, allow_pickle=False)
        names = [s.split("|") for s in z["names"]]
        want = []
        for i, (fam, W, par, K, rule) in enumerate(names):
            if rule != "tum":
                continue
            if fam in ("zED", "zED_amp", "DTW", "retcorr", "NW") and W == "20" and K == "50":
                want.append(i)
            elif fam in ("cokolcek", "refR7") and K == "50":
                want.append(i)
            elif fam == "SAXyol" and W == "20" and par == "a3w4":
                want.append(i)
            elif fam == "ngram" and par == "a3w6":
                want.append(i)
        C = z["calls"][:, want].astype(int); qt = z["qt"].astype(int)
        base = np.where(np.mean(z["bm"] == qt) >= np.mean(z["bh"] == qt), z["bm"], z["bh"])
        fams = [names[i][0] for i in want]
        agree = np.corrcoef(C.T) if C.shape[1] > 1 else None
        up = (C == 1).sum(1); dn = (C == -1).sum(1)
        for thr in (6, 7, 8):
            for side, m in (("YUKARI", up >= thr), ("ASAGI", dn >= thr)):
                if m.sum() < 30:
                    continue
                call = 1 if side == "YUKARI" else -1
                rows.append(dict(tf=tf, hz=hz, esik=thr, yon=side, n=int(m.sum()), isabet=float((qt[m] == call).mean()),
                                 taban=float((base[m] == qt[m]).mean()), mv=float((call * z["y"][m]).mean())))
        if agree is not None and tf == "1h" and hz == "1h":
            print("\n1h/1h aileler arası çağrı korelasyonu:", fams)
            print(np.round(agree, 2))
    d = pd.DataFrame(rows)
    if len(d):
        d["fark"] = d.isabet - d.taban
        print("\nKeşif — aile uzlaşısı (ön-kayıt DIŞI):"); print(d.round(4).to_string(index=False))
        d.to_csv(RES / "kesif_uzlasi.csv", index=False)


if __name__ == "__main__":
    main()
