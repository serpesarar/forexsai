#!/usr/bin/env python3
"""limit_entry_lab.py — MARKET yerine LIMIT emirle giriş: icra maliyetini sıfırlamak
kenarı anlamlı hale getiriyor mu?

Kurgu: büyük kırmızı 5m mum (i) + teyit mumu (i+1). Karar teyit mumunun kapanışında,
ama market'ten KOVALAMAK yerine kapanışın ÜSTÜNE (short için daha iyi fiyat) SELL LIMIT
bırakılır. Emir X bar içinde dolmazsa iptal.

Ölçülen iki ayrı sayı (ikisi de gerekli):
  * dolan işlem başına EV  → fiyat avantajı ne kadar?
  * SİNYAL başına EV       → dolmayanlar 0 sayılır; portföy gerçeği bu.
Market girişi her zaman dolduğu için karşılaştırma yalnız 'sinyal başına'da adil.

Doluş modeli (konservatif): sell-limit, sonraki barın HIGH'ı limit fiyata değerse dolar.
Dolduğu barda SL de görüldüyse KAYIP sayılır (aynı bar belirsizliği aleyhte çözülür).
"""
from datetime import datetime, timezone
import numpy as np
import lab_vol_tpsl_grid as G

SPREAD = 1.5
H = 72
CONFIRM = "lowbreak"
GEOS = ((80, 30), (120, 25), (80, 110))
EXPIRIES = (3, 6, 12)


def build_events(c, o, h, l, v, t, atr, vmean, n, confirm):
    ev = []
    for i in range(G.VOL_WINDOW + G.ATR_PERIOD + 2, n - H - 20):
        a = atr[i]
        if not np.isfinite(a) or a <= 0 or not np.isfinite(vmean[i]) or vmean[i] <= 0:
            continue
        body = o[i] - c[i]; rng_ = h[i] - l[i]
        if rng_ <= 0 or body <= 0 or body < a or body / rng_ < 0.55:
            continue
        if confirm == "red" and not (c[i + 1] < o[i + 1]):
            continue
        if confirm == "lowbreak" and not (c[i + 1] < l[i]):
            continue
        ev.append(i)
    return ev


def sim_from(fill_idx, fill_px, tp, sl, h, l, c, n, horizon=H):
    """fill barından İTİBAREN (dahil) çöz. Dönen: (net_puan, sonuç)."""
    tp_px = fill_px - tp; sl_px = fill_px + sl
    end = min(fill_idx + horizon, n - 1)
    for j in range(fill_idx, end + 1):
        hit_sl = h[j] >= sl_px - SPREAD
        hit_tp = l[j] <= tp_px - SPREAD
        if hit_sl and hit_tp:
            return fill_px - sl_px, "LOSS"
        if hit_sl:
            return fill_px - sl_px, "LOSS"
        if hit_tp:
            return fill_px - tp_px, "WIN"
    return fill_px - c[end] - SPREAD, "TIME"


def main():
    t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
    n = len(c)
    atr = G.wilder_atr(h, l, c)
    vmean = np.full(n, np.nan)
    for i in range(G.VOL_WINDOW, n):
        vmean[i] = v[i - G.VOL_WINDOW:i].mean()
    cut = t[int(n * 0.7)]
    events = build_events(c, o, h, l, v, t, atr, vmean, n, CONFIRM)
    print("=" * 118)
    print(f"LIMIT EMİRLE GİRİŞ — NAS100 5m · teyit={CONFIRM} · n={len(events):,} sinyal · "
          f"spread {SPREAD}p · ufuk {H} bar")
    print("=" * 118)

    def limit_price(i, kind):
        e = i + 1
        a = atr[i]
        if kind.startswith("+"):
            return c[e] + float(kind[1:]) * a
        if kind == "kirmizi_%50":
            return (o[i] + c[i]) / 2.0
        if kind == "kirmizi_acilis":
            return o[i]
        if kind == "teyit_tepesi":
            return h[e]
        raise ValueError(kind)

    KINDS = ("+0.10", "+0.20", "+0.30", "+0.50", "kirmizi_%50", "kirmizi_acilis", "teyit_tepesi")

    for tp, sl in GEOS:
        print(f"\n▸ GEOMETRİ TP {tp} / SL {sl}")
        # market referansı
        rows = []
        for i in events:
            e = i + 1
            net, out = sim_from(e + 1, c[e], tp, sl, h, l, c, n)
            rows.append((t[i], net, out, True))
        arr = np.asarray([r[1] for r in rows])
        tr = np.asarray([r[0] < cut for r in rows])
        print(f"  {'giriş türü':<20}{'exp':>5}{'doluş%':>8}{'| DOLAN EV(p)':>15}"
              f"{'| SİNYAL EV(p)':>15}{'eğitim':>9}{'test':>9}{'$ (5 lot)':>12}")
        print(f"  {'MARKET (referans)':<20}{'-':>5}{100.0:>8.1f}{arr.mean():>15.2f}"
              f"{arr.mean():>15.2f}{arr[tr].mean():>9.2f}{arr[~tr].mean():>9.2f}"
              f"{arr.sum() * G.LOT:>12,.0f}")
        for kind in KINDS:
            for exp in EXPIRIES:
                nets, filled, ts_list = [], 0, []
                for i in events:
                    e = i + 1
                    lp = limit_price(i, kind)
                    if lp <= c[e]:                      # limit market'in altında → anlamsız
                        nets.append(0.0); ts_list.append(t[i]); continue
                    fill_j = None
                    for j in range(e + 1, min(e + exp, n - 1) + 1):
                        if h[j] >= lp:
                            fill_j = j; break
                    if fill_j is None:
                        nets.append(0.0); ts_list.append(t[i]); continue
                    filled += 1
                    net, _out = sim_from(fill_j, lp, tp, sl, h, l, c, n)
                    nets.append(net); ts_list.append(t[i])
                nets = np.asarray(nets); ts_a = np.asarray(ts_list)
                if filled < 50:
                    continue
                fill_mask = nets != 0.0
                trm = ts_a < cut
                print(f"  {kind:<20}{exp:>5}{100.0 * filled / len(events):>8.1f}"
                      f"{nets[fill_mask].mean():>15.2f}{nets.mean():>15.2f}"
                      f"{nets[trm].mean():>9.2f}{nets[~trm].mean():>9.2f}"
                      f"{nets.sum() * G.LOT:>12,.0f}")


if __name__ == "__main__":
    main()
