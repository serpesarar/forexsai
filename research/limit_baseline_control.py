#!/usr/bin/env python3
"""limit_baseline_control.py — KONTROL: '1 ATR tepkiye satış' kırmızı muma mı bağlı?
Aynı limit mekaniği (a) büyük kırmızı mum + teyit sonrası, (b) KOŞULSUZ her barda,
(c) teyitsiz (yalnız büyük kırmızı mum) uygulanır. Taban eşitse koşul bilgisizdir."""
from datetime import datetime, timezone
import numpy as np
import lab_vol_tpsl_grid as G

H, LOT, SP = 72, 5.0, 1.5
t, o, h, l, c, v = G.load_csv("nas100_m5.csv")
n = len(c)
atr = G.wilder_atr(h, l, c)
cut = t[int(n * 0.7)]


def limit(e, L, expiry, tp_d, sl_d, sp=SP):
    fill = None
    for j in range(e + 1, min(e + expiry, n - 1) + 1):
        if h[j] >= L:
            fill = j; break
    if fill is None:
        return None
    tp_px, sl_px = L - tp_d, L + sl_d
    end = min(fill + H, n - 1)
    for j in range(fill, end + 1):
        if h[j] >= sl_px - sp:
            return "LOSS", L - sl_px
        if l[j] <= tp_px - sp:
            return "WIN", L - tp_px
    return "TIME", L - c[end] - sp


def gather(kind):
    out = []
    for i in range(G.ATR_PERIOD + 5, n - H - 30):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        if kind == "taban":
            if i % 6 == 0:
                out.append((i, a))
            continue
        body = o[i] - c[i]; rng_ = h[i] - l[i]
        if rng_ <= 0 or body <= 0 or body < a or body / rng_ < 0.55:
            continue
        if kind == "teyitli" and not (c[i + 1] < l[i]):
            continue
        out.append((i, a))
    return out


def show(rows, sig, label):
    if not rows:
        print(f"  {label:<40} —"); return
    net = np.asarray([r[1] for r in rows], float)
    print(f"  {label:<40}{sig:>7}{100.0 * len(rows) / sig:>8.1f}"
          f"{100.0 * sum(1 for r in rows if r[0] == 'WIN') / len(rows):>7.1f}"
          f"{net.mean():>+10.2f}{net.sum() / sig:>+11.2f}{net.sum() * LOT:>+11,.0f}")


print("=" * 108)
print("KONTROL — '+1.00×ATR tepkiye SELL limit / 12 bar geçerli / TP80 SL30' üç popülasyonda")
print("=" * 108)
print(f"  {'popülasyon':<40}{'sinyal':>7}{'dolum%':>8}{'TP%':>7}{'EV/işlem':>10}{'EV/sinyal':>11}{'$':>11}")
sets = {}
for kind, label in (("teyitli", "büyük kırmızı mum + teyit (kurgu)"),
                    ("teyitsiz", "yalnız büyük kırmızı mum"),
                    ("taban", "KOŞULSUZ her 6. bar (TABAN)")):
    evs = gather(kind)
    sets[kind] = evs
    for tag, want in (("TÜMÜ  ", None), ("EĞİTİM", True), ("TEST  ", False)):
        sub = [(i, a) for i, a in evs if want is None or (t[i] < cut) == want]
        rows = [r for r in (limit(i + 1, c[i + 1] + 1.00 * a, 12, 80.0, 30.0)
                            for i, a in sub) if r]
        show(rows, len(sub), f"{tag} {label}")
    print()

print("AYNI KONTROL, TP120/SL25 ile")
print(f"  {'popülasyon':<40}{'sinyal':>7}{'dolum%':>8}{'TP%':>7}{'EV/işlem':>10}{'EV/sinyal':>11}{'$':>11}")
for kind, label in (("teyitli", "kurgu"), ("taban", "TABAN")):
    for tag, want in (("EĞİTİM", True), ("TEST  ", False)):
        sub = [(i, a) for i, a in sets[kind] if (t[i] < cut) == want]
        rows = [r for r in (limit(i + 1, c[i + 1] + 1.00 * a, 12, 120.0, 25.0)
                            for i, a in sub) if r]
        show(rows, len(sub), f"{tag} {label}")

print("\nOFFSET TARAMASI — taban vs kurgu (TP80/SL30, 12 bar, TÜMÜ dönem)")
print(f"  {'offset':<12}{'| KURGU EV/sinyal':>18}{'TABAN EV/sinyal':>18}{'FARK':>10}")
for off in (0.25, 0.50, 0.75, 1.00, 1.25, 1.50):
    vals = {}
    for kind in ("teyitli", "taban"):
        sub = sets[kind]
        rows = [r for r in (limit(i + 1, c[i + 1] + off * a, 12, 80.0, 30.0)
                            for i, a in sub) if r]
        net = np.asarray([r[1] for r in rows], float) if rows else np.asarray([0.0])
        vals[kind] = net.sum() / max(1, len(sub))
    print(f"  +{off:.2f}×ATR{'':<3}{vals['teyitli']:>+18.2f}{vals['taban']:>+18.2f}"
          f"{vals['teyitli'] - vals['taban']:>+10.2f}")
