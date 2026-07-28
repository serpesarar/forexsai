"""daygate_combo.py — GÜN YÖNÜ TAHMİNİ + MUM TEYİDİ kombinasyonu (kullanıcı isteği).

Fikir: "Önce günün yönünü belirle; gün BOĞA ise, senin mum teyidinle (yeşil mum
kapanışı / destek dönüşü / EMA dönüşü) kısa-TP long aç."

GÜN YÖNÜ TAHMİNLERİ (hepsi karar anında BİLİNEN, sızıntısız):
  G1 AÇILIŞ-30    NY açılışının ilk 30 dk'sı yeşil (13:30→14:00 UTC getiri > 0)
  G2 AÇILIŞ-30 GÜÇLÜ  ilk 30 dk > +%0.20
  G3 GAP YUKARI   bugünkü RTH açılışı > dünkü RTH kapanışı
  G4 GECE POZİTİF gece seansı (00:00→13:25) getiri > 0
  G5 VIX REJİMİ   dünkü VIX kapanışı ≥ 18.4 → BUY lehine (doğrulanmış bulgu)
  G6 DÜN YEŞİL    önceki gün kapanışı > önceki gün açılışı
  G7 G1 & G4      açılış VE gece aynı yönde (çift teyit)

MUM TEYİTLERİ (hiwr_lab ile aynı): gövdeli yeşil 5m · destek dönüşü ·
EMA20 üstüne dönüş · 15m trend + yeşil.

Giriş penceresi: 14:00 → 19:30 UTC (gün yönü ancak 14:00'te bilinir).
Geometri: kısa TP'ler (20/60, 30/90, 40/110, 60/110) + botun 80/110'u.
Dürüstlük: hiwr_lab kuralları aynen (kapanmış mum, sonraki 1m açılışı, SL-önce,
aynı anda 1 pozisyon, kronolojik dilimler, gün-bloklu bootstrap).

NOT: Debate/bias motorunun günlük çağrıları da istendi — ama NDX'te yalnız
~15 gün ve 4 boğa çağrısı var (Temmuz'da başladı). n<10 işlemle ölçüm
anlamsız; rapor sonunda ayrıca listelenir, kapı olarak DEĞERLENDİRİLMEZ.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hiwr_lab import (FRIC, RNG, build_setups, day_boot_wr, load,
                      replay_episodes, split_of)

DATA = Path(__file__).resolve().parent / "data"
GEOMS = [(20, 60), (30, 90), (40, 110), (60, 110), (80, 110)]


def day_direction_table(b1: pd.DataFrame) -> pd.DataFrame:
    """Gün başına yön tahminleri. Hepsi 14:00 UTC itibarıyla bilinir."""
    d = b1.copy()
    d["gun"] = d.ts.dt.date
    mins = d.ts.dt.hour * 60 + d.ts.dt.minute

    rows = []
    for gun, g in d.groupby("gun", sort=True):
        m = g.ts.dt.hour * 60 + g.ts.dt.minute
        open1330 = g.loc[m >= 13 * 60 + 30, "open"]
        px1400 = g.loc[m >= 14 * 60, "open"]
        px0000 = g["open"].iloc[0]
        px1325 = g.loc[m <= 13 * 60 + 25, "close"]
        rth_close = g.loc[m <= 20 * 60, "close"]
        rows.append(dict(
            gun=gun,
            rth_open=open1330.iloc[0] if len(open1330) else np.nan,
            px_1400=px1400.iloc[0] if len(px1400) else np.nan,
            gece_acilis=px0000,
            px_premkt=px1325.iloc[-1] if len(px1325) else np.nan,
            gun_kapanis=rth_close.iloc[-1] if len(rth_close) else np.nan,
            gun_acilis=g["open"].iloc[0],
        ))
    t = pd.DataFrame(rows).sort_values("gun").reset_index(drop=True)
    t["or30_ret"] = (t.px_1400 / t.rth_open - 1) * 100
    t["gece_ret"] = (t.px_premkt / t.gece_acilis - 1) * 100
    t["prev_close"] = t.gun_kapanis.shift(1)
    t["gap_up"] = t.rth_open > t.prev_close
    t["dun_yesil"] = (t.gun_kapanis > t.gun_acilis).shift(1)

    # VIX (dünkü kapanış — macro_daily.csv gerçek UTC günlük)
    mx = pd.read_csv(DATA / "macro_daily.csv", parse_dates=["date"])
    mx["gun"] = mx.date.dt.date
    mx = mx.sort_values("gun")
    mx["vix_prev"] = mx["VIX_close"].shift(1)
    t = t.merge(mx[["gun", "vix_prev"]], on="gun", how="left")
    t["vix_prev"] = t["vix_prev"].ffill()

    t["G1"] = t.or30_ret > 0
    t["G2"] = t.or30_ret > 0.20
    t["G3"] = t.gap_up
    t["G4"] = t.gece_ret > 0
    t["G5"] = t.vix_prev >= 18.4
    t["G6"] = t.dun_yesil.fillna(False)
    t["G7"] = t.G1 & t.G4
    return t


def main() -> None:
    pd.set_option("display.width", 240)
    b1, b5, b15 = load()
    d = build_setups(b1, b5, b15)
    dd = day_direction_table(b1)
    print(f"gün sayısı: {len(dd)}  | G1 boğa günü: {int(dd.G1.sum())}  "
          f"G2: {int(dd.G2.sum())}  G3: {int(dd.G3.sum())}  G4: {int(dd.G4.sum())}  "
          f"G5: {int(dd.G5.sum())}  G6: {int(dd.G6.sum())}  G7: {int(dd.G7.sum())}\n")

    # kapıları 5m karar tablosuna bağla
    d["gun"] = d.ts.dt.date
    d = d.merge(dd[["gun", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]], on="gun", how="left")
    mins = d.ts.dt.hour * 60 + d.ts.dt.minute
    d["pencere"] = (mins >= 14 * 60) & (mins <= 19 * 60 + 30)   # 14:00–19:30 UTC

    CANDLES = {
        "gövdeli yeşil": d.green_solid,
        "destek dönüşü": d.sup_bounce,
        "EMA dönüşü": d.ema_crossup,
        "15m trend+yeşil": (d.trend15_up & d.green_solid),
    }
    GATES = {
        "kapı YOK": pd.Series(True, index=d.index),
        "G1 açılış-30 yeşil": d.G1,
        "G2 açılış-30 güçlü": d.G2,
        "G3 gap yukarı": d.G3,
        "G4 gece pozitif": d.G4,
        "G5 VIX≥18.4": d.G5,
        "G6 dün yeşil": d.G6,
        "G7 açılış&gece": d.G7,
    }

    rows = []
    for cn, cm in CANDLES.items():
        for gn, gm in GATES.items():
            mask = (cm & gm.fillna(False) & d.pencere).fillna(False)
            sig = (d.ts[mask] + pd.Timedelta(minutes=5)).values
            for tp, sl in GEOMS:
                be = (sl + FRIC) / (tp + sl)
                ep, amb = replay_episodes(b1, sig, float(tp), float(sl))
                if len(ep) < 40:
                    continue
                ep["sp"] = split_of(ep.ts)
                wr = ep.outcome.mean()
                lo, hi = day_boot_wr(ep)
                sub = {s: ep[ep.sp == s] for s in ("tr", "va", "te")}
                rows.append(dict(
                    mum=cn, kapı=gn, tp=tp, sl=sl, n=len(ep),
                    gün=ep.ts.dt.date.nunique(),
                    WR=round(wr * 100, 1), çıta=round(be * 100, 1),
                    marj=round((wr - be) * 100, 1), EV=round(ep.r.mean(), 4),
                    WR_GA=f"[{lo*100:.0f},{hi*100:.0f}]",
                    tr=round(sub["tr"].r.mean(), 3) if len(sub["tr"]) > 10 else np.nan,
                    va=round(sub["va"].r.mean(), 3) if len(sub["va"]) > 10 else np.nan,
                    te=round(sub["te"].r.mean(), 3) if len(sub["te"]) > 10 else np.nan,
                ))
    r = pd.DataFrame(rows)
    r.to_csv(DATA / "daygate_results.csv", index=False)

    print("═══ EN İYİ 25 (marj = WR − çıta) ═══")
    print(r.sort_values("marj", ascending=False).head(25).to_string(index=False))

    print("\n═══ KAPININ KATKISI — aynı mum+geometri, kapılı vs kapısız (EV farkı) ═══")
    base = r[r["kapı"] == "kapı YOK"].set_index(["mum", "tp", "sl"]).EV
    kat = []
    for _, x in r[r["kapı"] != "kapı YOK"].iterrows():
        b = base.get((x["mum"], x.tp, x.sl))
        if b is not None:
            kat.append(dict(mum=x["mum"], kapı=x["kapı"], tp=x.tp, sl=x.sl,
                            n=x.n, EV_kapılı=x.EV, EV_kapısız=round(b, 4),
                            katkı=round(x.EV - b, 4), marj=x.marj))
    k = pd.DataFrame(kat)
    print(k.sort_values("katkı", ascending=False).head(15).to_string(index=False))

    print("\n═══ TAM GEÇENLER (marj>0 VE tr/va/te üçü de ≥0) ═══")
    ok = r[(r.marj > 0) & (r.tr.fillna(-1) >= 0) & (r.va.fillna(-1) >= 0)
           & (r.te.fillna(-1) >= 0)]
    print(ok.sort_values("EV", ascending=False).to_string(index=False) if len(ok) else "  YOK")


if __name__ == "__main__":
    main()
