"""audit_D5_placebo.py — PLASEBO + ÇOKLU-TEST DÜZELTMESİ.

Soru 1: "9/11 veya 10/11 yıl pozitif" bulgusu anlamlı mı, yoksa taban zaten
        8/11 olduğu için kapsamı yüksek HERHANGİ bir kapı bunu verir mi?
Soru 2: G10 (gerç.vol yüzdelik<0.8) 2022'yi +EV yapan TEK kapı. 124 test içinde
        bir tanesinin bunu yapması şans mı?
Soru 3: 2022'de "EMA200 üstü" alt kümesinin EV'si -0.35; AYNI KAPSAMDA (2022'nin
        %11.6'sı) rastgele seçilmiş gün kümeleri ne veriyor?

Plasebo tasarımı: GÜN düzeyinde DAİRESEL KAYDIRMA. Kapsamı ve seri-uzunluk
(persistence) yapısını BİREBİR korur, piyasa koşullarıyla hizayı bozar.
Ham karıştırma (iid gün) kullanılmaz — rejim kapıları kalıcıdır, iid plasebo
fazla kolay yenilir ve yanlış anlamlılık üretir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from audit_common import build, r_series
from audit_D4_gates import gate_library, MIN_BARS_YEAR

GEOMS = [(2.0, 1.0), (3.0, 1.0)]
N_ROT = 600


def day_level(gate: np.ndarray, day_idx: np.ndarray, n_days: int) -> np.ndarray:
    """Kapıyı gün düzeyine indir (günün çoğunluğu)."""
    s = np.zeros(n_days); c = np.zeros(n_days)
    np.add.at(s, day_idx, gate.astype(float)); np.add.at(c, day_idx, 1.0)
    return (s / np.maximum(c, 1)) > 0.5


def main() -> None:
    pd.set_option("display.width", 250)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"])
    year = ts.year.to_numpy()
    days, day_idx = np.unique(ts.normalize().to_numpy(), return_inverse=True)
    n_days = len(days)
    day_year = pd.DatetimeIndex(days).year.to_numpy()
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    years = list(range(2016, 2027))
    gates = gate_library(d)
    rng = np.random.default_rng(2022)

    def score(r, mask):
        pos = trd = 0
        ev22 = np.nan
        for y in years:
            m = mask & (year == y)
            if m.sum() < MIN_BARS_YEAR:
                continue
            v = float(r[m].mean()); trd += 1; pos += int(v > 0)
            if y == 2022:
                ev22 = v
        return pos, trd, ev22

    for tp_a, sl_a in GEOMS:
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        print(f"\n════════════ TP{tp_a}/SL{sl_a} ════════════")
        base_pos, base_trd, base22 = score(r, ok)
        print(f"  TABAN (kapı yok): poz_yıl {base_pos}/{base_trd}, EV2022={base22:+.4f}, "
              f"EV={r[ok].mean():+.4f}")

        print("\n  ── Plasebo: gün düzeyinde dairesel kaydırma (kapsam+persistence korunur) ──")
        rows = []
        for name in ["G01 fiyat>EMA200", "G02 EMA200 EĞİMİ>0", "G10 gerç.vol yüzdelik<0.8",
                     "G11 gerç.vol yüzdelik<0.6", "G20 VIX<20", "G24 Pzt-Per"]:
            gm = gates[name]
            dl = day_level(gm, day_idx, n_days)
            real_mask = ok & gm
            r_pos, r_trd, r_ev22 = score(r, real_mask)
            # null dağılım
            null_pos, null_ev22 = [], []
            offs = rng.choice(np.arange(20, n_days - 20), size=min(N_ROT, n_days - 40), replace=False)
            for off in offs:
                rot_dl = np.roll(dl, off)
                rot = ok & rot_dl[day_idx]
                if rot.sum() < 500:
                    continue
                p, t, e22 = score(r, rot)
                null_pos.append(p / max(t, 1))
                if np.isfinite(e22):
                    null_ev22.append(e22)
            null_pos = np.array(null_pos); null_ev22 = np.array(null_ev22)
            p_pos = float((null_pos >= r_pos / max(r_trd, 1)).mean())
            p_ev22 = float((null_ev22 >= r_ev22).mean()) if np.isfinite(r_ev22) and len(null_ev22) else np.nan
            rows.append(dict(kapi=name, kapsam=round(real_mask.sum()/ok.sum(), 3),
                             poz=f"{r_pos}/{r_trd}",
                             plasebo_poz_ort=round(float(null_pos.mean()), 3),
                             p_poz=round(p_pos, 3),
                             ev2022=round(r_ev22, 4) if np.isfinite(r_ev22) else None,
                             plasebo_ev2022_ort=round(float(null_ev22.mean()), 4) if len(null_ev22) else None,
                             plasebo_ev2022_p5=round(float(np.percentile(null_ev22, 5)), 4) if len(null_ev22) else None,
                             plasebo_ev2022_p95=round(float(np.percentile(null_ev22, 95)), 4) if len(null_ev22) else None,
                             p_ev2022=round(p_ev22, 3) if np.isfinite(p_ev22) else None))
        print(pd.DataFrame(rows).to_string(index=False))

        print("\n  ── 2022 içi: EMA200-üstü'nün EV'si, AYNI KAPSAMDA rastgele günlere karşı ──")
        m22 = ok & (year == 2022)
        above = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
        real22 = m22 & above
        n_target_days = len(np.unique(day_idx[real22]))
        d22 = np.unique(day_idx[m22])
        # 2022'nin 258 gününden 30'unu rastgele seç (blok yapısını da dene)
        sims_iid, sims_blk = [], []
        for _ in range(4000):
            pick = rng.choice(d22, size=n_target_days, replace=False)
            sel = m22 & np.isin(day_idx, pick)
            sims_iid.append(float(r[sel].mean()))
        # blok versiyonu: 5 küme (gerçek epizot sayısı), her biri ardışık ~6 gün
        for _ in range(4000):
            picks = []
            for _k in range(5):
                st = rng.integers(0, len(d22) - 6)
                picks.extend(d22[st:st + 6])
            sel = m22 & np.isin(day_idx, np.unique(picks))
            sims_blk.append(float(r[sel].mean()))
        sims_iid = np.array(sims_iid); sims_blk = np.array(sims_blk)
        obs = float(r[real22].mean())
        print(f"    GERÇEK (EMA200 üstü, {n_target_days} gün): EV={obs:+.4f}")
        print(f"    plasebo IID-gün  : ort={sims_iid.mean():+.4f}  %5={np.percentile(sims_iid,5):+.4f}  "
              f"%95={np.percentile(sims_iid,95):+.4f}  P(plasebo<=gerçek)={float((sims_iid<=obs).mean()):.4f}")
        print(f"    plasebo 5-BLOK   : ort={sims_blk.mean():+.4f}  %5={np.percentile(sims_blk,5):+.4f}  "
              f"%95={np.percentile(sims_blk,95):+.4f}  P(plasebo<=gerçek)={float((sims_blk<=obs).mean()):.4f}")
        print("    → 5-BLOK plasebo dürüst olan (gerçek kapı 5 epizota yığılmış).")

    print("\n════════════ ÇOKLU-TEST: 124 kombinasyonda 'en iyi'nin şansı ════════════")
    r, win, opn = r_series(d, cmax, cmin, end_ret, 2.0, 1.0)
    m22 = ok & (year == 2022)
    # G10'un 2022'de +EV olması: aynı kapsamda rastgele kapılardan 124 tanesinin
    # EN İYİSİ ne kadar 2022-EV verir?
    g10 = gates["G10 gerç.vol yüzdelik<0.8"]
    dl = day_level(g10, day_idx, n_days)
    best_of_k = []
    for _ in range(400):
        vals = []
        for _k in range(31):     # kapı kütüphanesi büyüklüğü
            off = rng.integers(20, n_days - 20)
            rot = ok & np.roll(dl, off)[day_idx] & (year == 2022)
            if rot.sum() >= MIN_BARS_YEAR:
                vals.append(float(r[rot].mean()))
        if vals:
            best_of_k.append(max(vals))
    best_of_k = np.array(best_of_k)
    obs_g10 = float(r[ok & g10 & (year == 2022)].mean())
    print(f"  G10 gerçek EV2022 = {obs_g10:+.4f}")
    print(f"  31 RASTGELE kapının EN İYİSİNİN EV2022'si: ort={best_of_k.mean():+.4f} "
          f"%50={np.percentile(best_of_k,50):+.4f} %95={np.percentile(best_of_k,95):+.4f}")
    print(f"  P(rastgele en-iyi >= G10) = {float((best_of_k >= obs_g10).mean()):.3f}")


if __name__ == "__main__":
    main()
