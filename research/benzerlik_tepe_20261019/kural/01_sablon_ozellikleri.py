"""ME-10 adım 1 — şablonların (T1–T3) ÖZELLİKLERİ (sonuç değil) + özelliklerin geliştirme dağılımındaki yüzdelikleri.

İleri getiri HESAPLANMAZ. Çıktı: results/01_sablon_ozellikleri.json + stdout.
Çalıştır: nice -n 10 python3.13 research/benzerlik_tepe_20261019/kural/01_sablon_ozellikleri.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from tepe_ozellik import features, load_ndx, query_index

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"; OUT.mkdir(exist_ok=True)
DEV_END = pd.Timestamp("2025-11-30 23:00", tz="UTC")
# kullanıcının yaklaşık tarihleri + T1'in veriyle inceltilmiş sonu (son 5 işlem gününde en düşük kapanış)
TEMPL = {"T1_kullanici": ("2026-07-06", "2026-07-21"), "T1_incel": ("2026-07-06", "2026-07-17"),
         "T2": ("2026-07-17", "2026-07-29"), "T3": ("2026-08-13", "2026-08-20")}
COLS = ["net", "net_s", "eff", "rv_ratio", "pos", "rng_s", "dist60_s", "dist20_s", "dist60_pct", "dist20_pct",
        "dd60_s", "swings", "lh", "pull_s", "sref"]


def main() -> None:
    d = load_ndx(); Q = query_index(d, 20)
    qdates = pd.Series(d.ts.iloc[Q].dt.date.to_numpy())
    res: dict = {"sorgu_saat_utc": 20, "veri_son_bar": str(d.ts.iloc[-1])}
    # son-5-gün inceltmesi (belgeleme): her şablonun son 5 işlem gününde en düşük kapanış günü
    incel = {}
    for name, (a, b) in TEMPL.items():
        m = (qdates >= pd.Timestamp(a).date()) & (qdates <= pd.Timestamp(b).date())
        ks = np.flatnonzero(m.to_numpy())
        closes = d.close.iloc[Q[ks]].to_numpy()
        last5 = ks[-5:]
        kmin = last5[np.argmin(d.close.iloc[Q[last5]].to_numpy())]
        incel[name] = {"gun_sayisi": int(len(ks)), "ilk": str(qdates[ks[0]]), "son": str(qdates[ks[-1]]),
                       "son5_en_dusuk_kapanis_gunu": str(qdates[kmin]),
                       "kapanislar": [round(float(x), 1) for x in closes]}
    res["sablon_gunleri"] = incel
    feats = {}
    for W in (6, 9, 10, 12):
        feats[W] = features(d, Q, W)
    own = {}
    for name, (a, b) in TEMPL.items():
        kend = int(np.flatnonzero((qdates == pd.Timestamp(b).date()).to_numpy())[0])
        Wown = incel[name]["gun_sayisi"]
        f = features(d, Q, Wown).iloc[kend]
        own[name] = {"W_kendi": Wown, **{c: round(float(f[c]), 4) for c in COLS}}
    res["kendi_penceresi"] = own
    trail = {}
    for W, f in feats.items():
        dev = (f.ts <= DEV_END) & f.rv_ratio.notna()
        fd = f[dev]
        tw = {}
        for name, (a, b) in TEMPL.items():
            kend = int(np.flatnonzero((qdates == pd.Timestamp(b).date()).to_numpy())[0])
            row = f.iloc[kend]
            tw[name] = {c: {"deger": round(float(row[c]), 4),
                            "gelistirme_yuzdeligi": round(float(100 * (fd[c] <= row[c]).mean()), 1)} for c in COLS}
        trail[f"W={W}"] = {"sablonlar": tw,
                           "gelistirme_dagilimi": {c: {q: round(float(fd[c].quantile(q / 100)), 4) for q in (5, 10, 25, 50, 75, 90, 95)}
                                                   for c in COLS},
                           "gelistirme_gun": int(len(fd)), "ilk_gecerli": str(fd.ts.iloc[0])}
    res["sondaki_W_penceresi"] = trail
    (OUT / "01_sablon_ozellikleri.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(json.dumps(incel, ensure_ascii=False, indent=1))
    print("\n== kendi penceresi ==")
    print(pd.DataFrame(own).T.to_string())
    for W in (6, 9, 10, 12):
        t = trail[f"W={W}"]
        print(f"\n== W={W} (sondaki pencere) değer [geliştirme yüzdeliği] ==  geliştirme gün={t['gelistirme_gun']}")
        rows = {nm: {c: f"{v['deger']:.3f} [{v['gelistirme_yuzdeligi']:.0f}]" for c, v in t["sablonlar"][nm].items()}
                for nm in TEMPL}
        print(pd.DataFrame(rows).to_string())
        print(pd.DataFrame(t["gelistirme_dagilimi"]).T.to_string())


if __name__ == "__main__":
    main()
