#!/usr/bin/env python3
"""horizon_probe.py — sıkı-stop ailesinin ZAMAN-STOPU hassasiyeti + sonuç dağılımı.
Kenar yalnız 72 barlık ufukta varsa kırılgandır; her ufukta duruyorsa gerçektir."""
import numpy as np
import lab_vol_tpsl_grid as G
import lab_tight_stop as T

t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
n = len(c)
atr = G.wilder_atr(h, l, c)
vmean = np.full(n, np.nan)
for i in range(G.VOL_WINDOW, n):
    vmean[i] = v[i - G.VOL_WINDOW:i].mean()
cut = t[int(n * 0.7)]

print("=" * 104)
print("ZAMAN-STOPU (UFUK) HASSASİYETİ — teyit=lowbreak, giriş 2. mumun kapanışı, spread 1.5")
print("=" * 104)
print(f"  {'ufuk':<10}{'geometri':<12}{'n':>7}{'TP%':>7}{'SL%':>7}{'ZAMAN%':>8}"
      f"{'EĞİTİM EV(R)':>14}{'TEST EV(R)':>12}{'TÜMÜ EV(R)':>12}{'$ tümü':>11}")
for H in (12, 24, 36, 48, 72, 96):
    G.HORIZON = H
    book, vol1 = T.build(c, o, h, l, v, t, atr, vmean, n, "lowbreak", H)
    tr_i = np.where(book.ts < cut)[0]; te_i = np.where(book.ts >= cut)[0]
    all_i = np.arange(len(book.ts))
    for tp, sl in ((80, 30), (120, 25), (80, 110)):
        G.SPREAD = 1.5
        tp_d = np.full(len(all_i), float(tp)); sl_d = np.full(len(all_i), float(sl))
        net, risk, win, loss = book.evaluate(all_i, tp_d, sl_d)
        a_ = T.ev(book, tr_i, tp, sl, 1.5); b_ = T.ev(book, te_i, tp, sl, 1.5)
        f_ = T.ev(book, all_i, tp, sl, 1.5)
        time_pct = 100.0 * float((~win & ~loss).mean())
        print(f"  {H:<10}{f'{tp}/{sl}':<12}{len(all_i):>7}{100 * win.mean():>7.1f}"
              f"{100 * loss.mean():>7.1f}{time_pct:>8.1f}"
              f"{a_['ev_r']:>+14.3f}{b_['ev_r']:>+12.3f}{f_['ev_r']:>+12.3f}{f_['usd']:>+11,.0f}")

# kazanan/kaybeden anatomisi (H=72, 80/30)
G.HORIZON = 72
book, vol1 = T.build(c, o, h, l, v, t, atr, vmean, n, "lowbreak", 72)
all_i = np.arange(len(book.ts))
G.SPREAD = 1.5
tp_d = np.full(len(all_i), 80.0); sl_d = np.full(len(all_i), 30.0)
net, risk, win, loss = book.evaluate(all_i, tp_d, sl_d)
timeo = ~win & ~loss
print("\nSONUÇ ANATOMİSİ (TP 80 / SL 30, ufuk 72):")
print(f"  TP  : %{100 * win.mean():.1f}  ortalama +{net[win].mean():.1f} p")
print(f"  SL  : %{100 * loss.mean():.1f}  ortalama {net[loss].mean():.1f} p")
print(f"  ZAMAN: %{100 * timeo.mean():.1f}  ortalama {net[timeo].mean():+.1f} p "
      f"(zaman çıkışlarının %{100 * (net[timeo] > 0).mean():.0f}'i kârda)")
print(f"  toplam beklenti: {net.mean():+.2f} p/işlem · başabaş TP oranı %{100 * 30 / 110:.1f}")
print(f"  → kenar TP oranından DEĞİL, {2.67:.2f}:1 risk-getiri + zaman çıkışlarından geliyor")

print("\nYÜKSEK-WR ALTERNATİFLERİ (kullanıcı 'yüksek başarı oranı' istedi) — kâr ediyorlar mı?")
print(f"  {'TP/SL':<10}{'n':>7}{'TP%':>8}{'başabaş%':>10}{'fark':>8}{'EV(R)':>9}{'EV(p)':>9}{'$':>11}")
for tp, sl in ((20, 80), (25, 60), (30, 50), (40, 50), (50, 50), (30, 30), (80, 30), (120, 25)):
    r = T.ev(book, all_i, tp, sl, 1.5)
    be = 100.0 * sl / (tp + sl)
    print(f"  {f'{tp}/{sl}':<10}{r['n']:>7}{r['tp_rate']:>8.1f}{be:>10.1f}"
          f"{r['tp_rate'] - be:>+8.1f}{r['ev_r']:>+9.3f}{r['ev_p']:>+9.2f}{r['usd']:>+11,.0f}")
