"""box_usoil_posgate_hole.py — konum kapisi (POS_BUY_MAX=0.60) fiilen calisiyor mu?

Kapı 2026-07-28'de canliya alindi. Eger o tarihten SONRA acilmis USOIL MOM/SR
BUY islemleri arasinda konum>0.60 olanlar varsa, kapinin bir DELIGI vardir
(hangi yol kapiyi atliyor?). Konum, botun kendi olcumuyle ayni: son 48x5m
barin (giris bari haric) yuksek/dusuk araliginda giris fiyatinin yeri.

Calistirma (kutuda): python backend/research/box_usoil_posgate_hole.py
"""
from __future__ import annotations

import sys
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme"))

try:
    import MetaTrader5 as mt5  # type: ignore
except ImportError:
    sys.exit("HATA: MetaTrader5 yok.")

from box_usoil_v3_oos import (  # type: ignore
    SYM, MOM_MAGIC, connect, bars, load_positions, s2u,
)

GATE_LIVE = datetime(2026, 7, 28, tzinfo=timezone.utc)


def pos_at(t_srv: int, b5, t5) -> float | None:
    i = bisect_left(t5, t_srv)
    if i < 60:
        return None
    w = b5[i - 48:i]                     # giris bari DAHIL DEGIL
    hi, lo = max(x["h"] for x in w), min(x["l"] for x in w)
    return None if hi <= lo else (b5[i - 1]["c"] - lo) / (hi - lo)


def main():
    if not connect():
        sys.exit(f"mt5.initialize basarisiz: {mt5.last_error()}")
    mt5.symbol_select(SYM, True)
    b5, t5 = bars(mt5.TIMEFRAME_M5, 99000)
    pos = load_positions(datetime(2026, 1, 1, tzinfo=timezone.utc))
    live = [p for p in pos if p["magic"] == MOM_MAGIC and p["dir"] == "BUY"]
    print(f"MOM/SR BUY islem: {len(live)}  ·  kapı canli tarihi {GATE_LIVE:%Y-%m-%d}\n")
    print(f"{'tarih':<18}{'konum':>7}{'sonuc':>8}{'pnl':>10}  yorum")
    ihlal = []
    for p in live:
        pv = pos_at(p["t"], b5, t5)
        if pv is None:
            continue
        after = p["utc"] >= GATE_LIVE
        flag = ""
        if after and pv > 0.60:
            flag = "  <-- KAPI DELIGI (kapi sonrasi, konum>0.60)"
            ihlal.append((p, pv))
        if after or pv > 0.60:
            print(f"{p['utc']:%Y-%m-%d %H:%M}{pv:>7.2f}"
                  f"{'WIN' if p['win'] else 'LOSS':>8}{p['pnl']:>10.0f}$"
                  f"{'  [kapi oncesi]' if not after else ''}{flag}")
    print(f"\nkapı sonrasi konum>0.60 islem sayisi: {len(ihlal)}")
    if ihlal:
        net = sum(p["pnl"] for p, _ in ihlal)
        w = sum(1 for p, _ in ihlal if p["win"])
        print(f"  bunlarin karnesi: WR=%{100*w/len(ihlal):.1f}  net={net:+.0f}$")
    mt5.shutdown()


if __name__ == "__main__":
    main()
