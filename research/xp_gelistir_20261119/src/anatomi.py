"""anatomi.py — YALNIZ KEŞİF (≤ 2021-10): kaybedenlerin anatomisi, yol, tek özellik taraması. python anatomi.py"""
import json
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parents[1]
D = pd.read_parquet(HERE / "results/islemler.parquet")
K = D[(D.donem == "KESIF") & D.besleme.isin(["DUKA_NDX", "MT5_US500", "MT5_US30", "MT5_US2000"])].copy()  # ayrı piyasalar
# Duka'ya MT5 NAS100 hacmini tarihle bağla
nas = D[D.besleme == "MT5_NAS100"].set_index("d").mt5_hacim_oran
m = K.besleme == "DUKA_NDX"
K.loc[m, "mt5_hacim_oran"] = K.loc[m, "d"].map(nas).values
FEATS = ["gun_ret", "seans_ret", "son_saat", "son_yarim", "ilk_yarim_saat", "twap_uz", "bosluk", "aralik", "kapanis_konum", "dip_saati",
         "r5", "r20", "rsi2", "sma20_uz", "sma50_uz", "sma200_uz", "rv20", "aralik_oran", "zirve_uz", "vix", "vix_deg", "vix_vix3m",
         "qqq_hacim_oran", "mt5_hacim_oran", "gun", "ay", "opex_k", "opex_a", "olay", "sess_dun", "K1_dun", "K1_son10"]

def loss_stats(v):
    v = np.asarray(v)
    return {"n": int(len(v)), "toplam": round(float(v.sum()), 0), "brut_zarar": round(float(v[v < 0].sum()), 0),
            "kaybeden_n": int((v < 0).sum()), "kotu10": round(float(np.sort(v)[:max(1, len(v) // 10)].mean()), 1)}

out = {"taban": loss_stats(K.net)}
# zarar yoğunlaşması
neg = np.sort(K.net[K.net < 0].values)
out["zarar_yogunlasma"] = {"en_kotu_10_islem_zarar_payi_%": round(float(neg[:10].sum() / neg.sum() * 100), 1),
                           "en_kotu_%20_kaybeden_payi_%": round(float(neg[:max(1, len(neg) // 5)].sum() / neg.sum() * 100), 1)}
# yol: kaybeden vs kazanan kontrol noktalarında ortalama konum
path = {}
for c in ["c17", "c20", "c00", "c04", "c0930", "c1200", "g1", "g2", "g3"]:
    path[c] = {"kazanan_ort": round(float(K[K.net > 0][c].mean()), 1), "kaybeden_ort": round(float(K[K.net < 0][c].mean()), 1),
               "kaybeden_buyuk_ort": round(float(K[K.net < -200][c].mean()), 1)}
out["yol"] = path
out["mae"] = {"kazanan_mae_medyan": round(float(K[K.net > 0].mae.median()), 1), "kaybeden_mae_medyan": round(float(K[K.net < 0].mae.median()), 1),
              "kazanan_mae_p10": round(float(K[K.net > 0].mae.quantile(0.1)), 1)}
out["tutus"] = K.groupby("tutus_gun").net.agg(["count", "mean"]).round(1).to_dict()
# tek özellik taraması: piyasa içi beşte birlik; her kova için brüt zarar payı ve kâr payı
scan = []
for f in FEATS:
    z = K.dropna(subset=[f]).copy()
    if z[f].nunique() <= 7:
        z["q"] = z[f]
    else:
        z["q"] = z.groupby("besleme")[f].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    tot_loss, tot = z.net[z.net < 0].sum(), z.net.sum()
    for qv, g in z.groupby("q"):
        if len(g) < 15:
            continue
        scan.append({"ozellik": f, "kova": qv, "n": len(g), "ort": round(g.net.mean(), 1), "isabet": round((g.net > 0).mean() * 100, 1),
                     "zarar_payi_%": round(g.net[g.net < 0].sum() / tot_loss * 100, 1), "kar_payi_%": round(g.net.sum() / tot * 100, 1),
                     "islem_payi_%": round(len(g) / len(z) * 100, 1)})
S = pd.DataFrame(scan)
S["verim"] = S["zarar_payi_%"] - S["kar_payi_%"]  # vetolanırsa: kazanılan zarar azaltımı − kaybedilen kâr
out["tarama_en_iyi_veto_adaylari"] = S.sort_values("verim", ascending=False).head(25).to_dict("records")
(HERE / "results/anatomi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: v for k, v in out.items() if k != "tarama_en_iyi_veto_adaylari"}, ensure_ascii=False, indent=0, default=str))
print(S.sort_values("verim", ascending=False).head(25).to_string(index=False))
