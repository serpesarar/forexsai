"""Sıradaki adaylar denetimi (2026-07-23):
  A) premium_zone_buy vetosu HAKLI MI? — bloklanan NDX/USOIL BUY sinyalleri
     sabit bot geometrisiyle (NDX 80/110p, USOIL %1.04/%1.49) 1m replay edilir.
     Veto haklıysa bloklananların EV'si negatif çıkmalı.
  B) GDAXI CHREV'e rejim kapısı — son 30 günün pulse3 GDAXI BUY sinyallerinden
     bot mantığıyla (is_mean_reversion, 30m) CHREV girişleri yeniden kurulur,
     67/119 ile replay edilir; ADX(30m) ve kanal-eğimi kovalarında WR ayrışıyor mu?
Sızıntı yok: girişler sinyal anındaki fiyat, çözüm sonraki 1m barlarla, SL-önce.
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "yeni deneme"))
from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env"); load_dotenv(ROOT / ".env")
from database.supabase_client import get_supabase_client
from channel_filter import is_mean_reversion, channel_zscore

SINCE = "2026-06-20T00:00:00+00:00"
UNTIL = "2026-07-24T00:00:00+00:00"
EPISODE_GAP_MIN = 60          # aynı bloktaki ardışık vetolar tek "epizod"


def parse_ts(t: str) -> datetime:
    t = t.replace("Z", "+00:00")
    dt = datetime.fromisoformat(t)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch_table(client, table, select, filters, order="created_at"):
    out, cursor = [], SINCE
    while True:
        q = client.table(table).select(select)
        for f in filters:
            q = q.eq(*f)
        res = (q.gte("created_at", cursor).lt("created_at", UNTIL)
               .order("created_at").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        out.extend(chunk)
        cursor = (parse_ts(chunk[-1]["created_at"]) + timedelta(microseconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    return out


def fetch_bars(client, symbol, timeframe) -> list[dict]:
    cache = HERE / f"bars_{symbol.replace('.','_')}_{timeframe}.csv"
    if cache.exists():
        with open(cache) as f:
            return [{"ts": int(r["ts"]), "o": float(r["o"]), "h": float(r["h"]),
                     "l": float(r["l"]), "c": float(r["c"]), "v": float(r["v"])}
                    for r in csv.DictReader(f)]
    bars, cursor = [], SINCE
    while True:
        res = (client.table("candle_cache").select("candle_time,open,high,low,close,volume")
               .eq("symbol", symbol).eq("timeframe", timeframe)
               .gte("candle_time", cursor).lt("candle_time", UNTIL)
               .order("candle_time").limit(1000).execute())
        if res.get("error"):
            raise RuntimeError(res["error"])
        chunk = res.get("data") or []
        if not chunk:
            break
        for r in chunk:
            dt = parse_ts(r["candle_time"])
            if timeframe == "1m" and dt.second != 0:
                continue
            bars.append({"ts": int(dt.timestamp()), "o": float(r["open"]),
                         "h": float(r["high"]), "l": float(r["low"]),
                         "c": float(r["close"]), "v": float(r["volume"] or 0)})
        cursor = (parse_ts(chunk[-1]["candle_time"]) + timedelta(seconds=1)).isoformat()
        if len(chunk) < 1000:
            break
    seen, uniq = set(), []
    for b in bars:
        if b["ts"] not in seen:
            seen.add(b["ts"]); uniq.append(b)
    with open(cache, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ts", "o", "h", "l", "c", "v"])
        for b in uniq:
            w.writerow([b["ts"], b["o"], b["h"], b["l"], b["c"], b["v"]])
    return uniq


def replay(entry_ts: int, entry: float, direction: str, tp_d: float, sl_d: float,
           bars_1m: list[dict], keys: list[int], max_bars=4320):
    import bisect
    sign = 1 if direction == "BUY" else -1
    tp, sl = entry + sign * tp_d, entry - sign * sl_d
    i = bisect.bisect_right(keys, (entry_ts // 60) * 60)
    for k in keys[i:i + max_bars]:
        b = bars_1m[keys.index(k)] if False else None
    # hız: index eşlemeli erişim
    return None


def make_replayer(bars_1m):
    keys = [b["ts"] for b in bars_1m]
    bymap = {b["ts"]: b for b in bars_1m}
    import bisect

    def run(entry_ts, entry, direction, tp_d, sl_d, max_bars=4320):
        sign = 1 if direction == "BUY" else -1
        tp, sl = entry + sign * tp_d, entry - sign * sl_d
        i = bisect.bisect_right(keys, (entry_ts // 60) * 60)
        for k in keys[i:i + max_bars]:
            b = bymap[k]
            hit_sl = (b["l"] <= sl) if sign > 0 else (b["h"] >= sl)
            hit_tp = (b["h"] >= tp) if sign > 0 else (b["l"] <= tp)
            if hit_sl:                       # SL-önce konservatif
                return -1.0
            if hit_tp:
                return tp_d / sl_d
        return 0.0                           # çözülmedi
    return run


def episodes(rows, price_key="price_at_veto"):
    eps, last = [], None
    for r in sorted(rows, key=lambda x: x["created_at"]):
        ts = parse_ts(r["created_at"])
        px = r.get(price_key)
        if px is None:
            continue
        if last is None or (ts - last).total_seconds() > EPISODE_GAP_MIN * 60:
            eps.append({"ts": int(ts.timestamp()), "px": float(px)})
        last = ts
    return eps


def summarize(rs):
    n = len(rs)
    w = sum(1 for r in rs if r > 0)
    l = sum(1 for r in rs if r < 0)
    return (f"n={n} W={w} L={l} çözülmeyen={n-w-l} WR={100*w/max(1,w+l):.1f}% "
            f"totR={sum(rs):+.2f} avgR={statistics.mean(rs) if rs else 0:+.3f}")


def main():
    client = get_supabase_client()

    # ── A) premium_zone_buy denetimi ─────────────────────────────────────────
    print("═══ A) premium_zone_buy vetosu — bloklananların gerçek kaderi ═══")
    for symbol, tp_d_fn, sl_d_fn, be in [
        ("NDX.INDX", lambda p: 80.0, lambda p: 110.0, 57.9),
        ("USOIL.FOREX", lambda p: p * 0.0104, lambda p: p * 0.0149, 58.9),
    ]:
        rows = fetch_table(client, "signal_vetoes", "created_at,price_at_veto",
                           [("veto_reason", "premium_zone_buy"), ("symbol", symbol)])
        eps = episodes(rows)
        bars = fetch_bars(client, symbol, "1m")
        run = make_replayer(bars)
        rs = [run(e["ts"], e["px"], "BUY", tp_d_fn(e["px"]), sl_d_fn(e["px"]))
              for e in eps]
        rs_resolved = [r for r in rs if r != 0.0]
        print(f"  {symbol}: {len(rows)} veto → {len(eps)} epizod | "
              f"{summarize(rs)} | başabaş WR %{be}")
        if rs_resolved:
            wr = 100 * sum(1 for r in rs_resolved if r > 0) / len(rs_resolved)
            verdict = "VETO HAKLI (bloklananlar −EV)" if sum(rs_resolved) < 0 else \
                      "VETO PARA KAYBETTİRİYOR (bloklananlar +EV)"
            print(f"    → çözülenler: WR %{wr:.1f}, totR {sum(rs_resolved):+.2f} → {verdict}")

    # ── B) GDAXI CHREV rejim kapısı ──────────────────────────────────────────
    print("\n═══ B) GDAXI CHREV — rejim kovalarında WR ═══")
    sig = fetch_table(client, "prediction_logs", "created_at,entry_price",
                      [("model_type", "pulse3"), ("symbol", "GDAXI.INDX"),
                       ("ml_direction", "BUY")])
    eps = episodes(sig, price_key="entry_price")
    bars30 = fetch_bars(client, "GDAXI.INDX", "30m")
    bars1 = fetch_bars(client, "GDAXI.INDX", "1m")
    run = make_replayer(bars1)
    keys30 = [b["ts"] for b in bars30]
    import bisect
    results = []
    for e in eps:
        i = bisect.bisect_right(keys30, e["ts"])
        win = bars30[max(0, i - 60):i]
        if len(win) < 55:
            continue
        fbars = [{"high": b["h"], "low": b["l"], "close": b["c"], "volume": b["v"]}
                 for b in win]
        ok, source, z = is_mean_reversion(fbars, "BUY")
        if not ok:
            continue
        closes = [b["c"] for b in win]
        # rejim ölçüleri: kanal eğimi (ATR-normalize, 50 bar) + basit ADX yerine
        # 12 barlık (6 saat) yönlü hareket / ATR30
        a, _b = np.polyfit(np.arange(50), np.asarray(closes[-50:]), 1)
        trs = [max(win[j]["h"] - win[j]["l"], abs(win[j]["h"] - win[j - 1]["c"]),
                   abs(win[j]["l"] - win[j - 1]["c"])) for j in range(1, len(win))]
        atr30 = sum(trs[-14:]) / 14
        slope_norm = a / atr30 if atr30 > 0 else 0.0      # bar başına eğim / ATR
        mom12 = (closes[-1] - closes[-13]) / atr30 if atr30 > 0 else 0.0
        r = run(e["ts"], e["px"], "BUY", 67.0, 119.0)
        results.append({"z": z, "src": source, "slope": slope_norm,
                        "mom12": mom12, "r": r})
    resolved = [x for x in results if x["r"] != 0.0]
    print(f"  CHREV-benzeri giriş: {len(results)} (çözülen {len(resolved)})")
    print(f"  TÜMÜ: {summarize([x['r'] for x in results])} | başabaş WR %64.0")
    for name, cond in [
        ("eğim ≥ −0.05 (düşmeyen)", lambda x: x["slope"] >= -0.05),
        ("eğim < −0.05 (düşen kanal)", lambda x: x["slope"] < -0.05),
        ("mom12 ≥ −1.5 ATR", lambda x: x["mom12"] >= -1.5),
        ("mom12 < −1.5 ATR (sert düşüş)", lambda x: x["mom12"] < -1.5),
    ]:
        sub = [x["r"] for x in resolved if cond(x)]
        if sub:
            print(f"    {name:<32} {summarize(sub)}")


if __name__ == "__main__":
    main()
