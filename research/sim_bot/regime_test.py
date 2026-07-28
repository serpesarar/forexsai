"""regime_test.py — varyantların FARKLI ZAMAN DİLİMLERİNDE dayanıklılığı.

sim2.py IN/OUT ikiye bölüyordu; burada veri ardışık HAFTALIK dilimlere
bölünüp her varyant her dilimde ayrı ölçülüyor. Soru: bir varyant yalnız
belli bir rejimde mi kazanıyor, yoksa dilimlerin çoğunda mı?

Karar ölçütü (ön-kayıtlı):
  * "kaç dilimde pozitif" → dayanıklılık
  * "işlem/gün" → kullanıcı kriteri (seyrekleşme istenmiyor)
  * ikisi birlikte: en çok dilimde pozitif VE işlem sayısını koruyan kazanır.

Sızıntı: dilimler kronolojik, her karar yalnız o ana kadarki barlarla
(sim2.run aynen kullanılıyor), eşik ayarı YOK — tüm dilimlerde aynı sabitler.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sim import _client, fetch_bars, fetch_signals, stats  # noqa: E402
from sim2 import Ctx2, run, SINCE  # noqa: E402

WEEK = 7 * 86400
SYMBOLS = ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]
MODES = [("A ham-market", "A"), ("B kapı-at", "B")]


def weekly_slices(sigs):
    if not sigs:
        return []
    ss = sorted(sigs, key=lambda x: x["ts"])
    t0, t1 = ss[0]["ts"], ss[-1]["ts"]
    out, start = [], t0
    while start < t1:
        end = start + WEEK
        chunk = [s for s in ss if start <= s["ts"] < end]
        if len(chunk) >= 20:
            label = datetime.fromtimestamp(start, timezone.utc).strftime("%m-%d")
            out.append((label, chunk))
        start = end
    return out


def main():
    client = _client()
    print("HAFTALIK DİLİM DAYANIKLILIĞI — eşik ayarı yok, tüm dilimlerde aynı sabitler")
    print("Hücre: toplam R (işlem sayısı)\n")

    grand = defaultdict(lambda: {"pos": 0, "tot": 0, "R": 0.0, "n": 0, "days": 0.0})

    for symbol in SYMBOLS:
        b1 = fetch_bars(client, symbol, "1m", SINCE)
        b5 = fetch_bars(client, symbol, "5m", SINCE)
        b1h = fetch_bars(client, symbol, "1h", SINCE)
        sigs = fetch_signals(client, symbol, SINCE)
        if len(b1) < 1000 or not sigs:
            continue
        ctx = Ctx2(b1, b5, b1h)
        for direction in ("BUY", "SELL"):
            dsigs = [s for s in sigs if s["dir"] == direction]
            slices = weekly_slices(dsigs)
            if len(slices) < 3:
                continue
            print(f"\n── {symbol} {direction} ({len(slices)} hafta) ──")
            header = "varyant".ljust(20) + "".join(f"{lb:>13}" for lb, _ in slices)
            print(header + f"{'poz.hafta':>11}{'toplam':>9}{'işl/gün':>9}")
            for label, mode in MODES:
                cells, totR, totN, pos = [], 0.0, 0, 0
                for lb, chunk in slices:
                    tr, _ = run(symbol, direction, chunk, ctx, mode)
                    st = stats(tr)
                    cells.append(f"{st['totR']:+.1f}({st['n']})" if st["n"] else "—")
                    totR += st["totR"]
                    totN += st["n"]
                    if st["totR"] > 0:
                        pos += 1
                days = len(slices) * 7
                print(label.ljust(20) + "".join(f"{c:>13}" for c in cells)
                      + f"{pos}/{len(slices):>10}{totR:>+9.1f}{totN / days:>9.2f}")
                g = grand[label]
                g["pos"] += pos
                g["tot"] += len(slices)
                g["R"] += totR
                g["n"] += totN
                g["days"] += days

    print(f"\n\n{'═' * 70}\nGENEL TOPLAM (tüm sembol-yön-hafta)\n{'═' * 70}")
    print(f"{'varyant':<20}{'pozitif hafta':>16}{'toplam R':>11}{'işlem/gün':>12}")
    for label, _ in MODES:
        g = grand[label]
        if not g["tot"]:
            continue
        print(f"{label:<20}{g['pos']}/{g['tot']:<13}{g['R']:>+11.1f}"
              f"{g['n'] / max(1, g['days']):>12.2f}")


if __name__ == "__main__":
    main()
