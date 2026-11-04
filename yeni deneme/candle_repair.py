#!/usr/bin/env python3
"""candle_cache onarımı — doğru barları MT5'ten dönem kuralıyla yeniden kurar.

Vaka: analyst_reports/candle_cache_karisik_besleme_2026-11-04.md (Yahoo satırları +
60 dk kayma). Pencere içinde MT5 tek doğru kaynaktır:
  - MT5'te olup tabloda farklı/eksik olan bar yazılır,
  - tabloda olup MT5'te karşılığı olmayan satır (hayalet, Yahoo) silinir.
Değişecek her eski satır önce BACKUP_FILE'a (JSONL, kutuda) eklenir; yedek yazılamazsa
o parça değiştirilmez. Tekrar çalıştırmak güvenlidir.

Varsayılan kuru koşudur. Önce kaynak doğrulanır: MT5'ten kurulan seri son günlerde
indicator_snapshots ile uyuşmuyorsa yazmadan çıkılır.

    python candle_repair.py
    python candle_repair.py --apply
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
import data_recorder as dr
from broker_time import rule_matches_measured, rule_offset_sec

mt5 = dr.mt5
logging.getLogger("httpx").setLevel(logging.WARNING)

BACKUP_FILE = Path(__file__).parent / "candle_repair_backup_2026-11-04.jsonl"
SOURCE = "mt5_repair"
MAX_BARS = 99999
PAGE_SIZE = 1000
WRITE_CHUNK = 500
PRICE_TOLERANCE = 1e-6
#: Çok yeni barlar canlı kaydedicinin işi
FRESH_MARGIN_MIN = 10
#: Tablo penceresi: Yahoo gün-içi izinin en eski görüldüğü ay
WINDOW_START = datetime(2026, 5, 1, tzinfo=timezone.utc)
TIMEFRAMES = {"1m": mt5.TIMEFRAME_M1, "5m": mt5.TIMEFRAME_M5, "15m": mt5.TIMEFRAME_M15,
              "30m": mt5.TIMEFRAME_M30, "1h": mt5.TIMEFRAME_H1}
VALIDATE_DAYS = 5
VALIDATE_MIN_MATCH = 0.95
VALIDATE_MIN_ROWS = 100


def load_truth(mt5_symbol: str, tf_const: int, until: datetime) -> dict:
    rates = mt5.copy_rates_from_pos(mt5_symbol, tf_const, 1, MAX_BARS)
    truth = {}
    if rates is None:
        return truth
    for bar in rates:
        epoch = int(bar["time"]) - rule_offset_sec(int(bar["time"]))
        stamp = datetime.fromtimestamp(epoch, tz=timezone.utc)
        if WINDOW_START <= stamp < until:
            truth[stamp] = {"open": float(bar["open"]), "high": float(bar["high"]),
                            "low": float(bar["low"]), "close": float(bar["close"]),
                            "volume": float(bar["tick_volume"])}
    return truth


def fetch_rows(client, table: str, columns: str, symbol: str, tf: str,
               since: datetime, until: datetime) -> list:
    rows, last = [], since.isoformat()
    first = True
    while True:
        query = (client.table(table).select(columns).eq("symbol", symbol).eq("timeframe", tf)
                 .lt("candle_time", until.isoformat()))
        query = query.gte("candle_time", last) if first else query.gt("candle_time", last)
        batch = query.order("candle_time").limit(PAGE_SIZE).execute().data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return rows
        last, first = batch[-1]["candle_time"], False


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def validate_against_snapshots(client, fx: str, truth: dict, until: datetime) -> bool:
    since = until - timedelta(days=VALIDATE_DAYS)
    rows = fetch_rows(client, "indicator_snapshots", "candle_time,close", fx, "1m", since, until)
    matched = total = 0
    for row in rows:
        bar = truth.get(parse_time(row["candle_time"]))
        if bar is None:
            continue
        total += 1
        matched += abs(bar["close"] - float(row["close"])) <= PRICE_TOLERANCE
    ratio = matched / total if total else 0.0
    print(f"  doğrulama {fx}: MT5 kuralı ↔ snapshot {matched}/{total} = {ratio:.1%}")
    return total >= VALIDATE_MIN_ROWS and ratio >= VALIDATE_MIN_MATCH


def plan(existing: list, truth: dict, depth_start: datetime) -> tuple:
    updates, deletes, seen = [], [], set()
    for row in existing:
        stamp = parse_time(row["candle_time"])
        if stamp < depth_start:
            continue                    # MT5 derinliği yok: dokunma, raporda sayılır
        bar = truth.get(stamp)
        if bar is None:
            deletes.append(row)
            continue
        seen.add(stamp)
        if any(abs(bar[k] - float(row[k] or 0)) > PRICE_TOLERANCE for k in ("open", "high", "low", "close")):
            updates.append((row, stamp, bar))
    inserts = [(stamp, truth[stamp]) for stamp in truth if stamp not in seen]
    return updates, deletes, inserts


def backup(rows: list, action: str) -> None:
    with BACKUP_FILE.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({"action": action, **row}) + "\n")


def apply_changes(client, fx: str, tf: str, updates: list, deletes: list, inserts: list) -> None:
    backup([row for row, _, _ in updates], "update")
    backup(deletes, "delete")
    now = datetime.now(timezone.utc).isoformat()
    writes = [(stamp, bar) for _, stamp, bar in updates] + inserts
    rows = [{"symbol": fx, "timeframe": tf, "candle_time": stamp.isoformat(), **bar,
             "fetched_at": now} for stamp, bar in writes]
    if dr._source_column_available(client):
        for row in rows:
            row["source"] = SOURCE
    # Önce silme: upsert başarısız olsa bile yanlış satır kalmaz, kaydedici eksiği doldurur
    ids = [row["id"] for row in deletes]
    for i in range(0, len(ids), WRITE_CHUNK):
        client.table("candle_cache").delete().in_("id", ids[i:i + WRITE_CHUNK]).execute()
    for i in range(0, len(rows), WRITE_CHUNK):
        client.table("candle_cache").upsert(rows[i:i + WRITE_CHUNK],
                                            on_conflict="symbol,timeframe,candle_time").execute()


def process(client, fx: str, mt5_symbol: str, tf: str, until: datetime, apply: bool) -> dict:
    truth = load_truth(mt5_symbol, TIMEFRAMES[tf], until)
    if not truth:
        print(f"  {fx} {tf}: MT5 barı yok, atlandı")
        return {}
    depth_start = min(truth)
    existing = fetch_rows(client, "candle_cache", "id,symbol,timeframe,candle_time,open,high,low,close,volume,fetched_at",
                          fx, tf, WINDOW_START, until)
    updates, deletes, inserts = plan(existing, truth, depth_start)
    untouched_old = sum(parse_time(r["candle_time"]) < depth_start for r in existing)
    by_month = Counter(parse_time(r["candle_time"]).strftime("%m") for r in deletes)
    print(f"  {fx:12s} {tf:3s} mt5={len(truth):6d} tablo={len(existing):6d} güncelle={len(updates):6d} "
          f"sil={len(deletes):5d} ekle={len(inserts):5d} derinlik-öncesi={untouched_old:5d} "
          f"derinlik={depth_start:%Y-%m-%d} sil/ay={dict(sorted(by_month.items()))}", flush=True)
    if apply:
        apply_changes(client, fx, tf, updates, deletes, inserts)
    return {"updates": len(updates), "deletes": len(deletes), "inserts": len(inserts)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--tfs", default=",".join(TIMEFRAMES))
    ap.add_argument("--symbols", default=",".join(config.RECORDER_SYMBOLS))
    args = ap.parse_args()

    # Yalnız açık terminale bağlan: hesap değiştirme riski olan login yapılmaz
    ok = (mt5.initialize(config.MT5_TERMINAL_PATH) if config.MT5_TERMINAL_PATH else mt5.initialize())
    if not ok:
        print("mt5.initialize başarısız:", mt5.last_error())
        return 1
    try:
        offset = dr.detect_server_offset()
        now = datetime.now(timezone.utc)
        if offset is None or not rule_matches_measured(offset, now.timestamp()):
            print(f"offset {offset} dönem kuralına uymuyor, yazılmadı")
            return 2
        until = now - timedelta(minutes=FRESH_MARGIN_MIN)
        client = dr.supa()
        print(f"hesap={mt5.account_info().login} {'YAZMA' if args.apply else 'KURU KOŞU'} "
              f"{WINDOW_START:%Y-%m-%d} → {until:%Y-%m-%d %H:%M}", flush=True)
        symbols = args.symbols.split(",")
        for fx in symbols:
            truth = load_truth(config.RECORDER_SYMBOLS[fx], mt5.TIMEFRAME_M1, until)
            if not validate_against_snapshots(client, fx, truth, until):
                print(f"{fx}: kaynak doğrulaması geçmedi, hiçbir şey yazılmadı")
                return 3
        totals: Counter = Counter()
        for fx in symbols:
            for tf in args.tfs.split(","):
                totals.update(process(client, fx, config.RECORDER_SYMBOLS[fx], tf, until, args.apply))
        print("TOPLAM", dict(totals))
    finally:
        mt5.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
