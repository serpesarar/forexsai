#!/usr/bin/env python3
"""indicator_snapshots boşluk doldurucu — MT5 kutusunda elle çalışır.

Kaydedici yeniden başladığında derin backfill OHLC'yi tamamlar ama göstergeyi
poll başına RECORDER_MAX_IND_PER_POLL ile sınırlar; aradaki barların göstergesi
hiç yazılmaz. Bu araç eksik barları canlı kaydediciyle aynı pencereyle (son
HIST_BARS bar) hesaplar ve YALNIZ eksik satırları ekler; var olan satıra ve
candle_cache'e dokunmaz.

Varsayılan kuru koşudur: mevcut satırları yeniden hesaplayıp kıyaslar, hiçbir
şey yazmaz. Yazmak için --apply.

⚠️ --since broker DST geçişinden ÖNCEYE gitmemeli: MT5 geçmiş barları kendi
döneminin sunucu saatinde tutar, tek offset o barları yanlış damgalar.

    python scripts/backfill_indicators.py --since 2026-11-02T00:00
    python scripts/backfill_indicators.py --since 2026-11-02T00:00 --apply
"""
from __future__ import annotations

import argparse
import logging
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RECORDER_DIR = Path(__file__).resolve().parent.parent / "yeni deneme"
os.chdir(RECORDER_DIR)  # data_recorder log dosyasını ve config'i buradan bulur
sys.path.insert(0, str(RECORDER_DIR))

import config  # noqa: E402
import data_recorder as dr  # noqa: E402
from indicators import compute_all  # noqa: E402

mt5 = dr.mt5
logging.getLogger("httpx").setLevel(logging.WARNING)

TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}
PAGE_SIZE = 1000
SAFETY_BARS = 50
FRESH_MARGIN_MIN = 10   # bu kadar yeni barlar canlı kaydedicinin işi
MATCH_REL_TOL = 1e-6


def existing_rows(client, symbol: str, tf: str, since: datetime) -> dict:
    """candle_time → {close, ind}; sayfalı okur."""
    rows: dict = {}
    start = 0
    while True:
        res = (client.table("indicator_snapshots").select("candle_time,close,ind")
               .eq("symbol", symbol).eq("timeframe", tf)
               .gte("candle_time", since.isoformat()).order("candle_time")
               .range(start, start + PAGE_SIZE - 1).execute())
        for r in res.data:
            rows[datetime.fromisoformat(r["candle_time"])] = r
        if len(res.data) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=MATCH_REL_TOL, abs_tol=MATCH_REL_TOL)
    return a == b


def json_safe(ind: dict) -> dict:
    """Yeniden hesap ile DB'deki JSON aynı biçimde kıyaslansın."""
    return {k: (None if isinstance(v, float) and not math.isfinite(v) else v)
            for k, v in ind.items()}


def process(client, fx: str, mt5_sym: str, tf: str, since: datetime, until: datetime,
            apply: bool) -> None:
    count = int((datetime.now(timezone.utc) - since).total_seconds() / TF_SECONDS[tf])
    rates = mt5.copy_rates_from_pos(mt5_sym, dr.TF_MAP[tf], 1,
                                    count + dr.HIST_BARS + SAFETY_BARS)
    if rates is None or len(rates) < dr.HIST_BARS:
        print(f"{fx} {tf}: MT5 yetersiz bar, atlandı")
        return
    o = [float(r["open"]) for r in rates]
    h = [float(r["high"]) for r in rates]
    l = [float(r["low"]) for r in rates]
    c = [float(r["close"]) for r in rates]
    v = [float(r["tick_volume"]) for r in rates]
    t = [int(r["time"]) for r in rates]
    have = existing_rows(client, fx, tf, since)

    missing, compared, close_bad, ind_bad, short, bad_key = [], 0, 0, 0, 0, None
    in_window = 0
    for i in range(len(t)):
        stamp = dr._iso(t[i])
        ts = datetime.fromisoformat(stamp)
        if ts < since or ts >= until:
            continue
        in_window += 1
        if i + 1 < dr.HIST_BARS:
            short += 1
            continue
        lo = i + 1 - dr.HIST_BARS  # canlı kaydedicinin penceresi: son HIST_BARS bar
        row = have.get(ts)
        if row is None:
            missing.append({"symbol": fx, "timeframe": tf, "candle_time": stamp,
                            "open": o[i], "high": h[i], "low": l[i], "close": c[i],
                            "volume": v[i],
                            "ind": compute_all(o[lo:i + 1], h[lo:i + 1], l[lo:i + 1],
                                               c[lo:i + 1], v[lo:i + 1])})
            continue
        compared += 1
        if not same(row["close"], c[i]):
            close_bad += 1
        fresh = json_safe(compute_all(o[lo:i + 1], h[lo:i + 1], l[lo:i + 1],
                                      c[lo:i + 1], v[lo:i + 1]))
        diff = [k for k in fresh if not same(fresh[k], row["ind"].get(k))]
        if diff:
            ind_bad += 1
            bad_key = bad_key or diff[:4]

    span = (f"{missing[0]['candle_time'][:16]}→{missing[-1]['candle_time'][:16]}"
            if missing else "-")
    print(f"{fx:12s} {tf:3s} pencere={in_window} var={len(have)} eksik={len(missing)} "
          f"kisa={short} kiyas={compared} close_farki={close_bad} ind_farki={ind_bad} "
          f"ornek={bad_key} eksik_aralik={span}", flush=True)
    if apply and missing:
        dr._upsert_indicators(client, fx, tf, missing)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", required=True, help="UTC başlangıç, ör. 2026-11-02T00:00")
    ap.add_argument("--tfs", default="1m,5m,15m,30m,1h")
    ap.add_argument("--apply", action="store_true", help="eksik satırları yaz")
    args = ap.parse_args()

    since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
    until = datetime.now(timezone.utc) - timedelta(minutes=FRESH_MARGIN_MIN)
    # Yalnız açık terminale bağlan: hesap değiştirme riski olan login yapılmaz
    ok = (mt5.initialize(config.MT5_TERMINAL_PATH) if config.MT5_TERMINAL_PATH
          else mt5.initialize())
    if not ok:
        print("mt5.initialize başarısız:", mt5.last_error())
        return 1
    try:
        offset = dr.detect_server_offset()
        if offset is None:
            print("sunucu offset'i ölçülemedi, yazılmadı")
            return 2
        dr._SERVER_OFFSET_SEC = offset
        print(f"hesap={mt5.account_info().login} offset={offset / 3600:+.0f}s "
              f"{'YAZMA' if args.apply else 'KURU KOŞU'} {since.isoformat()} → {until.isoformat()}")
        client = dr.supa()
        for fx, mt5_sym in config.RECORDER_SYMBOLS.items():
            for tf in args.tfs.split(","):
                process(client, fx, mt5_sym, tf, since, until, args.apply)
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
