"""box_usoil_tp_stability.py — USOIL BUY hedef mesafesinin (RR) KARARLILIK sinamasi.

box_usoil_pos_tp.py bulgusu (n=2025, 17 ay, sizintisiz, spread'li):
    RR 0.40 -> -2.3$/islem · 0.60 -> +9.3 · 0.70 (BOTUN MEVCUDU) -> +11.2
    RR 1.00 -> +34.0 · 1.25 -> +30.4 · 1.50 -> +32.2 · 2.00 -> +29.1
Yani raporun "TP=0.6R" sampiyonu derin orneklemde botun mevcut ayarindan bile
KOTU; asil kazanc ters yonde — hedefi UZATMAKTA. Bu iddia canliya dokunacagi
icin go_live_gate olcutleriyle sinanir:

  1 hacim >=150      2 P(EV>0)>=%90     3 kronolojik IKI yari da >=0
  4 surtunme x1.5    5 icra gercekci    6 ayni anda tek pozisyon kisiti

Calistirma (kutuda): python backend/research/box_usoil_tp_stability.py
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok.")

from box_usoil_v3_oos import SYM, connect, bars, stats  # type: ignore
from box_usoil_pos_tp import scan, resolve, per, bootstrap_pos  # type: ignore

random.seed(20260822)
RRS = [0.60, 0.70, 0.80, 1.00, 1.25, 1.50, 2.00]


def sequential(rows_by_i, b5, spread, rr, sl_pct=1.49):
    """6. olcut: 'ayni anda tek pozisyon' — onceki islem kapanmadan yenisi acilmaz."""
    out = []
    busy_until = -1
    for s in rows_by_i:
        if s["i"] <= busy_until:
            continue
        i = s["i"]
        entry = b5[i]["c"] + spread
        sl_d = entry * sl_pct / 100.0
        tp_d = rr * sl_d
        tp, sl = entry + tp_d, entry - sl_d
        for off, x in enumerate(b5[i + 1:i + 1200]):
            if x["l"] <= sl:
                out.append({"pnl": -sl_d * 5.0 * 100.0, "win": False,
                            "utc": s["utc"], "pos": s["pos"]})
                busy_until = i + 1 + off
                break
            if x["h"] >= tp:
                out.append({"pnl": tp_d * 5.0 * 100.0, "win": True,
                            "utc": s["utc"], "pos": s["pos"]})
                busy_until = i + 1 + off
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spread", type=float, default=0.03)
    a = ap.parse_args()
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)
    b5, _ = bars(mt5.TIMEFRAME_M5, 99000)
    b30, t30 = bars(mt5.TIMEFRAME_M30, 40000)
    b1h, t1h = bars(mt5.TIMEFRAME_H1, 20000)
    sig = scan(b5, b30, t30, b1h, t1h)
    print(f"{SYM}: sinyal={len(sig)} ({sig[0]['utc']:%Y-%m-%d} -> {sig[-1]['utc']:%Y-%m-%d})")
    print(f"spread {a.spread} · SL sabit %1.49\n")

    print("=" * 96)
    print("KARARLILIK — her RR icin kronolojik yarilar, bootstrap, surtunme, sirali kisit")
    print("=" * 96)
    print(f"{'RR':<6}{'n':>6}{'WR':>8}{'islem_basi':>12}{'1.yari':>10}{'2.yari':>10}"
          f"{'P(EV>0)':>9}{'x1.5':>9}{'sirali':>18}")
    for rr in RRS:
        rows = [r for r in (resolve(b5, s, a.spread, rr=rr) for s in sig) if r]
        n, wr, net = stats(rows)
        srt = sorted(rows, key=lambda r: r["utc"])
        h = len(srt) // 2
        n1, _, p1 = stats(srt[:h])
        n2, _, p2 = stats(srt[h:])
        pev = bootstrap_pos([r["pnl"] for r in rows], reps=2000)
        rows15 = [r for r in (resolve(b5, s, a.spread * 1.5, rr=rr) for s in sig) if r]
        n15, _, net15 = stats(rows15)
        seq = sequential(sig, b5, a.spread, rr)
        ns, ws, nets = stats(seq)
        print(f"{rr:<6.2f}{n:>6}{wr:>7.1f}%{net/n:>11.1f}${p1/max(1,n1):>9.1f}$"
              f"{p2/max(1,n2):>9.1f}${pev:>8.1f}%{net15/max(1,n15):>8.1f}$"
              f"{f'n={ns} {ws:.0f}% {nets/max(1,ns):+.1f}$':>18}")

    print("\n" + "=" * 96)
    print("AYLIK — mevcut RR 0.70 vs aday RR 1.00 (islem basi $)")
    print("=" * 96)
    r07 = [r for r in (resolve(b5, s, a.spread, rr=0.70) for s in sig) if r]
    r10 = [r for r in (resolve(b5, s, a.spread, rr=1.00) for s in sig) if r]
    g7, g10 = defaultdict(list), defaultdict(list)
    for r in r07:
        g7[f"{r['utc']:%Y-%m}"].append(r)
    for r in r10:
        g10[f"{r['utc']:%Y-%m}"].append(r)
    kotu = 0
    for k in sorted(g7):
        n7, w7, p7 = stats(g7[k])
        n1, w1, p1 = stats(g10[k])
        e7, e1 = p7 / max(1, n7), p1 / max(1, n1)
        mark = "" if e1 >= e7 else "  <- RR1.0 daha kotu"
        kotu += int(e1 < e7)
        print(f"  {k}  n={n7:<4} RR0.70 {e7:>+8.1f}$  |  RR1.00 {e1:>+8.1f}${mark}")
    print(f"\n  RR1.00'in RR0.70'i gectigi ay: {len(g7)-kotu}/{len(g7)}")

    print("\n" + "=" * 96)
    print("KONUM KAPISI ALTINDA (canli davranis: pos<=0.60) RR karsilastirmasi")
    print("=" * 96)
    for rr in RRS:
        rows = [r for r in (resolve(b5, s, a.spread, rr=rr) for s in sig)
                if r and r["pos"] <= 0.60]
        print(f"  RR={rr:<5.2f} {per(rows)}")

    mt5.shutdown()


if __name__ == "__main__":
    main()
