#!/usr/bin/env python3
"""tight_stop_probe.py — 'sıkı stop + uzak hedef' ailesinin sağlamlık bataryası.

Grid taramasında tek hayatta kalan aday: büyük düşüş mumundan sonraki mumda SELL,
TP 80 / SL 30 puan. Bu dosya onu KIRMAYA çalışır: SL hassasiyeti, kayma (spread
3-5 puan), çeyreklik istikrar, taban farkı ve giriş varyantı duyarlılığı.
Kırılmazsa gölgeye alınmaya değer; kırılırsa çöpe.
"""
from datetime import datetime, timezone
import numpy as np
import lab_vol_tpsl_grid as G

TPS = (50, 60, 70, 80, 90, 100, 120, 150)
SLS = (20, 25, 30, 35, 40, 50, 60)
CONFIRMS = ("none", "red", "lowbreak")


def build(c, o, h, l, v, t, atr, vmean, n, confirm, H):
    idx_list = []
    for i in range(G.VOL_WINDOW + G.ATR_PERIOD + 2, n - H - 3):
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
        idx_list.append(i)
    m = len(idx_list)
    entry = np.empty(m); atr_e = np.empty(m); ts = np.empty(m, dtype=np.int64)
    LO = np.empty((m, H)); HI = np.empty((m, H)); ce = np.empty(m)
    vol1 = np.empty(m)
    for k, i in enumerate(idx_list):
        e = i + 1
        entry[k] = c[e]; atr_e[k] = atr[i]; ts[k] = t[i]; vol1[k] = v[i] / vmean[i]
        LO[k] = np.minimum.accumulate(l[e + 1:e + 1 + H])
        HI[k] = np.maximum.accumulate(h[e + 1:e + 1 + H])
        ce[k] = c[e + H]
    return G.Book(entry, atr_e, ts, LO, HI, ce), vol1


def ev(book, idx, tp, sl, spread):
    G.SPREAD = spread
    if len(idx) < 25:
        return None
    tp_d = np.full(len(idx), float(tp)); sl_d = np.full(len(idx), float(sl))
    net, risk, win, loss = book.evaluate(idx, tp_d, sl_d)
    return G.cell_stats(net, risk, win, loss, tp_d, sl_d)


def main():
    t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
    n = len(c)
    atr = G.wilder_atr(h, l, c)
    vmean = np.full(n, np.nan)
    for i in range(G.VOL_WINDOW, n):
        vmean[i] = v[i - G.VOL_WINDOW:i].mean()
    H = G.HORIZON
    cut = t[int(n * 0.7)]

    # taban (koşulsuz SELL)
    bidx = [i for i in range(G.VOL_WINDOW + G.ATR_PERIOD + 2, n - H - 3, 6)
            if np.isfinite(atr[i]) and atr[i] > 0]
    bm = len(bidx)
    be = np.empty(bm); ba = np.empty(bm); bt = np.empty(bm, dtype=np.int64)
    bLO = np.empty((bm, H)); bHI = np.empty((bm, H)); bce = np.empty(bm)
    for k, i in enumerate(bidx):
        be[k] = c[i]; ba[k] = atr[i]; bt[k] = t[i]
        bLO[k] = np.minimum.accumulate(l[i + 1:i + 1 + H])
        bHI[k] = np.maximum.accumulate(h[i + 1:i + 1 + H])
        bce[k] = c[i + H]
    bbook = G.Book(be, ba, bt, bLO, bHI, bce)

    print("=" * 116)
    print("SIKI STOP + UZAK HEDEF — SAĞLAMLIK BATARYASI (NAS100 5m, giriş 2. mumun kapanışı)")
    print("=" * 116)

    for confirm in CONFIRMS:
        book, vol1 = build(c, o, h, l, v, t, atr, vmean, n, confirm, H)
        tr_i = np.where(book.ts < cut)[0]; te_i = np.where(book.ts >= cut)[0]
        rows = []
        for tp in TPS:
            for sl in SLS:
                a_ = ev(book, tr_i, tp, sl, 1.5); b_ = ev(book, te_i, tp, sl, 1.5)
                if not a_ or not b_ or a_["n"] < 150 or b_["n"] < 60:
                    continue
                rows.append((min(a_["ev_r"], b_["ev_r"]), tp, sl, a_, b_))
        rows.sort(reverse=True)
        print(f"\n▸ teyit={confirm}  (n={len(book.ts):,}; eğitim {len(tr_i)} / test {len(te_i)})"
              f"  — ikisinde de en iyi 5 hücre")
        print(f"  {'TP/SL':<10}{'| EĞİTİM TP%':>13}{'EV(R)':>8}{'EV(p)':>8}"
              f"{'| TEST TP%':>11}{'EV(R)':>8}{'EV(p)':>8}{'$':>10}")
        for _s, tp, sl, a_, b_ in rows[:5]:
            print(f"  {f'{tp}/{sl}':<10}{a_['tp_rate']:>13.1f}{a_['ev_r']:>+8.3f}{a_['ev_p']:>+8.2f}"
                  f"{b_['tp_rate']:>11.1f}{b_['ev_r']:>+8.3f}{b_['ev_p']:>+8.2f}{b_['usd']:>+10,.0f}")

    # ── odak: lowbreak + 80/30 ailesinin sağlamlığı ────────────────────────
    book, vol1 = build(c, o, h, l, v, t, atr, vmean, n, "lowbreak", H)
    tr_i = np.where(book.ts < cut)[0]; te_i = np.where(book.ts >= cut)[0]
    all_i = np.arange(len(book.ts))
    print("\n" + "=" * 116)
    print("ODAK: teyit=lowbreak · SL HASSASİYETİ (TP 80 sabit) — knife-edge mi?")
    print(f"  {'SL':<6}{'| EĞİTİM EV(R)':>16}{'TEST EV(R)':>13}{'TÜMÜ EV(R)':>13}{'TÜMÜ TP%':>11}{'$ (tümü)':>12}")
    for sl in (20, 25, 30, 35, 40, 50, 60):
        a_ = ev(book, tr_i, 80, sl, 1.5); b_ = ev(book, te_i, 80, sl, 1.5)
        f_ = ev(book, all_i, 80, sl, 1.5)
        print(f"  {sl:<6}{a_['ev_r']:>+16.3f}{b_['ev_r']:>+13.3f}{f_['ev_r']:>+13.3f}"
              f"{f_['tp_rate']:>11.1f}{f_['usd']:>+12,.0f}")

    print("\nKAYMA (SLIPPAGE) DAYANIKLILIĞI — spread/kayma büyüdükçe (30p stop dar!)")
    print(f"  {'spread':<8}{'| TP 80/SL 30 eğitim':>22}{'test':>10}{'tümü':>10}"
          f"{'| TP 80/SL 40 tümü':>20}")
    for sp in (1.5, 3.0, 5.0, 8.0):
        a_ = ev(book, tr_i, 80, 30, sp); b_ = ev(book, te_i, 80, 30, sp)
        f_ = ev(book, all_i, 80, 30, sp); g_ = ev(book, all_i, 80, 40, sp)
        print(f"  {sp:<8}{a_['ev_r']:>+22.3f}{b_['ev_r']:>+10.3f}{f_['ev_r']:>+10.3f}"
              f"{g_['ev_r']:>+20.3f}")

    print("\nÇEYREKLİK (TP 80 / SL 30, spread 1.5) — kenar her dönemde duruyor mu?")
    qs = {}
    G.SPREAD = 1.5
    tp_d = np.full(len(all_i), 80.0); sl_d = np.full(len(all_i), 30.0)
    net, risk, win, loss = book.evaluate(all_i, tp_d, sl_d)
    for k in all_i:
        d = datetime.fromtimestamp(int(book.ts[k]), tz=timezone.utc)
        qs.setdefault(f"{d.year}Ç{(d.month - 1) // 3 + 1}", []).append(k)
    print(f"  {'çeyrek':<10}{'n':>6}{'TP%':>8}{'EV(R)':>9}{'EV(p)':>9}{'$':>11}")
    for q in sorted(qs):
        sel = np.asarray(qs[q])
        rr = net[sel] / risk[sel]
        print(f"  {q:<10}{len(sel):>6}{100.0 * win[sel].mean():>8.1f}{rr.mean():>+9.3f}"
              f"{net[sel].mean():>+9.2f}{net[sel].sum() * G.LOT:>+11,.0f}")

    print("\nTABAN FARKI (koşulsuz SELL, aynı geometri)")
    bt_i = np.where(bbook.ts < cut)[0]; bte_i = np.where(bbook.ts >= cut)[0]
    ball = np.arange(len(bbook.ts))
    for tp, sl in ((80, 30), (80, 40), (80, 110)):
        s_tr = ev(book, tr_i, tp, sl, 1.5); s_te = ev(book, te_i, tp, sl, 1.5)
        s_all = ev(book, all_i, tp, sl, 1.5)
        b_tr = ev(bbook, bt_i, tp, sl, 1.5); b_te = ev(bbook, bte_i, tp, sl, 1.5)
        b_all = ev(bbook, ball, tp, sl, 1.5)
        print(f"  {tp}/{sl}: eğitim {s_tr['ev_r']:+.3f} vs taban {b_tr['ev_r']:+.3f} "
              f"(fark {s_tr['ev_r'] - b_tr['ev_r']:+.3f}) | "
              f"test {s_te['ev_r']:+.3f} vs {b_te['ev_r']:+.3f} "
              f"(fark {s_te['ev_r'] - b_te['ev_r']:+.3f}) | "
              f"tümü {s_all['ev_r']:+.3f} vs {b_all['ev_r']:+.3f} "
              f"(fark {s_all['ev_r'] - b_all['ev_r']:+.3f})")

    print("\nHACİM KOVASI (TP 80 / SL 30, tümü) — hacim gerçekten gerekli mi?")
    print(f"  {'kova':<24}{'n':>7}{'TP%':>8}{'EV(R)':>9}{'EV(p)':>9}{'$':>11}")
    for name, lo_b, hi_b in (("hepsi", 0.0, 99.0), ("<0.9× sakin", 0.0, 0.9),
                             ("0.9–1.2×", 0.9, 1.2), ("1.2–1.5×", 1.2, 1.5),
                             ("1.5–2.0×", 1.5, 2.0), ("≥2.0× patlama", 2.0, 99.0)):
        sel = np.where((vol1 >= lo_b) & (vol1 < hi_b))[0]
        r = ev(book, sel, 80, 30, 1.5)
        if r:
            print(f"  {name:<24}{r['n']:>7}{r['tp_rate']:>8.1f}{r['ev_r']:>+9.3f}"
                  f"{r['ev_p']:>+9.2f}{r['usd']:>+11,.0f}")


if __name__ == "__main__":
    main()
