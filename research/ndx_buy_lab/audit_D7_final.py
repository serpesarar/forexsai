"""audit_D7_final.py — AİLE-BAZLI ÇOKLU-TEST DÜZELTMESİ + MEKANİZMANIN TEST EDİLEBİLİRLİĞİ
   + KAPSAM/EV TAKASI.

1) 28 kapı test edildi. "EMA200 kapısı 2022'yi -0.35'e düşürüyor" bulgusunun
   ham plasebo p'si 0.0135. Ama en kötü kapıyı POST-HOC seçtik. min-p (max-etki)
   yaklaşımıyla aile-bazlı düzeltilmiş p hesapla.
2) Mekanizma ("ayı piyasasında EMA200 üstü = başarısız dağıtım") kaç epizotta
   TEST EDİLEBİLİR? Düşüş eşiğini gevşeterek (-%15, -%10, -%8) say.
3) Kapı takası: kapsam kaybı vs EV artışı — yıllık R cinsinden.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from audit_common import build, r_series
from audit_D4_gates import gate_library
from geometry_sweep import build_paths, outcomes
from audit_D6_mechanism import daily_lab

FRIC = 1.0 / 29000


def main() -> None:
    pd.set_option("display.width", 250)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"]); yr = ts.year.to_numpy()
    days, day_idx = np.unique(ts.normalize().to_numpy(), return_inverse=True)
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    gates = gate_library(d)
    rng = np.random.default_rng(99)

    print("═════ 1) AİLE-BAZLI (min-p / max-etki) DÜZELTME — 2022, TP2.0/SL1.0 ═════")
    r, win, opn = r_series(d, cmax, cmin, end_ret, 2.0, 1.0)
    m22 = ok & (yr == 2022)
    d22_days = np.unique(day_idx[m22])
    # gerçek kapıların 2022 gün sayıları
    info = []
    for name, gm in gates.items():
        mm = m22 & gm
        if mm.sum() < 200 or name == "G00 kapı YOK":
            continue
        info.append((name, float(r[mm].mean()), len(np.unique(day_idx[mm]))))
    obs_min = min(x[1] for x in info)
    obs_name = min(info, key=lambda x: x[1])[0]
    print(f"  gözlenen EN KÖTÜ kapı: {obs_name}  EV2022 = {obs_min:+.4f}")
    print(f"  aile büyüklüğü = {len(info)} kapı")

    # NULL: her kapı için AYNI gün sayısında, 5 ardışık-blok yapısında rastgele
    # 2022 alt kümesi; min al; 3000 kez tekrarla.
    NSIM = 3000
    null_min, null_g01 = [], []
    n_g01 = [x[2] for x in info if x[0] == "G01 fiyat>EMA200"][0]
    for _ in range(NSIM):
        vals = []
        for name, _ev, nd in info:
            nblk = max(1, min(5, nd // 6))
            per = max(1, nd // nblk)
            picks = []
            for _k in range(nblk):
                st = rng.integers(0, max(1, len(d22_days) - per))
                picks.extend(d22_days[st:st + per])
            sel = m22 & np.isin(day_idx, np.unique(picks))
            if sel.sum() >= 100:
                vals.append(float(r[sel].mean()))
        if vals:
            null_min.append(min(vals))
        # ayrıca G01'in kendi kapsamında tek-kapı null'ı
        nblk = 5; per = max(1, n_g01 // nblk); picks = []
        for _k in range(nblk):
            st = rng.integers(0, max(1, len(d22_days) - per))
            picks.extend(d22_days[st:st + per])
        sel = m22 & np.isin(day_idx, np.unique(picks))
        if sel.sum() >= 100:
            null_g01.append(float(r[sel].mean()))
    null_min = np.array(null_min); null_g01 = np.array(null_g01)
    ev_g01 = [x[1] for x in info if x[0] == "G01 fiyat>EMA200"][0]
    p_raw = float((null_g01 <= ev_g01).mean())
    p_fw = float((null_min <= obs_min).mean())
    p_fw_g01 = float((null_min <= ev_g01).mean())
    print(f"\n  G01 (EMA200) EV2022 = {ev_g01:+.4f}")
    print(f"    HAM (tek-kapı) plasebo p            = {p_raw:.4f}")
    print(f"    AİLE-BAZLI düzeltilmiş p (min-p)    = {p_fw_g01:.4f}   ← 28 kapı denendiği için doğru olan")
    print(f"  en kötü kapı ({obs_name}) aile-bazlı p = {p_fw:.4f}")
    print(f"  null min dağılımı: ort={null_min.mean():+.4f} %5={np.percentile(null_min,5):+.4f} "
          f"%50={np.percentile(null_min,50):+.4f}")

    print("\n═════ 2) MEKANİZMA KAÇ EPİZOTTA TEST EDİLEBİLİR? (2008-2026 günlük) ═════")
    dl = daily_lab()
    H = 5
    e_, cmx, cmn, er = build_paths(dl, H)
    n = len(e_); ddl = dl.iloc[:n].reset_index(drop=True)
    a = ddl["atr_pct"].to_numpy()
    okd = np.isfinite(a) & (a > 0) & np.isfinite(ddl["dd252"].to_numpy())
    above = ddl["above200"].to_numpy() > 0.5
    tsd = pd.DatetimeIndex(ddl["ts"])
    for thr in (-15, -12, -10, -8):
        bear = ddl["dd252"].to_numpy() < thr
        bidx = np.where(okd & bear)[0]
        if not len(bidx):
            continue
        brk = np.concatenate([[0], (np.diff(bidx) > 30).cumsum()])
        ep = np.full(len(ddl), -1); ep[bidx] = brk
        testable = 0; details = []
        for e in sorted(set(brk)):
            m = ep == e
            nu = int((m & above & okd).sum()); na = int((m & ~above & okd).sum())
            if nu >= 10 and na >= 10:
                testable += 1
                details.append(f"{tsd[m].min().date()}→{tsd[m].max().date()} (ÜST={nu},ALT={na})")
        print(f"  düşüş eşiği {thr:>4}%: toplam epizot={len(set(brk)):2d}  "
              f"HEM ÜST HEM ALT ≥10 gün olan (test edilebilir) = {testable}")
        for x in details:
            print(f"      {x}")

    print("\n═════ 3) KAPSAM/EV TAKASI — yıllık R cinsinden (11 yıl, TP2.0 ve TP3.0) ═════")
    n_years = 10.17    # 2016-05 → 2026-07
    for tp_a, sl_a in ((2.0, 1.0), (3.0, 1.0)):
        r2, w2, o2 = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        rows = []
        for name in ["G00 kapı YOK", "G01 fiyat>EMA200", "G02 EMA200 EĞİMİ>0",
                     "G10 gerç.vol yüzdelik<0.8", "G11 gerç.vol yüzdelik<0.6",
                     "G14 ATR yüzdelik 0.2-0.8", "G24 Pzt-Per", "G20 VIX<20"]:
            m = ok & gates[name]
            m22g = m & (yr == 2022)
            rows.append(dict(kapi=name, kapsam=round(m.sum()/ok.sum(), 3),
                             ev=round(float(r2[m].mean()), 4),
                             toplamR=round(float(r2[m].sum()), 1),
                             yillikR=round(float(r2[m].sum())/n_years, 1),
                             R_2022=round(float(r2[m22g].sum()), 1) if m22g.sum() else 0.0,
                             en_kotu_yil_R=round(min(float(r2[m & (yr == y)].sum())
                                                     for y in range(2016, 2027)), 1)))
        df = pd.DataFrame(rows)
        base = df[df.kapi == "G00 kapı YOK"].iloc[0]
        df["yillikR_farki"] = (df.yillikR - base.yillikR).round(1)
        df["R2022_farki"] = (df.R_2022 - base.R_2022).round(1)
        print(f"\n  ── TP{tp_a}/SL{sl_a} ──")
        print(df.to_string(index=False))

    print("\n═════ 4) İDDİANIN TERSİ: 2022'de EMA200 ALTI long GERÇEKTEN kazandırdı mı? ═════")
    above1 = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
    for tp_a, sl_a in ((2.0, 1.0), (3.0, 1.0), (1.5, 1.0)):
        r3, w3, o3 = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        m = m22 & ~above1
        print(f"  TP{tp_a}/SL{sl_a}: 2022 EMA200 ALTI  n={m.sum()} gün={len(np.unique(day_idx[m]))} "
              f"EV={r3[m].mean():+.4f}  toplamR={r3[m].sum():+.1f}  WR={w3[m].mean():.3f}")
    print("  → EV NEGATİF. 'Ayı rallisi long kazandırdı' DEĞİL; sadece 'daha az kaybettirdi'.")


if __name__ == "__main__":
    main()
