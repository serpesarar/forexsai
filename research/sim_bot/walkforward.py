"""walkforward.py — sim.py bulgularının SIZINTISIZ doğrulaması.

İki soru:
  1. trend+konum kombinasyonu OUT-OF-SAMPLE'da da tutuyor mu?
     (kronolojik %60 IN / %40 OUT — eşik IN'de seçilir, OUT'ta test edilir)
  2. Konum eşiği parametreye ne kadar duyarlı? (düz mü, tek nokta mı?)

Sızıntı: split kronolojik (karıştırma yok); OUT diliminin verisi eşik
seçimine ASLA girmez; her karar yine yalnız o ana kadarki barlarla.
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sim import (_client, fetch_bars, fetch_signals, Ctx, simulate, stats,  # noqa: E402
                 GEOM)

SINCE = "2026-06-01T00:00:00+00:00"
SPLIT = 0.60
SYMBOLS = ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"]


def split_sigs(sigs, frac=SPLIT):
    ss = sorted(sigs, key=lambda x: x["ts"])
    if not ss:
        return [], []
    cut = ss[int(len(ss) * frac)]["ts"]
    return [s for s in ss if s["ts"] < cut], [s for s in ss if s["ts"] >= cut]


def fmt(s):
    return "n=0" if not s["n"] else \
        f"n={s['n']:>3} WR=%{s['wr']:<5} totR={s['totR']:>+7.2f} avgR={s['avgR']:>+.3f}"


def main():
    client = _client()
    print("KRONOLOJİK %60 IN-SAMPLE / %40 OUT-OF-SAMPLE\n"
          "(eşikler yalnız IN'de bakılır; OUT hiç görülmeden test edilir)\n")

    for symbol in SYMBOLS:
        b1 = fetch_bars(client, symbol, "1m", SINCE)
        b5 = fetch_bars(client, symbol, "5m", SINCE)
        b1h = fetch_bars(client, symbol, "1h", SINCE)
        sigs = fetch_signals(client, symbol, SINCE)
        if len(b1) < 1000 or not sigs:
            continue
        ctx = Ctx(b1, b5, b1h)
        ins, outs = split_sigs(sigs)
        print(f"\n{'═' * 76}\n{symbol}  (IN {len(ins)} sinyal / OUT {len(outs)} sinyal)\n{'═' * 76}")

        for direction in ("BUY", "SELL"):
            if sum(1 for s in sigs if s["dir"] == direction) < 40:
                continue
            print(f"\n── {direction} ──")
            print(f"{'varyant':<22}{'IN-SAMPLE':<42}{'OUT-OF-SAMPLE'}")
            for label, gates in [
                ("baseline", {}),
                ("trend", {"trend": True}),
                ("konum", {"position": True}),
                ("trend+konum", {"trend": True, "position": True}),
                ("trend+konum+sabır", {"trend": True, "position": True, "patience": True}),
            ]:
                si = stats(simulate(symbol, direction, ins, ctx, gates)[0])
                so = stats(simulate(symbol, direction, outs, ctx, gates)[0])
                print(f"{label:<22}{fmt(si):<42}{fmt(so)}")

    # ── Eşik duyarlılığı (yalnız IN dilimde — OUT'a bakılmaz) ────────────
    print(f"\n\n{'═' * 76}\nKONUM EŞİĞİ DUYARLILIĞI (IN-SAMPLE, trend kapısı açık)\n{'═' * 76}")
    for symbol in SYMBOLS:
        b1 = fetch_bars(client, symbol, "1m", SINCE)
        b5 = fetch_bars(client, symbol, "5m", SINCE)
        b1h = fetch_bars(client, symbol, "1h", SINCE)
        sigs = fetch_signals(client, symbol, SINCE)
        if len(b1) < 1000 or not sigs:
            continue
        ctx = Ctx(b1, b5, b1h)
        ins, _ = split_sigs(sigs)
        for direction in ("BUY", "SELL"):
            if sum(1 for s in ins if s["dir"] == direction) < 30:
                continue
            row = []
            for thr in (0.0, 0.3, 0.4, 0.5, 0.6, 0.7):
                g = {"trend": True, "position": True,
                     "pos_sell_min": thr, "pos_buy_max": 1 - thr}
                s = stats(simulate(symbol, direction, ins, ctx, g)[0])
                row.append(f"{thr:.1f}:{s['totR']:+.1f}({s['n']})" if s["n"] else f"{thr:.1f}:—")
            print(f"  {symbol:<13}{direction:<5} " + "  ".join(row))


if __name__ == "__main__":
    main()
