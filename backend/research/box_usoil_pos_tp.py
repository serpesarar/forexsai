"""box_usoil_pos_tp.py — USOIL BUY: konum kapisi ESIGI + TP geometrisi derin sinamasi.

box_usoil_v3_oos.py sonucu: v3 raporunun iki filtresinden
  * F1 (ATR14/ATR60) 17 ayda TAMAMEN DUZ (%58.7-59.9, hangi esik olursa olsun) -> GURULTU
  * F2 (4s dalga konumu) GERCEK: pos<=0.85 -> islem basi +11.0$ -> +39.5$ (n=1037)
Ama F2'nin SIKI hali botta ZATEN CANLI: POS_BUY_MAX=0.60 (2026-07-28).

Bu script acik kalan iki soruyu kapatir:
  1) ESIK: 0.60 cok mu siki? 0.60-0.85 bandi kendi basina +EV mi?
     (kronolojik iki yari, bootstrap, surtunme stresi ile)
  2) TP: raporun "TP=0.6R" sampiyonu derin orneklemde botun 1.04%/1.49%
     geometrisini geciyor mu?

Yontem box_usoil_v3_oos.py ile ayni: botun gercek USOIL:BUY momentum kosullari
bar-bar, sizintisiz; giris = sinyal barinin KAPANISI + spread, cozum SONRAKI
barlardan; ayni barda TP+SL -> muhafazakar KAYIP.

Calistirma (kutuda): python backend/research/box_usoil_pos_tp.py
"""
from __future__ import annotations

import argparse
import random
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok — bu script MT5 kutusunda calisir.")

import config  # type: ignore
from box_usoil_v3_oos import (  # type: ignore
    SYM, LOT, CONTRACT, SL_PCT, TP_PCT, s2u, connect, bars, atr_of, ema_series,
    stoch_k, sar_last, stats, wilson,
)

random.seed(20260821)
POS_GRID = [0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
RR_GRID = [0.40, 0.60, 0.70, 0.80, 1.00, 1.25, 1.50, 2.00]


def scan(b5, b30, t30, b1h, t1h, cooldown_min=60):
    """Botun USOIL:BUY momentum kosullarini saglayan bar indekslerini + konumu dondur."""
    out = []
    son = None
    c30 = [x["c"] for x in b30]
    ema20_30 = ema_series(c30, 20) if c30 else []
    for i in range(300, len(b5)):
        t = b5[i]["t"]
        if son is not None and (t - son) < cooldown_min * 60:
            continue
        j = bisect_right(t30, t) - 1
        if j < 60:
            continue
        if t30[j] + 1800 > t:
            j -= 1
            if j < 60:
                continue
        seg30 = b30[j - 29:j + 1]
        k = stoch_k(seg30, 14)
        a30 = atr_of(seg30[-15:])
        if k is None or not a30 or not (k > 70.0):
            continue
        if not ((seg30[-1]["c"] - ema20_30[j]) / a30 > 0.8):
            continue
        h = bisect_right(t1h, t) - 1
        if h < 60:
            continue
        if t1h[h] + 3600 > t:
            h -= 1
            if h < 60:
                continue
        seg1h = b1h[max(0, h - 199):h + 1]
        a1h = atr_of(seg1h[-15:])
        if not a1h or not ((seg1h[-1]["c"] - sar_last(seg1h)) / a1h > 0.0):
            continue
        w48 = b5[i - 47:i + 1]          # son 4 saat, giris bari DAHIL edilmez:
        w48 = b5[i - 48:i]              # (yalniz kapanmis onceki barlar)
        hi, lo = max(x["h"] for x in w48), min(x["l"] for x in w48)
        px = b5[i - 1]["c"]
        out.append({"i": i, "t": t, "utc": s2u(t),
                    "pos": (px - lo) / (hi - lo) if hi > lo else 0.5})
        son = t
    return out


def resolve(b5, sig, spread, rr=None, tp_pct=TP_PCT, sl_pct=SL_PCT):
    i = sig["i"]
    entry = b5[i]["c"] + spread
    sl_d = entry * sl_pct / 100.0
    tp_d = rr * sl_d if rr else entry * tp_pct / 100.0
    tp, sl = entry + tp_d, entry - sl_d
    for x in b5[i + 1:i + 1200]:
        if x["l"] <= sl:
            return {"pnl": -sl_d * LOT * CONTRACT, "win": False, "utc": sig["utc"],
                    "pos": sig["pos"]}
        if x["h"] >= tp:
            return {"pnl": tp_d * LOT * CONTRACT, "win": True, "utc": sig["utc"],
                    "pos": sig["pos"]}
    return None


def per(rows):
    n, wr, net = stats(rows)
    return f"n={n:<5} WR=%{wr:5.1f} net={net:>+9.0f}$ islem_basi={net/n if n else 0:>+7.1f}$"


def bootstrap_pos(vals, reps=3000):
    if not vals:
        return 0.0
    n = len(vals)
    hits = 0
    for _ in range(reps):
        hits += int(sum(vals[random.randrange(n)] for _ in range(n)) > 0)
    return 100.0 * hits / reps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spread", type=float, default=0.03)
    a = ap.parse_args()
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)
    b5, t5 = bars(mt5.TIMEFRAME_M5, 99000)
    b30, t30 = bars(mt5.TIMEFRAME_M30, 40000)
    b1h, t1h = bars(mt5.TIMEFRAME_H1, 20000)
    if not b5:
        sys.exit("bar yok")
    sig = scan(b5, b30, t30, b1h, t1h)
    print(f"{SYM}: 5m={len(b5)} · sinyal={len(sig)} "
          f"({sig[0]['utc']:%Y-%m-%d} -> {sig[-1]['utc']:%Y-%m-%d})")
    be = 100 / (1 + TP_PCT / SL_PCT)
    print(f"geometri TP {TP_PCT}%/SL {SL_PCT}% (RR {TP_PCT/SL_PCT:.2f}, basabas %{be:.1f}) "
          f"· spread {a.spread}\n")

    base = [r for r in (resolve(b5, s, a.spread) for s in sig) if r]
    print("=" * 88)
    print("1) KONUM ESIGI — kumulatif (pos <= X) ve BANT bazinda")
    print("=" * 88)
    print(f"  {'KOSULSUZ':<22} {per(base)}")
    prev = None
    for th in POS_GRID:
        sel = [r for r in base if r["pos"] <= th]
        band = [r for r in base if (prev is None or r["pos"] > prev) and r["pos"] <= th]
        print(f"  pos<={th:.2f} kumulatif   {per(sel)}")
        if prev is not None:
            print(f"     └ BANT ({prev:.2f},{th:.2f}]  {per(band)}")
        prev = th

    print("\n" + "=" * 88)
    print("2) CANLI KAPININ (0.60) BLOKLADIGI BANT: (0.60, 0.85]  — gevsetme adayi")
    print("=" * 88)
    band = [r for r in base if 0.60 < r["pos"] <= 0.85]
    print(f"  {'bant':<22} {per(band)}  (basabas %{be:.1f})")
    k = sum(1 for r in band if r["win"])
    lo, hi = wilson(k, len(band))
    print(f"  Wilson %95: [{lo:.1f}, {hi:.1f}]  ·  bootstrap P(EV>0)=%"
          f"{bootstrap_pos([r['pnl'] for r in band]):.1f}")
    srt = sorted(band, key=lambda r: r["utc"])
    h = len(srt) // 2
    for lbl, part in (("ilk yari", srt[:h]), ("ikinci yari", srt[h:])):
        print(f"  {lbl:<22} {per(part)}")
    print("  ── surtunme stresi (spread x1.5 ve x2) ──")
    for mult in (1.5, 2.0):
        rows = [r for r in (resolve(b5, s, a.spread * mult) for s in sig)
                if r and 0.60 < r["pos"] <= 0.85]
        print(f"  spread x{mult:<20.1f} {per(rows)}")
    print("  ── ustundeki bant (0.85, 1.00] — kapinin GERCEKTEN kesmesi gereken yer ──")
    print(f"  {'':<22} {per([r for r in base if r['pos'] > 0.85])}")

    print("\n" + "=" * 88)
    print("3) 1B PLASEBO — konum esigi aramasi (sonuclar karistirilir)")
    print("=" * 88)
    cells = []
    for th in POS_GRID:
        idx = [i for i, r in enumerate(base) if r["pos"] <= th]
        if len(idx) >= 100:
            cells.append(idx)
    pay = [r["pnl"] for r in base]
    best = lambda p: max(sum(p[i] for i in idx) for idx in cells)
    obs = best(pay)
    hits = 0
    for _ in range(2000):
        random.shuffle(pay)
        hits += int(best(pay) >= obs)
    print(f"  en iyi kumulatif hucre {obs:+.0f}$ · duzeltilmis p={hits/2000:.4f} "
          f"{'ANLAMLI' if hits/2000 < 0.05 else 'GURULTU'}")

    print("\n" + "=" * 88)
    print("4) TP GEOMETRISI — raporun 'TP=0.6R' sampiyonu derin orneklemde")
    print("=" * 88)
    print(f"  {'referans (TP 1.04%)':<24} {per(base)}")
    for rr in RR_GRID:
        rows = [r for r in (resolve(b5, s, a.spread, rr=rr) for s in sig) if r]
        bb = 100 / (1 + rr)
        print(f"  TP={rr:.2f}R (basabas %{bb:4.1f})   {per(rows)}")
    print("\n  ── ayni izgara, YALNIZ pos<=0.85 kumesinde ──")
    keep = [s for s in sig]
    for rr in (0.6, 1.0, 1.5):
        rows = [r for r in (resolve(b5, s, a.spread, rr=rr) for s in keep)
                if r and r["pos"] <= 0.85]
        print(f"  TP={rr:.2f}R  {per(rows)}")

    print("\n" + "=" * 88)
    print("5) YILLIK/AYLIK KARARLILIK — pos<=0.85 vs pos<=0.60 vs kosulsuz")
    print("=" * 88)
    ay = defaultdict(list)
    for r in base:
        ay[f"{r['utc']:%Y-%m}"].append(r)
    for key in sorted(ay):
        g = ay[key]
        n0, w0, p0 = stats(g)
        g6 = [r for r in g if r["pos"] <= 0.60]
        g85 = [r for r in g if r["pos"] <= 0.85]
        n6, w6, p6 = stats(g6)
        n8, w8, p8 = stats(g85)
        print(f"  {key}  kosulsuz n={n0:<4}{p0:>+8.0f}$ | <=0.60 n={n6:<3}{p6:>+8.0f}$ "
              f"| <=0.85 n={n8:<4}{p8:>+8.0f}$")

    mt5.shutdown()


if __name__ == "__main__":
    main()
