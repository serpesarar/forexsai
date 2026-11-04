"""Adım 2 — KEŞİF ek analizleri (kasa kapalı). Ön-kayıt dışı olanlar 'POST-HOC' etiketlidir.

(a) brüt (maliyetsiz) sonuçlar — literatürle kıyas için
(b) S6 | VIX≥18,4 kovası (ön-kayıtlı V1 bölmesi) için ayrı kart (PROTOCOL §3: kova ayrı scope adayı olabilir)
(c) POST-HOC: sürekli pozisyon (sinyal/dvol, ±2 kırpma) — regresyon eğimi ile işaret stratejisi farkını açıklamak için
(d) POST-HOC: en büyük 5 / 10 gün çıkarılınca S6|VIX
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from imcore import COST, RES, STRESS, VIX_TH, boot_p, perm_p, summarize, yearly
from run_1_discovery import HYP, build, card, run_h, sig


def main() -> None:
    T30, T1h, T1m = build("30m", 30), build("1h", 60), build("1m", 1)
    data = {"30m": T30, "1h": T1h}
    out: dict = {}
    # (a) brüt
    br = []
    for hid in ["P1", "S1", "S2", "S4", "S5", "S6", "S7", "S6_30m"]:
        X = run_h(data[HYP[hid][2]], hid, cost=0.0)
        s = summarize(X, hid + "_brut")
        br.append(s)
    out["brut"] = br
    # maliyetin R cinsinden büyüklüğü yıllara göre
    c = (COST / (T1h.O900 * T1h.dvol)).groupby(T1h.index.year).median().round(4).to_dict()
    out["maliyet_R_yil_N1h"] = {int(k): v for k, v in c.items()}

    # (b) S6 | VIX≥18,4 kartı (N1h 10 y) + 30m + 1m icra
    def sub(X: pd.DataFrame) -> pd.DataFrame:
        return X[X.vix >= VIX_TH]
    X = sub(run_h(T1h, "S6"))
    Xs = sub(run_h(T1h, "S6", cost=COST * STRESS))
    X30 = sub(run_h(T30, "S6_30m"))
    X1 = sub(run_h(T1m, "S6_30m"))
    m, o = float(X.R.mean()), float(X.R_opt.mean())
    m1, o1 = float(X1.R.mean()), float(X1.R_opt.mean())
    icra = {"deger": f"N1h: iyimser {o:+.4f} vs gerçek {m:+.4f} (fark {o - m:+.4f}); "
                     f"N1m (n={len(X1)}): iyimser {o1:+.4f} vs gerçek {m1:+.4f} (fark {o1 - m1:+.4f})",
            "esik": "fark < ortR/2", "gecti": bool(m > 0 and (o - m) < m / 2 and (m1 <= 0 or (o1 - m1) < m1 / 2))}
    chk = card(X, Xs, icra)
    out["kart_S6_VIXhi"] = {"checks": chk, "gecen": int(sum(bool(v["gecti"]) for v in chk.values())),
                           "ozet_N1h": summarize(X, "S6|VIX>=18.4@1h"), "perm_p": perm_p(X)[0],
                           "ozet_N30": summarize(X30, "S6|VIX>=18.4@30m"),
                           "ozet_N1m": summarize(X1, "S6|VIX>=18.4@1m"),
                           "yillar_N1h": yearly(X), "yillar_N30": yearly(X30)}
    # (d) POST-HOC uç-gün bağımlılığı
    v = X.R.sort_values(ascending=False)
    out["kart_S6_VIXhi"]["en_iyi5_haric"] = round(float(v.iloc[5:].mean()), 4)
    out["kart_S6_VIXhi"]["en_iyi10_haric"] = round(float(v.iloc[10:].mean()), 4)
    out["kart_S6_VIXhi"]["toplamR"] = round(float(v.sum()), 2)
    out["kart_S6_VIXhi"]["en_iyi5_toplam"] = round(float(v.iloc[:5].sum()), 2)
    out["kart_S6_VIXhi"]["P_blok20"] = round(boot_p(X.R.to_numpy(), block=20)[0], 3)
    # VIX kovaları (post-hoc ayrıntı)
    Xa = run_h(T1h, "S6")
    bins = pd.cut(Xa.vix, [0, 15, 18.4, 25, 35, 100])
    out["S6_vix_kovalari"] = {str(k): [int(len(g)), round(float(g.R.mean()), 4), round(float(g.R_long.mean()), 4)]
                              for k, g in Xa.groupby(bins, observed=True)}

    # (c) POST-HOC sürekli pozisyon
    cont = {}
    for hid in ["P1", "S1", "S6"]:
        T = data[HYP[hid][2]]
        s_name, ent, _ = HYP[hid]
        x = sig(T, s_name)
        w = (x / T.dvol).clip(-2, 2)
        e, ex = T[f"O{ent}"], T.P960
        ok = w.notna() & e.notna() & ex.notna() & T.dvol.notna()
        R = (w[ok] * (ex[ok] - e[ok]) - w[ok].abs() * COST) / (e[ok] * T.dvol[ok])
        cont[hid] = {"n": int(ok.sum()), "ortR_birim_basina": round(float(R.mean()), 4),
                     "ort|w|": round(float(w[ok].abs().mean()), 3), "P": round(boot_p(R.to_numpy())[0], 3),
                     "yari": [round(float(R.iloc[:len(R) // 2].mean()), 4), round(float(R.iloc[len(R) // 2:].mean()), 4)]}
    out["POSTHOC_surekli"] = cont

    json.dump(out, open(RES / "kesif_ek.json", "w"), ensure_ascii=False, indent=1, default=str)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(br)[["id", "n", "ortR", "ort_puan", "ort_bp", "WR", "P_EV>0", "yari1", "yari2", "hepAL_ortR", "fark_hepAL"]].to_string(index=False))
    print(json.dumps({k: v for k, v in out.items() if k != "brut"}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
