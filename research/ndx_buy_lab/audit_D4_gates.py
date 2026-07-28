"""audit_D4_gates.py — GENİŞ KAPI ARAMASI + PLASEBO.

İddia: "HİÇBİR basit rejim kapısı 2022'yi kurtarmıyor."
Orijinal script 10 kapı denedi ve hiçbiri EMA200'ün EĞİMİNİ içermiyordu — oysa
iddianın KENDİ mekanizması ("ayı piyasasında EMA200 üstü = başarısız dağıtım")
tam olarak "EMA200 DÜŞERKEN üstünde olmak" demektir. Bunu ve 25+ kapıyı test et.

Sonra: 11 yılın 11'inde +EV bulgusu çoklu-testte ayakta mı? Kapsam ve GÜN/RUN
uzunluğu eşleştirilmiş RASTGELE kapılarla plasebo yap.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from audit_common import build, r_series

GEOMS = [(2.0, 1.0), (3.0, 1.0), (1.5, 1.0), (0.727, 1.0)]
MIN_BARS_YEAR = 200          # ~10 işlem günü; altındaki yıl "işlem edilmedi" sayılır


def gate_library(d: pd.DataFrame) -> dict:
    g = {}
    nz = lambda s: np.nan_to_num(d[s].to_numpy(), nan=np.nan)
    above200 = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
    above50 = np.nan_to_num(d["above_ema50"].to_numpy(), nan=0.0) > 0.5
    golden = np.nan_to_num(d["golden"].to_numpy(), nan=0.0) > 0.5
    slope = d["ema200_slope"].to_numpy()
    ts = pd.DatetimeIndex(d["ts"])
    hour = ts.hour.to_numpy()
    dow = ts.dayofweek.to_numpy()
    atr = d["atr_pct"].to_numpy()
    # ATR rejimi — SADECE geçmişe bakan kayan yüzdelik (2000 bar ~ 3 ay)
    atr_pct_rank = pd.Series(atr).rolling(2000, min_periods=500).rank(pct=True).to_numpy()

    g["G00 kapı YOK"] = np.ones(len(d), bool)
    g["G01 fiyat>EMA200"] = above200
    g["G02 EMA200 EĞİMİ>0"] = slope > 0
    g["G03 fiyat>EMA200 & EĞİM>0"] = above200 & (slope > 0)
    g["G04 fiyat>EMA50 & EĞİM>0"] = above50 & (slope > 0)
    g["G05 altın kesiş & EĞİM>0"] = golden & (slope > 0)
    g["G06 VIX vade yapısı<1 (contango)"] = nz("vix_ts") < 1.0
    g["G07 VIX vade<0.95"] = nz("vix_ts") < 0.95
    g["G08 VIX vade<1 & fiyat>EMA200"] = (nz("vix_ts") < 1.0) & above200
    g["G09 VIX vade<1 & EĞİM>0"] = (nz("vix_ts") < 1.0) & (slope > 0)
    g["G10 gerç.vol yüzdelik<0.8"] = nz("rv20_pct") < 0.8
    g["G11 gerç.vol yüzdelik<0.6"] = nz("rv20_pct") < 0.6
    g["G12 rv20<25"] = nz("rv20") < 25
    g["G13 ATR yüzdelik<0.8"] = atr_pct_rank < 0.8
    g["G14 ATR yüzdelik 0.2-0.8"] = (atr_pct_rank > 0.2) & (atr_pct_rank < 0.8)
    g["G15 20g&60g getiri>0"] = (nz("ret20d") > 0) & (nz("ret60d") > 0)
    g["G16 60g getiri>0 & EĞİM>0"] = (nz("ret60d") > 0) & (slope > 0)
    g["G17 düşüş60>-%5"] = nz("dd60") > -5
    g["G18 SPX>EMA200 & NDX>EMA200"] = (nz("spx_above_ema200") > 0.5) & above200
    g["G19 HYG 20g>0 (kredi)"] = nz("hyg_ret20") > 0
    g["G20 VIX<20"] = nz("vix") < 20
    g["G21 VIX/VIX_ma20<1.1"] = nz("vix_rel") < 1.1
    g["G22 saat 13-20 UTC (NY)"] = (hour >= 13) & (hour <= 20)
    g["G23 saat 07-15 UTC (AB+açılış)"] = (hour >= 7) & (hour <= 15)
    g["G24 Pzt-Per"] = dow <= 3
    g["G25 Sal-Cum"] = (dow >= 1) & (dow <= 4)
    g["G26 EĞİM>0 & VIX<25"] = (slope > 0) & (nz("vix") < 25)
    g["G27 EĞİM>0 & rv yüzd<0.8"] = (slope > 0) & (nz("rv20_pct") < 0.8)
    g["G28 EĞİM>0 & vade<1 & NY saati"] = (slope > 0) & (nz("vix_ts") < 1.0) & (hour >= 13) & (hour <= 20)
    g["G29 EĞİM>0 & 20g getiri>0"] = (slope > 0) & (nz("ret20d") > 0)
    g["G30 EĞİM>0 & düşüş120>-%12"] = (slope > 0) & (nz("dd120") > -12)
    return {k: np.nan_to_num(v, nan=False).astype(bool) for k, v in g.items()}


def year_table(r, mask, year, years):
    rec, pos, traded = {}, 0, 0
    for y in years:
        m = mask & (year == y)
        if m.sum() < MIN_BARS_YEAR:
            rec[f"y{y}"] = np.nan
            continue
        v = float(r[m].mean()); rec[f"y{y}"] = round(v, 3)
        traded += 1; pos += int(v > 0)
    return rec, pos, traded


def main() -> None:
    pd.set_option("display.width", 300)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"])
    year = ts.year.to_numpy()
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    years = list(range(2016, 2027))
    gates = gate_library(d)

    all_rows = []
    for tp_a, sl_a in GEOMS:
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        rows = []
        for name, gm in gates.items():
            m = ok & gm
            if m.sum() < 500:
                continue
            rec, pos, traded = year_table(r, m, year, years)
            row = dict(geom=f"TP{tp_a}/SL{sl_a}", kapi=name, n=int(m.sum()),
                       kapsam=round(m.sum() / ok.sum(), 3),
                       ev=round(float(r[m].mean()), 4), toplamR=round(float(r[m].sum()), 1),
                       ev2022=rec.get("y2022"), poz=pos, islenen_yil=traded, **rec)
            rows.append(row); all_rows.append(row)
        df = pd.DataFrame(rows).sort_values(["poz", "ev"], ascending=[False, False])
        print(f"\n══════ TP{tp_a}/SL{sl_a} — kapılar (poz_yıl'a göre) ══════")
        print(df.drop(columns=["geom"]).head(14).to_string(index=False))

    A = pd.DataFrame(all_rows)
    A.to_csv("data/audit_D_gates.csv", index=False)
    print("\n══════ TÜM KOMBİNASYONLAR — 'işlenen yılların HEPSİNDE +EV' olanlar ══════")
    best = A[(A.poz == A.islenen_yil) & (A.islenen_yil >= 8)].sort_values(["islenen_yil", "toplamR"],
                                                                          ascending=False)
    print(best[["geom", "kapi", "n", "kapsam", "ev", "toplamR", "ev2022", "poz", "islenen_yil"]]
          .to_string(index=False) if len(best) else "  YOK")
    print(f"\n  Test edilen kombinasyon sayısı = {len(A)}")

    print("\n══════ 2022'yi +EV YAPAN kapılar (2022'de en az 200 bar işleyerek) ══════")
    s = A[(A.ev2022 > 0)].sort_values("ev2022", ascending=False)
    print(s[["geom", "kapi", "n", "kapsam", "ev", "ev2022", "poz", "islenen_yil"]].to_string(index=False)
          if len(s) else "  YOK — hiçbir kapı 2022'yi +EV yapmıyor (iddianın bu kısmı ayakta)")

    print("\n══════ 2022'yi TAMAMEN ELEYEN (işlem yok) kapılar ══════")
    s2 = A[A.ev2022.isna()].groupby("kapi").agg(kapsam=("kapsam", "mean"),
                                                 ev=("ev", "mean"),
                                                 islenen_yil=("islenen_yil", "max")).reset_index()
    print(s2.round(4).to_string(index=False) if len(s2) else "  YOK")


if __name__ == "__main__":
    main()
