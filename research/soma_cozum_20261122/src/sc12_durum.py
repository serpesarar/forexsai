"""SC-12 — aday ateşlemeler arasında Soma'nın seçimini hesap durumu açıklıyor mu? (PROTOCOL SC-12)

Karar anı τ = min(ateşleme, eşleşen girişin − 1 sn) → eşleşen sinyalin kendisi durumdan çıkar; ıskada τ = ateşleme.
Çıktı: results/sc12_sonuc.json, results/sc12_tekli.csv, results/sc12_durum.parquet
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc08_kural as K  # noqa: E402
import sc08_ozellik as F  # noqa: E402
import sc11_analiz as A  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_tick as TK  # noqa: E402
import sc_veri as V  # noqa: E402

R = A.R
YOK = 10 ** 7
OZ = ["acik_n", "acik_ayni", "son_kapanis_sn", "son_sinyal_sn", "gun_sinyal_n", "gun_net", "son_sinyal_kar", "son5_net", "hafta_net"]


def _sunucu(t: np.ndarray) -> np.ndarray:
    return t + F.sunucu_ofset(t)


def durum(hesap: str, tau: np.ndarray) -> pd.DataFrame:
    p = V.islemler(hesap, sessiz=True)
    gi, ci = p["t_giris"].to_numpy("int64"), p["t_cikis"].to_numpy("int64")
    net, yon = p["net"].to_numpy(float), p["yon"].to_numpy(int)
    sg = p.groupby("sinyal").agg(bas=("t_giris", "min"), son=("t_cikis", "max"), net=("net", "sum")).sort_values("bas")
    sb, ss, sn = sg["bas"].to_numpy(), sg["son"].to_numpy(), sg["net"].to_numpy()
    o_ss = np.argsort(ss)
    ss_s, sn_s = ss[o_ss], sn[o_ss]
    o_ci = np.argsort(ci)
    ci_s, net_s = ci[o_ci], net[o_ci]
    kum_net = np.r_[0.0, np.cumsum(net_s)]
    gun = _sunucu(tau) // 86400
    gun_bas = gun * 86400 - (_sunucu(tau) - tau)            # sunucu günü başının UTC karşılığı (yaklaşık, ofset sabit)
    hafta_bas = gun_bas - ((gun + 3) % 7) * 86400           # 1970-01-01 Perşembe → Pazartesi başı
    out = {k: np.zeros(len(tau)) for k in OZ}
    for i, (t, y) in enumerate(zip(tau, np.zeros(len(tau)))):
        acik = (gi < t) & (ci > t)
        out["acik_n"][i] = acik.sum()
        j = np.searchsorted(ci_s, t) - 1
        out["son_kapanis_sn"][i] = t - ci_s[j] if j >= 0 else YOK
        k = np.searchsorted(sb, t) - 1
        out["son_sinyal_sn"][i] = t - sb[k] if k >= 0 else YOK
        out["gun_sinyal_n"][i] = np.sum((sb >= gun_bas[i]) & (sb < t))
        a, b = np.searchsorted(ci_s, gun_bas[i]), np.searchsorted(ci_s, t)
        out["gun_net"][i] = kum_net[b] - kum_net[a]
        a2 = np.searchsorted(ci_s, hafta_bas[i])
        out["hafta_net"][i] = kum_net[b] - kum_net[a2]
        m = np.searchsorted(ss_s, t)                         # t'den önce TAMAMEN kapanmış sinyaller
        out["son_sinyal_kar"][i] = np.sign(sn_s[m - 1]) if m > 0 else 0
        out["son5_net"][i] = sn_s[max(0, m - 5):m].sum()
    return pd.DataFrame(out)


def olaylar(hesap: str) -> pd.DataFrame:
    E = A.olaylar_d()
    Fv = E[E["tur"] == "F"].reset_index(drop=True)
    P = E[(E["tur"] == "P") & (E["hesap"] == hesap)]
    pt, py = P["t_d"].to_numpy(), P["y"].to_numpy()
    eslesen, tau = np.zeros(len(Fv), bool), Fv["t_d"].to_numpy().astype("int64").copy()
    for i, (t, y) in enumerate(zip(Fv["t_d"], Fv["y"])):
        m = (np.abs(pt - t) <= K.PENCERE) & (py == y)
        if m.any():
            eslesen[i] = True
            tau[i] = min(t, int(pt[m].min()) - 1)
    Fv["eslesen"], Fv["tau"] = eslesen, tau
    X = pd.concat([Fv, durum(hesap, tau)], axis=1)
    # acik_ayni: aynı yönde açık pozisyon (ayrı hesap — yön gerekir)
    p = V.islemler(hesap, sessiz=True)
    gi, ci, yo = p["t_giris"].to_numpy(), p["t_cikis"].to_numpy(), p["yon"].to_numpy()
    X["acik_ayni"] = [float(((gi < t) & (ci > t) & (yo == y)).sum()) for t, y in zip(tau, X["y"])]
    X["hesap_d"] = hesap
    return X


def tekli(X: pd.DataFrame) -> pd.DataFrame:
    pos, neg = X[X["eslesen"]], X[~X["eslesen"]]
    rows = []
    for c in OZ:
        a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
        auc = roc_auc_score(np.r_[np.ones(len(a)), np.zeros(len(b))], np.r_[a, b])
        rows.append({"ozellik": c, "AUC": round(max(auc, 1 - auc), 3), "yon": "≥" if auc >= 0.5 else "≤",
                     "eslesen_med": float(np.median(a)), "iska_med": float(np.median(b)),
                     "eslesen_ort": round(float(np.mean(a)), 3), "iska_ort": round(float(np.mean(b)), 3)})
    return pd.DataFrame(rows).sort_values("AUC", ascending=False)


def main() -> None:
    kesim = TK.kesim()
    X = olaylar("2268766")
    Xc = olaylar("2347514")
    X.to_parquet(R / "sc12_durum.parquet")
    Xk = X[X["tau"] < kesim]
    T = tekli(Xk)
    T.to_csv(R / "sc12_tekli.csv", index=False)
    pd.set_option("display.width", 250)
    print(T.to_string(index=False))
    # açgözlü ≤ 3 koşul (eşleşenlerin ≥ %80'i)
    pos, neg = Xk[Xk["eslesen"]], Xk[~Xk["eslesen"]]
    mp, mn, kural = np.ones(len(pos), bool), np.ones(len(neg), bool), []
    for _ in range(3):
        en = None
        for _, r in T[T["AUC"] >= 0.55].iterrows():
            c, yon = r["ozellik"], r["yon"]
            if any(c == k[0] for k in kural):
                continue
            a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
            for q in (0.02, 0.05, 0.10, 0.15, 0.20):
                e = float(np.quantile(a[mp], q if yon == "≥" else 1 - q))
                ga, gb = (a >= e, b >= e) if yon == "≥" else (a <= e, b <= e)
                if (mp & ga).mean() < 0.80:
                    continue
                if en is None or (mn & gb).mean() < en[0]:
                    en = ((mn & gb).mean(), c, yon, e)
        if en is None or (kural and en[0] > 0.97 * mn.mean()):
            break
        _, c, yon, e = en
        kural.append((c, yon, e))
        a, b = pos[c].to_numpy(float), neg[c].to_numpy(float)
        mp &= (a >= e) if yon == "≥" else (a <= e)
        mn &= (b >= e) if yon == "≥" else (b <= e)
        print(f"+ {c} {yon} {e:.3f}  eşleşen kapsama %{mp.mean() * 100:.1f}  ıska geçme %{mn.mean() * 100:.1f}")
    E = A.olaylar_d()
    sonuc = {"kural": kural, "tekli_ilk": T.head(9).to_dict("records")}
    for ad, XX in (("soma", X), ("cwdt", Xc)):
        ok = A.kural_ok(XX, kural) if kural else np.ones(len(XX), bool)
        Af = pd.DataFrame({"t": XX["t_d"].to_numpy()[ok], "y": XX["y"].to_numpy()[ok]})
        sonuc[ad] = A.degerlendir(Af, E, kesim)
    print(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    (R / "sc12_sonuc.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    D.kaydet("SC-12", "HESAP", {"kural": kural}, {"soma": sonuc["soma"], "cwdt": sonuc["cwdt"]})


if __name__ == "__main__":
    main()
