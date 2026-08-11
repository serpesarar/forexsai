"""USOIL BREAKOUT — varyant taraması: geometri, GERİ-ÇEKİLME (retest) girişi, gecikmeli giriş.

lab.py taban ölçümü: market girişi + TP=SL=1×ATR → WR %43.8, −0.125R/işlem (spread dahil).
Bu betik "fiyat tepedeyken alma" sorununa üç yapısal alternatifi aynı olay evreninde,
aynı dürüst M1 çözümlemesiyle karşılaştırır:

  A) market girişi + farklı TP/SL geometrileri (±kazananı-koştur)
  B) GERİ-ÇEKİLME LİMİTİ: kırılım seviyesine (level + k×ATR) limit emri, N bar geçerli
  C) GECİKMELİ market girişi: kırılımdan N bar sonra (fakeout dedektöründeki +1 bar fikri)

Sızıntı: tüm kararlar kapalı bar bilgisiyle; limit dolumu M1 bid barlarıyla
(BUY limit P → ask≤P, yani bid ≤ P−spread); TP/SL yarışı doldurulan fiyattan.
"""
from __future__ import annotations

import itertools
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from usoil_breakout_lab import (CACHE, SERVER_UTC_OFFSET, MAX_HOLD_MIN, build_events,
                                fetch, get_spread, stat, wilson_low, DAYS)


def race(m1, k0: int, entry: float, tp: float, sl: float, unit: float,
         be_trail: bool, max_min: int = MAX_HOLD_MIN):
    """M1 bid barlarıyla TP/SL yarışı. Aynı barda ikisi de → konservatif KAYIP."""
    hi, lo = m1[k0:k0 + max_min, 2], m1[k0:k0 + max_min, 3]
    cur_sl, runner, peak = sl, False, entry
    for j in range(len(hi)):
        hit_sl = lo[j] <= cur_sl
        hit_tp = (not runner) and hi[j] >= tp
        if hit_sl:
            return (cur_sl - entry) / unit, j + 1
        if hit_tp:
            if not be_trail:
                return (tp - entry) / unit, j + 1
            runner = True
            cur_sl = max(cur_sl, tp - unit)
        if runner:
            peak = max(peak, hi[j])
            cur_sl = max(cur_sl, peak - unit)
    return None, None


def run_variant(ev, m1, spread, mode: str, tp_atr=1.0, sl_atr=1.0, be_trail=False,
                k_atr=0.0, expiry_bars=6, delay_bars=1):
    """mode: 'market' | 'retest' | 'delay'"""
    t1 = m1[:, 0]
    rows, seen, expired = [], 0, 0
    for e in ev:
        close_t = e["t"] + 300
        k = int(np.searchsorted(t1, close_t))
        if k >= len(t1) - 5 or t1[k] - close_t > 600:
            continue
        seen += 1
        unit = sl_atr * e["atr"]
        if mode == "market":
            k0, entry = k, m1[k, 1] + spread
        elif mode == "delay":
            k0 = k + delay_bars * 5
            if k0 >= len(t1) - 5 or t1[k0] - close_t > (delay_bars * 5 + 10) * 60:
                continue
            entry = m1[k0, 1] + spread
        else:                                   # retest limiti
            limit = e["level"] + k_atr * e["atr"]
            win = m1[k:k + expiry_bars * 5]
            fill = np.where(win[:, 3] <= limit - spread)[0]   # bid limit-spread'e değdi
            if not len(fill):
                expired += 1
                continue
            k0, entry = k + int(fill[0]), limit
        r = dict(e)
        r["entry"] = entry
        R, mins = race(m1, k0, entry, entry + tp_atr * e["atr"], entry - unit, unit, be_trail)
        if R is None:
            continue
        r["R"], r["win"], r["hold_min"] = R, 1 if R > 0 else 0, mins
        rows.append(r)
    return rows, seen, expired


def main():
    m5, m1 = fetch("M5", DAYS), fetch("M1", DAYS)
    spread = get_spread()
    ev = build_events(m5)
    print(f"olay={len(ev)}  spread={spread}", flush=True)

    print("\n=== A) MARKET GİRİŞİ — geometri ızgarası ===")
    print(f"  {'tp':>5}{'sl':>5}{'trail':>7}   sonuç")
    best_a = []
    for tp, sl, tr in itertools.product((0.75, 1.0, 1.5, 2.0, 3.0), (0.75, 1.0, 1.5), (False, True)):
        rows, _, _ = run_variant(ev, m1, spread, "market", tp, sl, tr)
        if not rows:
            continue
        best_a.append((np.mean([r["R"] for r in rows]), tp, sl, tr, rows))
        print(f"  {tp:>5}{sl:>5}{str(tr):>7}   {stat(rows)}")

    print("\n=== B) GERİ-ÇEKİLME LİMİTİ (seviyeye dönüşte al) ===")
    print(f"  {'k×ATR':>7}{'geçerli':>8}{'tp':>5}{'sl':>5}{'trail':>7}{'dolum%':>8}   sonuç")
    best_b = []
    for k_atr, exp_b, (tp, sl), tr in itertools.product(
            (-0.25, -0.1, 0.0, 0.1), (3, 6, 12), ((1.0, 1.0), (1.5, 1.0), (2.0, 1.0)), (False, True)):
        rows, seen, exp_n = run_variant(ev, m1, spread, "retest", tp, sl, tr,
                                        k_atr=k_atr, expiry_bars=exp_b)
        if len(rows) < 40:
            continue
        fill = 100 * len(rows) / max(seen, 1)
        best_b.append((np.mean([r["R"] for r in rows]), k_atr, exp_b, tp, sl, tr, rows))
        print(f"  {k_atr:>7.2f}{exp_b:>8}{tp:>5}{sl:>5}{str(tr):>7}{fill:>7.1f}%   {stat(rows)}")

    print("\n=== C) GECİKMELİ MARKET GİRİŞİ ===")
    for d, (tp, sl), tr in itertools.product((1, 2, 3), ((1.0, 1.0), (1.5, 1.0)), (False, True)):
        rows, _, _ = run_variant(ev, m1, spread, "delay", tp, sl, tr, delay_bars=d)
        if rows:
            print(f"  +{d} bar  tp{tp}/sl{sl} trail={str(tr):<5}   {stat(rows)}")

    # en iyi varyantları kronolojik yarıya böl (kararlılık kontrolü)
    print("\n=== KARARLILIK: en iyi varyantların ilk yarı / ikinci yarı ===")
    named = ([(f"A tp{t}/sl{s} trail={tr}", m, rows) for m, t, s, tr, rows in best_a] +
             [(f"B k={k:+.2f} exp={e} tp{t}/sl{s} trail={tr}", m, rows)
              for m, k, e, t, s, tr, rows in best_b])
    for name, m, rows in sorted(named, key=lambda x: -x[1])[:6]:
        rows = sorted(rows, key=lambda r: r["t"])
        h = len(rows) // 2
        print(f"  {name:<40}\n      ilk yarı: {stat(rows[:h])}\n      son yarı: {stat(rows[h:])}")

    json.dump({"a": [[round(x[0], 4), x[1], x[2], x[3]] for x in best_a],
               "b": [[round(x[0], 4), x[1], x[2], x[3], x[4], x[5]] for x in best_b]},
              open(CACHE / "lab2_summary.json", "w"), indent=1)
    print("\nBITTI")


if __name__ == "__main__":
    main()
