"""NDX MT5 işlem-yönetimi araştırması — VERİ SETİ KURULUMU.

İki kohortu tek şemaya indirger ve 1m barlarla eşler:
  A) 2026-06-25 → 07-09  : analiz_paketi deals CSV (NAS100) + paket 1m CSV'si.
     OUT comment'inde [tp X]/[sl X] → tetiklenen seviye BİREBİR bilinir.
  B) 2026-06-15 → 06-24  : bot_live_audit/positions.json + Supabase candle_cache
     1m (tick-kirlilik önlemi: yalnız :00 saniyeli bucket-hizalı barlar).

Bilinmeyen SL/TP tarafı, aynı kohort+yön içindeki tetiklenen mesafelerin
medyanıyla doldurulur (empirik; config varsayımı değil). Mesafesi medyandan
aşırı sapan (×2+) işlemler 'geometry_uncertain' işaretlenir.

Çıktı: trades.json (işlem listesi) + bars_1m.csv (birleşik 1m barlar).
Sızıntı yok: yalnız geçmiş veri; replay motoru bar-kapanışı kararlıdır.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / "backend" / ".env")
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
PKG = ROOT / "analiz_paketi_2026-07-09"
OUT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

POINT_VALUE = 1.0          # NAS100: 1 lot = $1/puan (deals'ten doğrulandı)


def parse_ts(text: str) -> datetime:
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.fromisoformat(t)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ─── Kohort A: deals CSV → pozisyonlar ───────────────────────────────────────

def build_cohort_a() -> list[dict]:
    rows = list(csv.DictReader(open(PKG / "trades" / "mt5_deals_son_14gun.csv")))
    nas = [r for r in rows if r["symbol"] == "NAS100"]
    by_pos: dict[str, dict] = defaultdict(dict)
    for r in nas:
        pid = r["position_id"]
        if r["entry"] == "IN":
            by_pos[pid]["in"] = r
        elif r["entry"] == "OUT":
            by_pos[pid]["out"] = r

    trades = []
    for pid, pair in by_pos.items():
        if "in" not in pair or "out" not in pair:
            continue
        i, o = pair["in"], pair["out"]
        direction = "BUY" if i["type"] == "BUY" else "SELL"
        entry_px = float(i["price"])
        exit_px = float(o["price"])
        comment = o["comment"].strip()
        if comment.startswith("[tp"):
            reason = "tp"
        elif comment.startswith("[sl"):
            reason = "sl"
        else:
            reason = "other"
        trades.append({
            "cohort": "A",
            "pid": pid,
            "direction": direction,
            "entry_time": i["time_utc"],
            "exit_time": o["time_utc"],
            "entry_px": entry_px,
            "exit_px": exit_px,
            "lot": float(i["volume"]),
            "pnl": float(o["profit"]),
            "close_reason": reason,
            "trig_level": exit_px if reason in ("tp", "sl") else None,
            "magic": i["magic"],
            "strategy_tag": i["comment"].strip(),
        })
    return trades


# ─── Kohort B: positions.json ────────────────────────────────────────────────

def build_cohort_b() -> list[dict]:
    data = json.load(open(ROOT / "bot_live_audit" / "positions.json"))
    trades = []
    for p in data:
        if p.get("symbol") != "NDX.INDX":
            continue
        reason = p.get("close_reason")
        if reason not in ("tp", "sl"):        # dir_flip vb. yönetim-dışı kapanış
            continue
        trades.append({
            "cohort": "B",
            "pid": p["pid"],
            "direction": p["direction"],
            "entry_time": p["entry_time"] + "+00:00",
            "exit_time": p["exit_time"] + "+00:00",
            "entry_px": float(p["entry_px"]),
            "exit_px": float(p["exit_px"]),
            "lot": float(p.get("lot") or 1.0),
            "pnl": float(p.get("pnl") or 0.0),
            "close_reason": reason,
            "trig_level": float(p["level"]) if p.get("level") else None,
            "magic": None,
            "strategy_tag": p.get("combo") or "",
        })
    return trades


# ─── Geometri: bilinmeyen tarafı empirik medyanla doldur ─────────────────────

def fill_geometry(trades: list[dict]) -> None:
    dists: dict[tuple, list[float]] = defaultdict(list)
    for t in trades:
        if t["trig_level"] is None:
            continue
        d = abs(t["trig_level"] - t["entry_px"])
        dists[(t["cohort"], t["direction"], t["close_reason"])].append(d)

    med: dict[tuple, float] = {k: statistics.median(v) for k, v in dists.items()
                               if len(v) >= 3}

    def lookup(cohort: str, direction: str, side: str) -> float | None:
        for key in ((cohort, direction, side),
                    (cohort, "BUY", side), (cohort, "SELL", side)):
            if key in med:
                return med[key]
        pooled = [d for (c, _dir, s), v in dists.items() if s == side for d in v]
        return statistics.median(pooled) if pooled else None

    for t in trades:
        e, sign = t["entry_px"], (1 if t["direction"] == "BUY" else -1)
        if t["trig_level"] is None or t["close_reason"] not in ("tp", "sl"):
            t["geometry_ok"] = False
            continue
        if t["close_reason"] == "tp":
            tp_d = abs(t["trig_level"] - e)
            sl_d = lookup(t["cohort"], t["direction"], "sl")
        else:
            sl_d = abs(t["trig_level"] - e)
            tp_d = lookup(t["cohort"], t["direction"], "tp")
        if not tp_d or not sl_d:
            t["geometry_ok"] = False
            continue
        t["tp_dist"], t["sl_dist"] = round(tp_d, 2), round(sl_d, 2)
        t["tp_px"] = round(e + sign * tp_d, 2)
        t["sl_px"] = round(e - sign * sl_d, 2)
        t["geometry_ok"] = True
        # tetiklenen mesafe kendi tarafının medyanından ×2+ sapıyorsa işaretle
        own = med.get((t["cohort"], t["direction"], t["close_reason"]))
        trig_d = abs(t["trig_level"] - e)
        t["geometry_uncertain"] = bool(own and (trig_d > 2 * own or trig_d < own / 2))


# ─── 1m barlar ───────────────────────────────────────────────────────────────

def load_bars_pkg() -> dict[int, dict]:
    bars = {}
    with open(PKG / "prices" / "NDX_INDX_1m_son_14gun.csv") as f:
        for r in csv.DictReader(f):
            ts = int(parse_ts(r["time_utc"]).timestamp())
            bars[ts] = {"ts": ts, "open": float(r["open"]), "high": float(r["high"]),
                        "low": float(r["low"]), "close": float(r["close"])}
    return bars


def load_bars_supabase(start: str, end: str) -> dict[int, dict]:
    """candle_cache 1m — bucket-hizalı (:00) barlar, sayfalı çekim."""
    from database.supabase_client import get_supabase_client
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase erişilemedi — kohort B barları çekilemez")
    bars: dict[int, dict] = {}
    cursor = start
    while True:
        res = (client.table("candle_cache").select("candle_time,open,high,low,close")
               .eq("symbol", "NDX.INDX").eq("timeframe", "1m")
               .gte("candle_time", cursor).lt("candle_time", end)
               .order("candle_time").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(f"candle_cache sorgu hatası: {res['error']}")
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            dt = parse_ts(r["candle_time"])
            if dt.second != 0:                 # tick-kirlilik önlemi
                continue
            ts = int(dt.timestamp())
            bars[ts] = {"ts": ts, "open": float(r["open"]), "high": float(r["high"]),
                        "low": float(r["low"]), "close": float(r["close"])}
        last = parse_ts(chunk[-1]["candle_time"])
        cursor = (last + timedelta(seconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    return bars


def main() -> None:
    trades = build_cohort_a() + build_cohort_b()
    fill_geometry(trades)
    usable = [t for t in trades if t.get("geometry_ok")]
    print(f"işlem: toplam={len(trades)} kullanılabilir={len(usable)} "
          f"(A={sum(1 for t in usable if t['cohort']=='A')}, "
          f"B={sum(1 for t in usable if t['cohort']=='B')})")

    bars = load_bars_pkg()
    sb = load_bars_supabase("2026-06-14T00:00:00+00:00", "2026-06-26T00:00:00+00:00")
    print(f"1m bar: paket={len(bars)} supabase={len(sb)}")
    for ts, b in sb.items():
        bars.setdefault(ts, b)

    json.dump(trades, open(OUT_DIR / "trades.json", "w"), indent=1)
    with open(OUT_DIR / "bars_1m.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close"])
        for ts in sorted(bars):
            b = bars[ts]
            w.writerow([ts, b["open"], b["high"], b["low"], b["close"]])
    print(f"yazıldı: trades.json ({len(trades)}), bars_1m.csv ({len(bars)})")


if __name__ == "__main__":
    main()
