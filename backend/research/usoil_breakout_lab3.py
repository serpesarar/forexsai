"""USOIL BREAKOUT — karar turu: ÖN-TANIMLI kapılar, MTF hizası, bootstrap, canlı mutabakat.

lab.py + lab2.py sonucu: market girişi TP=SL=1×ATR → −0.125R/işlem; 30 geometri
varyantının hepsi negatif; geri-çekilme limiti ve gecikmeli giriş de kurtarmıyor.
Bu betik kararı sağlamlaştırır:

  1) CANLI MUTABAKAT — 2026-08-06→bugün simülasyon vs kutunun gerçek 19 işlemi.
  2) ÖN-TANIMLI kapılar (mining DEĞİL — daha önceki otopsilerden gelen kurallar):
       · USOIL seans bloğu 00–11 UTC (analiz_paketi_2026-07-09 §5)
       · aşırı-uzama freni: overshoot ≤ 0.5×ATR ("tepeden alma")
       · 1h trend hizası (EMA50 üstü) — NDX TREND_ALIGN_GATE'in USOIL karşılığı
       · bunların birleşimi
  3) BOOTSTRAP — taban ve en iyi kapının ortalama R'si için %95 aralık + P(EV>0).
  4) SIRA-BAĞIMLI ("as-traded") simülasyon: aynı anda tek pozisyon.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np

from usoil_breakout_lab import (DAYS, SERVER_UTC_OFFSET, build_events, fetch,
                                get_spread, stat)
from usoil_breakout_lab2 import race

RNG = np.random.default_rng(7)


def ema_np(x, span):
    k = 2.0 / (span + 1)
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = x[i] * k + out[i - 1] * (1 - k)
    return out


def add_mtf(ev, m5):
    """1h EMA50/EMA200 hizası (5m barlardan saatlik seri, sızıntısız: kapalı saat)."""
    t, c = m5[:, 0], m5[:, 4]
    hour_id = (t // 3600).astype(np.int64)
    idx_last = {}
    for i, hid in enumerate(hour_id):
        idx_last[hid] = i                       # o saatin son 5m barı
    hours = sorted(idx_last)
    hc = np.array([c[idx_last[h]] for h in hours])
    e50, e200 = ema_np(hc, 50), ema_np(hc, 200)
    pos = {h: j for j, h in enumerate(hours)}
    for e in ev:
        hid = int(e["t"] // 3600) - 1           # KAPALI önceki saat
        j = pos.get(hid)
        e["h1_above_e50"] = float(hc[j] > e50[j]) if j and j > 200 else np.nan
        e["h1_above_e200"] = float(hc[j] > e200[j]) if j and j > 200 else np.nan
    return ev


def sim(ev, m1, spread, tp_atr=1.0, sl_atr=1.0, be_trail=False):
    t1 = m1[:, 0]
    out = []
    for e in ev:
        k = int(np.searchsorted(t1, e["t"] + 300))
        if k >= len(t1) - 5 or t1[k] - (e["t"] + 300) > 600:
            continue
        entry = m1[k, 1] + spread
        unit = sl_atr * e["atr"]
        R, mins = race(m1, k, entry, entry + tp_atr * e["atr"], entry - unit, unit, be_trail)
        if R is None:
            continue
        r = dict(e); r["entry"] = entry; r["R"] = R
        r["win"] = 1 if R > 0 else 0; r["hold_min"] = mins
        r["k_entry"] = k
        out.append(r)
    return out


def boot(rows, n=5000):
    x = np.array([r["R"] for r in rows])
    if len(x) < 20:
        return (np.nan, np.nan, np.nan)
    m = RNG.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m > 0).mean())


def show(name, rows, base_n):
    lo, hi, p = boot(rows)
    print(f"  {name:<42} {stat(rows):<46} kaps=%{100*len(rows)/base_n:4.1f}"
          f"  R95=[{lo:+.3f},{hi:+.3f}] P(EV>0)=%{100*p:.1f}")


def main():
    m5, m1 = fetch("M5", DAYS), fetch("M1", DAYS)
    spread = get_spread()
    ev = add_mtf(build_events(m5), m5)
    base = sim(ev, m1, spread)
    n0 = len(base)
    print(f"spread={spread}  çözülen olay={n0}\n")

    # ── 1) canlı mutabakat ──────────────────────────────────────────────────
    live_start = datetime(2026, 8, 6).timestamp() + SERVER_UTC_OFFSET * 3600
    liv = [r for r in base if r["t"] >= live_start]
    print("[1] CANLI MUTABAKAT (2026-08-06 →)")
    print(f"  simülasyon : {stat(liv)}")
    print("  gerçek MT5 : n=  19 WR= 26.3% (5K/14Z)  net=-895.0$  (magic 52890974)")
    print("  → simülatör canlıyı doğru yakalıyorsa ikisi de belirgin negatif olmalı\n")

    # ── 2) ön-tanımlı kapılar ───────────────────────────────────────────────
    print("[2] ÖN-TANIMLI KAPILAR (mining değil — önceki otopsilerden)")
    show("TABAN (bugünkü canlı kural)", base, n0)
    gates = {
        "seans: 12–23 UTC (00–11 blok)": lambda r: not (0 <= r["hour_utc"] < 12),
        "uzama freni: overshoot ≤ 0.50": lambda r: r["overshoot"] <= 0.50,
        "uzama freni: overshoot ≤ 0.30": lambda r: r["overshoot"] <= 0.30,
        "1h trend: EMA50 üstü": lambda r: r.get("h1_above_e50") == 1.0,
        "1h trend: EMA200 üstü": lambda r: r.get("h1_above_e200") == 1.0,
        "dar kanal: don_width ≤ 6.7": lambda r: r["don_width"] <= 6.7,
        "gün-içi tepe değil: day_pos ≤ 0.97": lambda r: r["day_pos"] <= 0.97,
        "ADX 18–35": lambda r: 18 <= r["adx"] <= 35,
    }
    for name, f in gates.items():
        show(name, [r for r in base if f(r)], n0)
    combo = [r for r in base if (not (0 <= r["hour_utc"] < 12)) and r["overshoot"] <= 0.50
             and r.get("h1_above_e50") == 1.0]
    show("BİRLEŞİK (seans + uzama + 1h trend)", combo, n0)
    combo2 = [r for r in combo if r["don_width"] <= 6.7]
    show("BİRLEŞİK + dar kanal", combo2, n0)

    # koştur yönetimiyle aynı birleşik kapı
    ev_combo = [e for e in ev if (not (0 <= e["hour_utc"] < 12)) and e["overshoot"] <= 0.50
                and e.get("h1_above_e50") == 1.0]
    for tp, tr in ((1.0, True), (1.5, True), (2.0, True)):
        show(f"BİRLEŞİK + tp{tp} koştur", sim(ev_combo, m1, spread, tp, 1.0, tr), n0)

    # ── 3) kronolojik yarılar (kararlılık) ──────────────────────────────────
    print("\n[3] KRONOLOJİK YARILAR")
    for name, rows in (("TABAN", base), ("BİRLEŞİK", combo)):
        rows = sorted(rows, key=lambda r: r["t"])
        h = len(rows) // 2
        if h < 15:
            continue
        print(f"  {name:<12} ilk: {stat(rows[:h])}   son: {stat(rows[h:])}")

    # ── 4) as-traded (aynı anda tek pozisyon) ───────────────────────────────
    print("\n[4] AS-TRADED (tek pozisyon kuralı, botun gerçek davranışı)")
    for name, rows in (("TABAN", base), ("BİRLEŞİK", combo)):
        rows = sorted(rows, key=lambda r: r["t"])
        taken, busy_until = [], -1
        for r in rows:
            if r["k_entry"] < busy_until:
                continue
            taken.append(r)
            busy_until = r["k_entry"] + r["hold_min"]
        print(f"  {name:<12} {stat(taken)}")

    print("\nBITTI")


if __name__ == "__main__":
    main()
