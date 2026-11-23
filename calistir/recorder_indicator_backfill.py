"""recorder_indicator_backfill.py — kaydedicinin kaçırdığı indicator_snapshots satırlarını yeniden üret.

Kutuda çalışır (MT5 gerekir). Kaydedicinin KENDİ fonksiyonlarını kullanır: aynı hesap
doğrulaması, aynı sunucu-saati dönüşümü (_iso), aynı compute_all penceresi (HIST_BARS) ve
aynı parçalı upsert. candle_cache'e yazmaz (açılış derin backfill'i onu zaten doldurur).

NEDEN: 2026-11-19 05:05 → 11-23 23:00 UTC kaydedici yazmadı; yeniden başlayınca
candle_cache'i 20.000 barla doldurdu ama indicator_snapshots'a poll başına yalnız
RECORDER_MAX_IND_PER_POLL (120) satır yazdı.

Kullanım (repo kökünde):
  python calistir\\recorder_indicator_backfill.py --since 2026-11-19T05:00 --until 2026-11-23T23:05
  ... --dry-run      # yalnız sayar, yazmaz
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1] / "yeni deneme"
CHUNK_EPOCH_PAD = 400          # since'ten önce gösterge ısınması için ek bar


def _utc(s: str) -> float:
    dt = datetime.fromisoformat(s)
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()


def backfill_one(rec, client, fx: str, mt5_sym: str, tf_name: str, since: float, until: float,
                 dry: bool) -> int:
    tf = rec.TF_MAP[tf_name]
    secs = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}[tf_name]
    now = datetime.now(timezone.utc).timestamp()
    need = int((now - since) / secs) + rec.HIST_BARS + CHUNK_EPOCH_PAD
    rates = rec.mt5.copy_rates_from_pos(mt5_sym, tf, 1, min(need, 90000))
    if rates is None:
        print(f"{fx} {tf_name}: copy_rates boş ({rec.mt5.last_error()})"); return 0
    o = [float(r["open"]) for r in rates]; h = [float(r["high"]) for r in rates]
    lo = [float(r["low"]) for r in rates]; c = [float(r["close"]) for r in rates]
    v = [float(r["tick_volume"]) for r in rates]; t = [int(r["time"]) for r in rates]
    rows = []
    for i in range(len(t)):
        stamp = rec._iso(t[i])
        ts = datetime.fromisoformat(stamp).timestamp()
        if ts < since or ts >= until or i < 30:
            continue
        a = max(0, i + 1 - rec.HIST_BARS)           # kaydedicinin kararlı penceresi
        ind = rec.compute_all(o[a:i + 1], h[a:i + 1], lo[a:i + 1], c[a:i + 1], v[a:i + 1])
        rows.append({"symbol": fx, "timeframe": tf_name, "candle_time": stamp, "open": o[i],
                     "high": h[i], "low": lo[i], "close": c[i], "volume": v[i], "ind": ind})
    print(f"{fx} {tf_name}: {len(rows)} satır ({rows[0]['candle_time'][:16] if rows else '-'} → "
          f"{rows[-1]['candle_time'][:16] if rows else '-'})", flush=True)
    if rows and not dry:
        rec._upsert_indicators(client, fx, tf_name, rows)
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="UTC ISO, ör. 2026-11-19T05:00")
    ap.add_argument("--until", required=True, help="UTC ISO (hariç)")
    ap.add_argument("--timeframes", nargs="+", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    os.chdir(BOT_DIR)                     # config.py + kaydedici modülleri burada
    sys.path.insert(0, str(BOT_DIR))
    import data_recorder as rec           # noqa: E402  (log satırları data_recorder.log'a düşer)

    if not rec.connect_mt5():
        sys.exit("MT5 bağlantısı reddedildi/başarısız")
    off = rec.detect_server_offset()
    if off is None:
        sys.exit("sunucu saat offset'i ölçülemedi — yanlış damga yazmamak için çıkılıyor")
    rec._SERVER_OFFSET_SEC, rec._OFFSET_KNOWN = off, True
    print(f"offset {off / 60:+.0f} dk, dönem kuralı uyumlu={rec._history_rule_trusted()}")
    client = None if a.dry_run else rec.supa()
    since, until = _utc(a.since), _utc(a.until)
    total = 0
    try:
        for fx, m in rec.config.RECORDER_SYMBOLS.items():
            sym = rec.resolve(m)
            if not sym:
                continue
            for tf_name in (a.timeframes or rec.config.RECORDER_TIMEFRAMES):
                if tf_name in rec.TF_MAP:
                    total += backfill_one(rec, client, fx, sym, tf_name, since, until, a.dry_run)
    finally:
        rec.mt5.shutdown()
    print(f"TOPLAM {total} satır {'(dry-run, yazılmadı)' if a.dry_run else 'yazıldı'}")


if __name__ == "__main__":
    main()
